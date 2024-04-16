# %%
import logging
from datetime import datetime
from flask import Flask, render_template, request, session
from flask.logging import default_handler
from markupsafe import escape
import requests

# %%

# statschat-api endpoint
endpoint = "http://localhost:8000/"  # TODO: add to some params/secrets file

# define session_id that will be used for log file and feedback
SESSION_NAME = f"statschat_app_{format(datetime.now(), '%Y_%m_%d_%H:%M')}"

logger = logging.getLogger(__name__)
log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_fmt,
    # filename=f"log/{SESSION_NAME}.log",
    filemode="a",
)
logger.addHandler(default_handler)

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"


@app.route("/")
def home():
    if "latest_filter" in request.args:
        session["latest_filter"] = request.args.get("latest_filter")
    else:
        session["latest_filter"] = "on"
    return render_template(
        "statschat.html", latest_filter=session["latest_filter"], question=""
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    session["question"] = escape(request.args.get("q")).strip()
    if "latest_filter" in request.args:
        session["latest_filter"] = request.args.get("latest_filter")
    else:
        session["latest_filter"] = "on"
    if session["latest_filter"] in ["on", "On", "True", "true", True, "latest"]:
        session["content_type"] = "latest"
    else:
        session["content_type"] = "all"

    if session["question"]:
        try:
            response = requests.get(
                url=endpoint + "search",
                params={
                    "q": session["question"],
                    "content_type": session["content_type"],
                },
            )
            if response.ok:
                print(response.json())
                session["answer"] = response.json()["answer"]
                docs = response.json()["references"]
                logger.info(
                    f"""QAPAIR: {
                    {"question": session["question"],
            "content_type": session["content_type"],
            "response": response.json()}}"""
                )
            else:
                session["answer"] = f"Connection to API failed: {response.status_code}"
                docs = []
                logger.warning(
                    f"""API-FAIL: {
                    {"question": session["question"],
            "content_type": session["content_type"],
            "response": response.status_code}}"""
                )
        except requests.exceptions.RequestException as e:
            session["answer"] = f"Connection to API failed: {e}"
            docs = []
            logger.warning(
                f"""API-FAIL: {
                {"question": session["question"],
                 "content_type": session["content_type"],
                 "response": e}}"""
            )
        results = {"answer": session["answer"], "references": docs}

    else:
        results = {}

    return render_template(
        "statschat.html",
        latest_filter=session["latest_filter"],
        question=session["question"],
        results=results,
    )


@app.route("/record_rating", methods=["POST"])
def record_rating():
    rating = request.form["rating"]
    last_answer = {
        "rating": rating,
        "rating_comment": request.form["comment"],
        "question": session["question"],
        "content_type": session["content_type"],
        "answer": session["answer"],
    }
    requests.post(endpoint + "feedback", json=last_answer)
    logger.info(f"FEEDBACK: {last_answer}")
    return "", 204  # Return empty response with status code 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
