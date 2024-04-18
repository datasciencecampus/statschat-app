from statschat.generative.response_model import LlmResponse


def deduplicator(records: list[dict], keys: list[str]) -> list[dict]:
    """
    Given a list of dicts, removes duplicates based on one or more listed keys.

    Args:
        records (list[dict]): list of dicts to deduplicate.
        keys (list[str]): list of keys by which to deduplicate.

    Returns:
        list[dict]: list of dicts that are unique w.r.t. keys.
    """
    signatures = []
    to_return = []
    for record in records:
        signature = "::".join([str(record[field]) for field in keys])
        if signature not in signatures:
            to_return.append(record)
    return to_return


def highlighter(
    top_matches: list[dict], validated_response: LlmResponse, logger
) -> list[dict]:
    """
    Takes highlighting phrases selected from the top 3 context. Matches and returns ALL
    matched contexts with phrases highlighted in bold where they exist.

    Args:
        top_matches (list[dict]): Documents closely related to query
        validated_answer: response form LLm containing phrases for highlighting

    Returns:
        list[dict]: Copy of 'top_matches' with highlighted phrases
    """
    phrases = sorted(
        list(
            set(
                (
                    [validated_response.most_likely_answer]
                    if validated_response.most_likely_answer
                    else []
                )
                + validated_response.highlighting1
                + validated_response.highlighting2
                + validated_response.highlighting3
            )
        ),
        key=lambda x: len(x),
    )
    logger.info(f"Highlighting contexts: {phrases}")
    if len(phrases) > 0:
        highlighted_contexts = []

        # iterate over each context
        for doc in top_matches:
            for phrase in phrases:
                found = doc["page_content"].lower().find(phrase.lower())
                # print(phrase, found, doc)
                if found != -1:
                    end_index = found + len(phrase)
                    highlighted = (
                        doc["page_content"][:found]
                        + "<b>"
                        + doc["page_content"][found:end_index]
                        + "</b>"
                        + doc["page_content"][end_index:]
                    )
                    doc["page_content"] = highlighted

            highlighted_contexts.append(doc)
    else:
        highlighted_contexts = top_matches

    return highlighted_contexts


def trim_context(context: str) -> str:
    """Remove unfinished words/sentence from the end of a string."""
    # if context[-1] != ".":
    #    fixed = ". ".join(re.split("\.\s+", context)[:-1]) + "."  # noqa: W605
    # else:
    # Remove the last word from the context, in case it's broken.
    fixed = " ".join(context.split(" ")[:-1])
    # Remove the first word from the context, in case it's broken.
    fixed = " ".join(fixed.split(" ")[1:])
    # If this crude cleaning stripped everything somehow; give up
    if len(fixed) == 0:
        return context
    return fixed
