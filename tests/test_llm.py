import pytest
from statschat.generative.llm import Inquirer


@pytest.fixture(scope="module")
def inquirer():
    return Inquirer(
        generative_model_name="google/flan-t5-small", faiss_db_root="tests/data/db_test"
    )


def test_llm_answer(inquirer):
    """Independently test it instantiates and runs QA"""
    docs = [
        {
            "page_content": "Today is Tuesday.",
            "source": "dummy1.json",
            "seq_num": 1,
            "score": 0.4644126296043396,
            "date": "",
            "title": "",
        },
        {
            "page_content": "My birthday is on Thursday.",
            "source": "dummy2.json",
            "seq_num": 1,
            "score": 0.6272023320198059,
            "date": "",
            "title": "",
        },
    ]

    response = inquirer.query_texts(query="What day is my birthday?", docs=docs)

    assert (response.answer_provided is False) or (
        "thursday" in response.most_likely_answer.lower()
    )


def test_llm_search(inquirer):
    """Just tests that this instantiates and runs."""

    result = inquirer.similarity_search(
        query="How many national parks are there in England?"
    )

    assert "National parks" in result[0]["page_content"]
