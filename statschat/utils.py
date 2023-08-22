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
        if signature in signatures:
            continue
        to_return.append(record)
    return to_return


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
