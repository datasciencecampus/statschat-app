from datetime import datetime
import pandas as pd


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


def prep_response(answer):
    """reformat answer to for flast front end"""

    # TODO: filter figures?

    response = {
        "title": answer.meta["title"],
        "url": answer.meta["url"],
        "date": datetime.strptime(answer.meta["release_date"], "%Y-%m-%d").__format__(
            "%d %B %Y"
        ),
        "score": f"{int(answer.score*100)}%",
        "context": "... " + trim_context(answer.context) + " ...",
        "source": answer.meta["id"],
        "section": answer.meta["section_header"],
        "section_url": answer.meta["section_url"],
        "figures": answer.meta["figures"],
    }
    return response


def deduplicate_answers(references):
    """Drop references that are duplicated.
    At this moment it checks exact match of the context"""
    if len(references) > 1:
        keep = pd.DataFrame.from_dict(references)[
            ["section_url", "context"]
        ].drop_duplicates()
        return [references[i] for i in keep.index]
    else:
        return references
