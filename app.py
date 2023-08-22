import toml
import logging

import pandas as pd

from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask.logging import default_handler
from markupsafe import escape
from werkzeug.datastructures import MultiDict

from statschat.search import BasicSearcher
from statschat.latest_flag_helpers import get_latest_flag


# define session_id that will be used for log file and feedback
session_name = f"haystack_app_{format(datetime.now(), '%Y_%m_%d_%H:%M')}"
logger = logging.getLogger(__name__)
log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_fmt,
    filename=f"log/{session_name}.log",
    filemode="a",
)
logger.addHandler(default_handler)


# define global variable to link last answer to ratings for feedback capture
last_answer = {}
feedback_file = f"data/feedback/{session_name}.csv"
pd.DataFrame(
    {"question": [], "answer": [], "confidence": [], "timing": [], "feedback": []}
).to_csv(feedback_file, index=False)


# initiate Statschat AI and start the app
config = toml.load("app_config.toml")
searcher = BasicSearcher(
    **config["engine"], **config["models"], **config["query"], logger=logger
)
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
    advanced, latest = get_latest_flag(request.args, config["query"]["use_latest"])
    logger.info(f"Search query: {question}")
    if question:
        now = datetime.now()
        # TODO: pass the advanced filters to the searcher
        results, _ = searcher.query(question, latest=latest)
        logger.info(f"Received answer: {results['answer']}")
        global last_answer
        last_answer = {
            "question": question,
            "answer": results["answer"],
            "confidence": results["confidence"],
            "timing": (datetime.now() - now).total_seconds(),
        }
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
    _, latest = get_latest_flag(request.args, config["query"]["use_latest"])
    logger.info(f"Search query: {question}")
    if question:
        results, _ = searcher.query(question, latest=latest)
        logger.info(f"Received answer: {results['answer']}")
        return jsonify(results), 200
    else:
        return jsonify({"error": "Empty question"}), 400


@app.route("/api/about", methods=["GET", "POST"])
def about():
    info = {"version": "ONS StatsChat API v0.1", "contact": "dsc.projects@ons.gov.uk"}
    return jsonify(info)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
