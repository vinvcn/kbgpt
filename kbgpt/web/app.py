import logging
import sys
import tempfile
import uuid
from os.path import join

from aiofiles import open, tempfile
from sanic import Sanic
from sanic.exceptions import FileNotFound
from sanic.response import html, json, text
from sanic.server.protocols.websocket_protocol import WebSocketProtocol

from kbgpt.svc.file_services import add_file_to_customer_service
from kbgpt.svc.qa_services import QAagent

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s]  %(filename)s:%(lineno)d %(message)s",
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler(sys.stdout)],
)


app = Sanic("app")


@app.route("/process_file", methods=["POST"])
async def process_file(request):
    """
    POST endpoint to process file"""

    try:
        for file in request.files["file"]:
            async with tempfile.NamedTemporaryFile(
                delete=True, prefix=str(uuid.uuid4()), suffix=file.name
            ) as temp_file:
                async with open(temp_file.name, "wb") as f:
                    await f.write(file.body)
                    await add_file_to_customer_service(path=temp_file.name)
        return json({"success": True})
    except Exception as e:
        logging.error(str(e))
        return json({"success": False, "error": str(e)})


@app.websocket("/qa")
async def answer_question(request, ws):
    agent = QAagent()
    while True:
        # Wait for incoming message
        message = await ws.recv()
        # Process message as needed
        # processed_message = process_qa_message(message)
        # Send response back over websocket
        llm_result = await agent.answer_question(question=message)
        await ws.send(llm_result)


def run_debug():
    app.run(host="0.0.0.0", port=8000, debug=True, protocol=WebSocketProtocol)
