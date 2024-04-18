from pydantic import BaseModel, Field
from typing import Union, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import logging
from datetime import datetime
from markupsafe import escape

from statschat import load_config
from statschat.generative.llm import Inquirer
from statschat.embedding.latest_flag_helpers import get_latest_flag


# Config file to load
CONFIG = load_config(name="main")

# define session_id that will be used for log file and feedback
SESSION_NAME = f"statschat_api_{format(datetime.now(), '%Y_%m_%d_%H:%M')}"

logger = logging.getLogger(__name__)
log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_fmt,
    # filename=f"log/{SESSION_NAME}.log",
    filemode="a",
)

# initiate Statschat AI and start the app
inquirer = Inquirer(**CONFIG["db"], **CONFIG["search"], logger=logger)

app = FastAPI(
    title="ONS StatsChat API",
    description=(
        "Read more in [blog post]"
        + "(https://datasciencecampus.ons.gov.uk/using-large-language-models-llms-to-improve-website-search-experience-with-statschat/)"  # noqa: E501
        + " or see [the code repository]"
        + "(https://github.com/datasciencecampus/statschat-app). "
        + "Frontend UI available internally [here]"
        + "(http://localhost:5000)."
    ),
    summary="""Experimental search of Office for National Statistics web publications.
        Using retrieval augmented generation (RAG).""",
    version="0.0.2",
    contact={
        "name": "ONS Data Science Campus",
        "email": "dsc.projects@ons.gov.uk",
    },
)


@app.get("/", tags=["Principle Endpoints"])
async def about():
    """Access the API documentation in json format.

    Returns:
        Redirect to /openapi.json
    """
    response = RedirectResponse(url="/openapi.json")
    return response


@app.get("/search", tags=["Principle Endpoints"])
async def search(
    q: str,
    content_type: Union[str, None] = "latest",
    debug: bool = True,
):
    """Search ONS articles and bulletins for a question.

    Args:
        q (str): Question to be answered based on ONS articles and bulletins.
        content_type (Union[str, None], optional): Type of content to be searched.
            Currently accepted values: 'latest' to search the latest bulletins only
            or 'all' to search any articles and bulletins.
            Optional, defaults to 'latest'.
        debug (bool, optional): Flag to return debug information (full LLM response).
            Optional, defaults to True.

    Raises:
        HTTPException: 422 Validation error.

    Returns:
        HTTPresponse: 200 JSON with fields: question, content_type, answer, references
            and optionally debug_response.
    """
    question = escape(q).strip()
    if question in [None, "None", ""]:
        raise HTTPException(status_code=422, detail="Empty question")

    if content_type not in ["latest", "all"]:
        logger.warning('Unknown content type. Fallback to "latest".')
        content_type = "latest"
    latest_weight = get_latest_flag({"q": question}, CONFIG["app"]["latest_max"])

    docs, answer, response = inquirer.make_query(
        question,
        latest_filter=content_type == "latest",
        latest_weight=latest_weight,
    )
    results = {
        "question": question,
        "content_type": content_type,
        "answer": answer,
        "references": docs,
    }
    if debug:
        results["debug_response"] = response.__dict__
    logger.info(f"Sending following response: {results}")
    return results


class Feedback(BaseModel):
    rating: Union[str, int] = Field(
        description="""Recorded rating of the last answer.
        If thumbs are used then values are '1' for thumbs up
        and '0' for thumbs down."""
    )
    rating_comment: Optional[str] = Field(
        description="""Recorded comment on the last answer. Optional."""
    )
    question: Optional[str] = Field(description="""Last question. Optional.""")
    content_type: Optional[str] = Field(description="""Last content type. Optional.""")
    answer: Optional[str] = Field(description="""Last answer. Optional.""")


@app.post("/feedback", status_code=202, tags=["Principle Endpoints"])
async def record_rating(feedback: Feedback):
    """Records feedback on a previous answer.

    Args:
        feedback (Feedback): Recorded rating of the last answer.
            Required fields: rating (str or int).
            Optional fields: question, content_type, answer.

    Raises:
        HTTPException: 422 Validation error.

    Returns:
        HTTPResponse: 202 with empty body to indicate successfully added feedback.
    """
    logger.info(f"Recorded answer feedback: {feedback}")
    return ""
