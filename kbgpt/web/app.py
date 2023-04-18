import logging
import sys
import tempfile
import time
import uuid
from os.path import join

from aiofiles import open, tempfile
from sanic import Sanic
from sanic.exceptions import FileNotFound
from sanic.response import html, json, text
from sanic.server.protocols.websocket_protocol import WebSocketProtocol

from config import *
from kbgpt.svc.file_services import add_file_to_customer_service
from kbgpt.svc.qa_services import QAagent

app = Sanic("app")


@app.route("/process_file", methods=["POST"])
async def process_file(request):
    """
    POST endpoint to process file"""

    try:
        flush = FLUSH_BEFORE_WRITE
        for file in request.files["file"]:
            async with tempfile.NamedTemporaryFile(
                delete=True, prefix=str(uuid.uuid4()), suffix=file.name
            ) as temp_file:
                async with open(temp_file.name, "wb") as f:
                    await f.write(file.body)
                    await add_file_to_customer_service(path=temp_file.name, flush_index=flush)
                    flush = False
        return json({"success": True})
    except Exception as e:
        logging.exception(e)
        return json({"success": False, "error": str(e)})


@app.route("/get_qa", methods=["GET"])
async def answer_question_get(request):
    """
    GET endpoint to answer a question"""
    start_counter = time.perf_counter()
    try:
        question = request.json["question"]
        agent = QAagent()
        llm_result = await agent.answer_question(question=question)
        return json({"success": True, "answer": llm_result})
    except Exception as e:
        logging.error(e.with_traceback())
        return json({"success": False, "error": str(e)})
    finally:
        logging.debug("End of answer_question_get request, total time %.3f" % (time.perf_counter() - start_counter))


@app.websocket("/qa")
async def answer_question(request, ws):
    """
    Websocket endpoint to answer a question"""
    agent = QAagent()
    while True:
        # Wait for incoming message
        message = await ws.recv()
        # Process message as needed
        # processed_message = process_qa_message(message)
        # Send response back over websocket
        llm_result = await agent.answer_question(question=message)
        await ws.send(llm_result)


def run():
    app.run(
        host=SANIC.get("IP", "0.0.0.0"),
        port=SANIC.get("PORT", 8080),
        debug=SANIC.get("DEBUG", False),
        protocol=WebSocketProtocol,
    )
