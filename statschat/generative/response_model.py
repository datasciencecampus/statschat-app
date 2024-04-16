from pydantic import BaseModel, Field
from typing import List, Optional


class LlmResponse(BaseModel):
    answer_provided: bool = Field(
        description="""True if enough information is provided in the context to answer
        the question, False otherwise."""
    )
    most_likely_answer: Optional[str] = Field(
        description="""Answer to the question, quoting or only minimally rephrasing
        the provided text. Empty if answer_provided=False."""
    )
    highlighting1: List[str] = Field(
        description="""List of short exact subphrases from the first context document,
        that are most relevant to the question and should therefore be highlighted
        within the context."""
    )
    highlighting2: List[str] = Field(
        description="""List of short exact subphrases from the second context document,
        that are most relevant to the question and should therefore be highlighted
        within the context."""
    )
    highlighting3: List[str] = Field(
        description="""List of short exact subphrases from the third and any further
        context document, that are most relevant to the question and should therefore
        be highlighted within the context.
        Empty of the number of context documents is smaller."""
    )
    reasoning: Optional[str] = Field(
        description="""Step by step reasoning why an answer has been selected or could
        not be provided. Reasoning how highlighted keywords relate to the question."""
    )
