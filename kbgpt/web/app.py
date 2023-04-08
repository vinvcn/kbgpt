from __future__ import print_function

import logging
import sys
import tempfile
import uuid
from os.path import join

from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

from kbgpt.svc.file_services import add_file_to_customer_service
from kbgpt.svc.qa_services import answer_question_as_a_customer_service_agent

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s]  %(filename)s:%(lineno)d %(message)s",
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler(sys.stdout)],
)


def create_app():
    session_id = str(uuid.uuid4().hex)
    app = Flask(__name__)
    app.session_id = session_id
    # log session id
    logging.info(f"session_id: {session_id}")
    app.config["file_text_dict"] = {}
    CORS(app, supports_credentials=True)
    return app

app = create_app()


@app.route(f"/process_file", methods=["POST"])
@cross_origin(supports_credentials=True)
def process_file():
    """
    curl -X POST -F "file=@/Users/abhishek/Downloads/abc.txt" \ 
    http://localhost:8080/process_file
    """
    try:
        with tempfile.TemporaryDirectory() as tmpDir:
            file = request.files["file"]
            tmp_file_path = join(tmpDir, file.filename)
            file.save(tmp_file_path)
            logging.info(str(file))
            add_file_to_customer_service(
                path=tmp_file_path
            )
        return jsonify({"success": True})
    except Exception as e:
        logging.error(str(e))
        return jsonify({"success": False, "error": str(e)})


@app.route(f"/answer_question", methods=["POST"])
@cross_origin(supports_credentials=True)
def answer_question():
    """
    curl -X POST -H "Content-Type: application/json" \ 
    -d '{"question": "what is the capital of france"}' \ 
    http://localhost:8080/answer_question
    """
    try:
        params: dict = request.get_json()
        question = params["question"]
        llm_result = answer_question_as_a_customer_service_agent(
            question=question
        )
        return llm_result
    except Exception as e:
        return str(e)



@app.route("/healthcheck", methods=["GET"])
@cross_origin(supports_credentials=True)
def healthcheck():
    """
    curl http://localhost:8080/healthcheck
    """
    return "OK"

def run_debug():
    app.run(debug=True, port=8080, threaded=True)
    