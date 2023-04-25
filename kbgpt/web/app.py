"""
define the Sanic app
"""
import logging
import time
import uuid
from json import dumps

from aiofiles import open as aopen
from aiofiles import tempfile
from sanic import Sanic
from sanic.response import json
from sanic.server.protocols.websocket_protocol import WebSocketProtocol

from config import profile
from kbgpt.svc.file_services import add_file_to_customer_service
from kbgpt.svc.qa_services import ConvAgent, QAagent
from kbgpt.web.callbacks import StreamingTextCallbackHandler

app = Sanic(profile.sanic.app_name)


@app.route("/process_file", methods=["POST"])
async def process_file(request):
    """
    POST endpoint to process file"""
    # pylint: disable=broad-except
    try:
        flush = profile.indexing.flush_before_write
        for file in request.files["file"]:
            if len(file.body) <= 0:
                raise ValueError(f"File {file.name} can not be empty")
            async with tempfile.NamedTemporaryFile(
                delete=True, prefix=str(uuid.uuid4()), suffix=file.name
            ) as temp_file:
                async with aopen(temp_file.name, "wb") as f:
                    await f.write(file.body)
                    await f.flush()
                    await add_file_to_customer_service(
                        path=temp_file.name, flush_index=flush
                    )
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
    # pylint: disable=broad-except
    try:
        question = request.json["question"]
        logging.info("handling request: %s", dumps(request.json, indent=4))
        agent = QAagent.get_instance()
        llm_result, stats = await agent.answer_question(question=question)
        return json({"success": True, "answer": llm_result})
    except Exception as e:
        logging.exception(e)
        return json({"success": False, "error": str(e)})
    finally:
        logging.debug(
            "End of answer_question_get request, total time %.3f",
            (time.perf_counter() - start_counter),
        )


# pylint: disable=unused-argument
@app.websocket("/qa")
async def answer_question(request, ws):
    """
    Websocket endpoint to answer a question
    """
    agent = ConvAgent(
        streaming=True, handlers=[StreamingTextCallbackHandler(ws)]
    )
    while True:
        # Wait for incoming message
        message = await ws.recv()
        # Process message as needed
        # processed_message = process_qa_message(message)
        # Send response back over websocket
        answer = await agent.question(message)

        await ws.send(answer)
        # llm_result = await agent.answer_question(question=message)
        # await ws.send(llm_result)


def run():
    """
    run the web app
    """
    app.run(
        host=profile.sanic.ip,
        port=profile.sanic.port,
        debug=profile.sanic.debug,
        workers=profile.sanic.workers,
        protocol=WebSocketProtocol,
    )
