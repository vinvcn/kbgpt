from sanic import Sanic
from sanic.response import html, json, text
from sanic.server.protocols.websocket_protocol import WebSocketProtocol

app = Sanic("draft_ws_async")


# POST endpoint to process file
@app.route("/process_file", methods=["POST"])
async def process_file(request):
    # Get file from request body
    file_body = request.body
    # Process the file as needed
    # processed_data = process_file_function(file_body)
    # Return processed data as JSON
    return json({"data": "processed_data"})


# WebSocket endpoint for QA
@app.websocket("/qa")
async def qa(request, ws):
    lst = []
    while True:
        # Wait for incoming message
        message = await ws.recv()
        lst.append(message)
        # Process message as needed
        # processed_message = process_qa_message(message)
        # Send response back over websocket
        await ws.send("\n".join(lst))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, protocol=WebSocketProtocol)
