import json
import numpy as np
from time import time
from datetime import datetime
from pandas import DataFrame, Series
from rapidfuzz import fuzz
from typing import Optional

from statschat import load_config
from statschat.generative.llm import Inquirer


def get_test_responses(questions: list, make_query) -> list:
    """retrieve the first query responses for all questions
    Parameters
    ---------
    questions:list
        a list of questions to query
    searcher
        a searcher class object
    k_docs: int
        number of documents for the retriver to return for the reader
    k_answer: int
        number of answers the reader provides the summarizer
    Returns
    -------
    list
        list of dictionaries containing responses from each test
    """
    test_responses = []
    for q in questions:
        start_time = time()
        docs, _, response = make_query(q)
        run_time_seconds = round(time() - start_time, 2)
        test_responses.append(
            _get_response_components(docs, response.__dict__, run_time_seconds)
        )

    return test_responses


def _get_response_components(
    docs: list, response: dict, run_time_seconds: float
) -> dict:
    """extract important response components for testing
    Parameters
    ----------
    response: dict
        complete dictonary of response objects
    Returns
    -------
    dict
        selected response components (answer, confidence,
        section_url, answer_provided)
    """
    response_components = {
        "answer_provided": response["answer_provided"],
        "answer": response["most_likely_answer"],
        "section_url": docs[0]["section_url"] if docs else "",
        "all_urls": [x["section_url"] for x in docs],
        "page_content": docs[0]["page_content"] if docs else "",
        "seconds_to_run": run_time_seconds,
    }
    return response_components


def test_answer_provided(
    meta_test_responses: DataFrame, question_config: dict
) -> DataFrame:
    """
    Parameters
    ----------
    meta_test_responses: DataFrame
        a dataframe of test responses with searcher information
    question_config: dict
        the question configuration dictionary
    Returns
    -------
    DataFrame
        a dataframe with columns confirming whether the questions that
        were supposed to be answered met that criteria
    """
    question_info = _add_question_info(meta_test_responses, question_config)
    question_info["test_answer_provided"] = _test_series_value_match(
        question_info["should_answer"], question_info["answer_provided"]
    )
    question_info["fuzzy_partial_ratio"] = _partial_ratio_rowwise(
        question_info, "expected_answer", "answer"
    )
    return question_info


def _add_question_info(dataframe: DataFrame, question_config: dict) -> DataFrame:
    """add question info from config to dataframe
    Parameters
    ----------
    dataframe: DataFrame
        a dataframe which you want to append questions to
    question_config: dict
        the question configuration dictionary
    Returns
    -------
    DataFrame
        a dataframe with the question info appended
    """
    dataframe["questions"] = question_config.keys()
    question_fields = [
        "should_answer",
        "should_provide_relevant",
        "expected_keywords",
        "expected_answer",
        "expected_url",
    ]
    for field in question_fields:
        dataframe[field] = _get_nested_dict_element(field, question_config)
    return dataframe


def _get_nested_dict_element(dict_key: str, dictionary: dict) -> list:
    """get value from nested dictionary using 2nd order key
    Parameters
    ----------
    dict_key: str
        key for nested dictionary
    dictionary: dict
        dictionary containing another dictionary
    Returns
    -------
        value of the nested dictionary which corosponds to the given key
    """
    nested_dict_element = [
        value[dict_key] for value in dictionary.values() if dict_key in value
    ]
    return nested_dict_element


def _test_series_value_match(reference: Series, comparison: Series) -> Series:
    """rowwise comparison of two series to check if they have the same values
    in a given row
    Parameters
    ----------
    reference: Series
        the reference series for comparison
    comparison: Series
        the comparison series for comparison
    Returns
    -------
    Series
        a series of 'pass' or 'fail' strings
    """
    new_series = Series(np.where(reference == comparison, True, False))
    return new_series


def _partial_ratio_rowwise(
    dataframe: DataFrame, column_1: str, column_2: str
) -> Series:
    """map the partial token set ratio function across two columns of a dataframe
    Parameters
    ----------
    dataframe: Dataframe
        dataframe with two columns you want to compare
    column_1: string
        name of the first column
    column_2: string
        name of the second column
    Returns
    -------
    Series
        series of partial ratio scores
    """
    ratio = Series(map(fuzz.partial_ratio, dataframe[column_1], dataframe[column_2]))
    return ratio


def score_retrieval(text: str, tokens: list[str]) -> float:
    """
    Crude measure of retrieval accuracy, are the expected keywords present?
    Normalises to fraction of keywords present, for comparisons between docs.

    Parameters
    ----------
    text: str
        The piece of text to be scored
    tokens: list[str]
        A list of expected (lowercase) tokens/words

    Returns
    -------
    float
        score, between 1 (perfect recall) and 0
    """
    text_clean = text.lower()
    return sum([token in text_clean for token in tokens]) / len(tokens)


def check_url(expected: str, actual: str) -> bool:
    """Check if the expected url present in that returned."""
    return str(expected) in str(actual)


def mmr_url(expected_url: str, returned_urls: list[str]) -> float:
    """
    Score rank of expected result within retrieved docs.  Score is 1 / rank
    of the expected document.  We use the URL's of documents as unique
    identifiers here.  Score is 0.0 if not found.

    Parameters
    ----------
    expected_url: str
        The anticipated URL of the top retrieved document, what we want to see
    returned_urls: list[str]
        The URL's of the documents actually returned by the search

    Returns
    -------
    float
        A score between 0 (not found) and 1 (top-ranked)
    """
    # Handles case, no returns expected
    if not expected_url:
        if len(returned_urls) > 0:
            return 0.0
        return 1.0

    # Returns 1/rank if expected url is present in results
    for i, url in enumerate(returned_urls):
        if expected_url in url:
            return 1.0 / (i + 1.0)

    # Returns zero if no match in search results
    return 0.0


def test_search_result(df):
    """Handles tests relating to accuracy of doc retrieval system."""
    df["retrieval_keyword_score"] = df.apply(
        lambda row: score_retrieval(row["page_content"], row["expected_keywords"]),
        axis=1,
    )
    df["correct_doc"] = df.apply(
        lambda row: check_url(row["expected_url"], row["section_url"]), axis=1
    )
    df["retrieval_rank"] = df.apply(
        lambda row: mmr_url(row["expected_url"], row["all_urls"]), axis=1
    )
    return df


def pipeline(
    app_config_file: Optional[str] = None,
    question_config_file: Optional[str] = None,
    n_questions: int = None,
):
    """main pipeline function for the evaluator"""
    question_config = load_config(question_config_file, name="questions")

    # Optionally only run N questions (useful for quick test/eval)
    if n_questions:
        question_config = {
            key: value for key, value in list(question_config.items())[:n_questions]
        }

    # Create app components
    app_config = load_config(app_config_file, name="main")
    searcher = Inquirer(**app_config["db"], **app_config["search"])

    test_responses = get_test_responses(
        question_config.keys(), make_query=searcher.make_query
    )
    test_response_df = DataFrame(test_responses)
    print(test_response_df.head())
    question_info = test_answer_provided(test_response_df, question_config)
    question_info = test_search_result(question_info)
    question_info["app_config"] = str(app_config)

    metrics = {
        "retrieval_keyword": question_info["retrieval_keyword_score"].mean(),
        "retrieval_rank": question_info["retrieval_rank"].mean(),
        "retrieval_correct": question_info["correct_doc"].mean(),
        "answer_fuzz": question_info["fuzzy_partial_ratio"].mean(),
        "answer_present": question_info["test_answer_provided"].mean(),
    }

    col_order = [
        "questions",
        "should_answer",
        "answer_provided",
        "test_answer_provided",
        "expected_answer",
        "answer",
        "fuzzy_partial_ratio",
        "expected_url",
        "retrieval_keyword_score",
        "correct_doc",
        "retrieval_rank",
        "should_provide_relevant",
        "section_url",
        "all_urls",
        "page_content",
        "expected_keywords",
        "seconds_to_run",
        "app_config",
    ]
    stamp = datetime.now()

    # Save the detailed responses
    question_info[col_order].to_csv(
        f"data/test_outcomes/{format(stamp, '%Y-%m-%d_%H:%M')}_questions.csv",
        index=False,
    )

    # Save the model config that yielded the responses
    app_config["prompt"] = searcher.extractive_prompt.to_json()
    with open(
        f"data/test_outcomes/{format(stamp, '%Y-%m-%d_%H:%M')}_config.json", "w"
    ) as f:
        json.dump(app_config, f, indent=4)

    # Save the average (mean) performance metrics
    with open(
        f"data/test_outcomes/{format(stamp, '%Y-%m-%d_%H:%M')}_metrics.json", "w"
    ) as f:
        json.dump(metrics, f, indent=4)

    return metrics


if __name__ == "__main__":
    pipeline()


# TODO consider alternative tests for answer correctness
# TODO conduct relevance scoring on more than the first returned article
# TODO add a field to capture other relevant parameters
# TODO create a new script for joining multiple test output csvs
