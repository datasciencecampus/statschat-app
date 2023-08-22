import toml
import logging

import pandas as pd

from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask.logging import default_handler
from markupsafe import escape
from werkzeug.datastructures import MultiDict

from statschat.llm import Inquirer
from statschat.utils import deduplicator
from statschat.latest_flag_helpers import get_latest_flag, time_decay


# Config file to load
CONFIG = toml.load("app_config.toml")

# define session_id that will be used for log file and feedback
SESSION_NAME = f"statschat_app_{format(datetime.now(), '%Y_%m_%d_%H:%M')}"

logger = logging.getLogger(__name__)
log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_fmt,
    filename=f"log/{SESSION_NAME}.log",
    filemode="a",
)
logger.addHandler(default_handler)


# define global variable to link last answer to ratings for feedback capture
last_answer = {}
feedback_file = f"data/feedback/{SESSION_NAME}.csv"
pd.DataFrame(
    {"question": [], "answer": [], "confidence": [], "timing": [], "feedback": []}
).to_csv(feedback_file, index=False)

# initiate Statschat AI and start the app
searcher = Inquirer(**CONFIG["db"], **CONFIG["search"], logger=logger)


def make_query(question: str, latest_max: bool = True) -> dict:
    """
    Utility, wraps code for querying the search engine, and then the summarizer.
    Also handles storing the last answer made for feedback purposes.

    Args:
        question (str): The user query.
        latest (bool, optional): Whether to weight in favour of recent releases.
            Defaults to True.

    Returns:
        dict: answer and supporting documents returned.
    """
    now = datetime.now()
    # TODO: pass the advanced filters to the searcher
    # TODO: move deduplication keys to config['app']
    docs = deduplicator(
        searcher.similarity_search(question),
        keys=["section", "title", "date"],
    )
    if len(docs) > 0:
        if latest_max:
            for doc in docs:
                # Divided by decay term because similarity scores are inverted
                # Original score is L2 distance; lower is better
                #  https://python.langchain.com/docs/integrations/vectorstores/faiss
                doc["weighted_score"] = doc["score"] / time_decay(
                    doc["date"], latest=latest_max
                )
            docs.sort(key=lambda doc: doc["weighted_score"])
            logger.info(
                f"Weighted and reordered docs to latest with decay = {latest_max}"
            )

        answer = searcher.query_texts(question, docs)
    else:
        answer = "NA"

    results = {
        "answer": answer,
        "question": question,
        "references": docs,
        "timing": (datetime.now() - now).total_seconds(),
    }
    logger.info(f"Received answer: {results['answer']}")

    # Handles storing last answer for feedback purposes
    global last_answer
    last_answer = results.copy()

    return results


app = Flask(__name__)


@app.route("/")
def home():
    advanced = MultiDict()
    return render_template("statschat.html", advanced=advanced, question="?")


@app.route("/advanced")
def advanced():
    advanced = MultiDict(
        [("latest-publication", "Off"), ("bulletins", "on"), ("articles", "on")]
    )
    return render_template("statschat.html", advanced=advanced, question="?")


@app.route("/search", methods=["GET", "POST"])
def search():
    question = escape(request.args.get("q"))
    advanced, latest_max = get_latest_flag(request.args, CONFIG["app"]["latest_max"])
    logger.info(f"Search query: {question}")
    if question:
        results = make_query(question, latest_max)
        return render_template(
            "statschat.html", advanced=advanced, question=question, results=results
        )
    else:
        return render_template("statschat.html", advanced=advanced, question="?")


@app.route("/record_rating", methods=["POST"])
def record_rating():
    rating = request.form["rating"]
    logger.info(f"Recorded answer rating: {rating}")
    last_answer["rating"] = rating
    pd.DataFrame([last_answer]).to_csv(
        feedback_file, mode="a", index=False, header=False
    )
    return "", 204  # Return empty response with status code 204


@app.route("/api/search", methods=["GET", "POST"])
def api_search():
    question = escape(request.args.get("q"))
    _, latest_max = get_latest_flag(request.args, CONFIG["app"]["latest_max"])
    logger.info(f"Search query: {question}")
    if question:
        results = make_query(question, latest_max)
        logger.info(f"Received {len(results['references'])} documents.")
        return jsonify(results), 200
    else:
        return jsonify({"error": "Empty question"}), 400


@app.route("/api/about", methods=["GET", "POST"])
def about():
    info = {"version": "ONS StatsChat API v0.1", "contact": "dsc.projects@ons.gov.uk"}
    return jsonify(info)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
