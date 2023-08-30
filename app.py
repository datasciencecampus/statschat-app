import toml
import logging

from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask.logging import default_handler
from markupsafe import escape
from werkzeug.datastructures import MultiDict
from flask_socketio import SocketIO

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


# initiate Statschat AI and start the app
searcher = Inquirer(**CONFIG["db"], **CONFIG["search"], logger=logger)


def make_query(question: str, latest: int = 1) -> list:
    """
    Utility, wraps code for querying the search engine, and then the summarizer.
    Also handles storing the last answer made for feedback purposes.

    Args:
        question (str): The user query.
        latest (bool, optional): Whether to weight in favour of recent releases.
            Defaults to True.

    Returns:
        list: supporting documents returned.
    """
    # TODO: pass the advanced filters to the searcher
    # TODO: move deduplication keys to config['app']
    docs = deduplicator(
        searcher.similarity_search(question),
        keys=["section", "title", "date"],
    )
    if len(docs) > 0:
        if latest:
            for doc in docs:
                # Divided by decay term because similarity scores are inverted
                # Original score is L2 distance; lower is better
                #  https://python.langchain.com/docs/integrations/vectorstores/faiss
                doc["score"] = doc["score"] / time_decay(doc["date"], latest=latest)
            docs.sort(key=lambda doc: doc["score"])
            logger.info(f"Weighted and reordered docs to latest with decay = {latest}")
        for doc in docs:
            doc["score"] = round(doc["score"], 2)

    return docs


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)


@app.route("/")
def home():
    advanced = MultiDict()
    return render_template("statschat.html", advanced=advanced, question="?")
    # TODO: redesign the statschat template to put results in sockets


@app.route("/advanced")
def advanced():
    advanced = MultiDict(
        [("latest-publication", "Off"), ("bulletins", "on"), ("articles", "on")]
    )
    return render_template("statschat.html", advanced=advanced, question="?")


@app.route("/search", methods=["GET", "POST"])
def search():
    session["question"] = escape(request.args.get("q"))
    advanced, latest = get_latest_flag(request.args, CONFIG["app"]["latest_max"])
    if session["question"]:
        logger.info(f"Search query: {session['question']}")
        docs = make_query(session["question"], latest)
        logger.info(
            f"Received {len(docs)} references"
            + f" with top distance {docs[0]['score'] if docs else 'Inf'}"
        )
        session["docs"] = docs[: CONFIG["search"]["k_contexts"]]
        return render_template(
            "statschat.html",
            advanced=advanced,
            question=session["question"],
            results={"answer": "Loading...", "references": docs},
        )
    else:
        return render_template("statschat.html", advanced=advanced, question="?")


def search_question_async(sid, question, docs):
    """
    Generate answer and emit to a socketio instance (broadcast)
    Ideally to be run in a separate thread?
    """
    # TODO: pass the advanced filters to the searcher
    socketio.emit(
        "newanswer",
        {"answer": "Looking for answer in relevant documents..."},
        namespace="/answer",
        to=sid,
    )
    answer = searcher.query_texts(question, docs)
    logger.info(f"Received answer: {answer}")
    if answer in ["NA", "NA.", ""]:
        answer_str = ""
    else:
        answer_str = (
            'Most likely answer: <h4 class="ons-u-fs-xxl"> <div id="answer">'
            + answer
            + "</div> </h4>"
        )
    socketio.emit("newanswer", {"answer": answer_str}, namespace="/answer", to=sid)


@socketio.on("connect", namespace="/answer")
def test_connect():
    # need visibility of the global thread object
    print("Client connected")
    sid = request.sid
    socketio.start_background_task(
        search_question_async,
        sid=sid,
        question=session.get("question"),
        docs=session.get("docs"),
    )


@socketio.on("disconnect", namespace="/answer")
def test_disconnect():
    print("Client disconnected")


@app.route("/record_rating", methods=["POST"])
def record_rating():
    rating = request.form["rating"]
    logger.info(f"Recorded answer rating: {rating}")
    last_answer = {
        "rating": rating,
        "question": session["question"],
        "answer": searcher.query_texts(
            session["question"], session["docs"]
        ),  # session['answer'],  # TODO: store answer in session?
        "references": session["docs"],
        "config": CONFIG,
    }
    logger.info(f"Received feedback: {last_answer}")
    # pd.DataFrame([last_answer]).to_csv(
    #    feedback_file, mode="a", index=False, header=False
    # )
    return "", 204  # Return empty response with status code 204


@app.route("/api/search", methods=["GET", "POST"])
def api_search():
    question = escape(request.args.get("q"))
    logger.info(f"API Search query: {question}")
    if question:
        _, latest = get_latest_flag(request.args, CONFIG["app"]["latest_max"])
        docs = make_query(question, latest)
        answer = searcher.query_texts(question, docs)
        results = {"question": question, "answer": answer, "references": docs}
        logger.info(f"Received {len(results['references'])} documents.")
        return jsonify(results), 200
    else:
        return jsonify({"error": "Empty question"}), 400


@app.route("/api/about", methods=["GET", "POST"])
def about():
    info = {"version": "ONS StatsChat API v0.1", "contact": "dsc.projects@ons.gov.uk"}
    return jsonify(info)


if __name__ == "__main__":
    socketio.run(app, debug=False, host="0.0.0.0")
