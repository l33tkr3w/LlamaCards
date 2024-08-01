import json
from quart import Quart, request, jsonify, render_template, websocket, Response
from quart_cors import cors
import aiohttp
import asyncio

app = Quart(__name__)
app = cors(app, allow_origin="*")

# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable tracemalloc for debugging
import tracemalloc
tracemalloc.start()

# Function to make a request to Ollama with streaming enabled
async def query_ollama(model, messages):
    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": messages,
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status != 200:
                app.logger.error(f"Failed to get a valid response from Ollama API: {response.status}")
                raise ValueError(f"Failed to get a valid response from Ollama API: {response.status}")
            
            async for line in response.content:
                yield line.decode('utf-8')

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/api/chat', methods=['POST'])
async def chat():
    try:
        data = await request.json
        model = data['model']
        messages = data['messages']
        
        app.logger.debug(f"Received request for model: {model} with messages: {messages}")

        async def response_generator():
            try:
                async for chunk in query_ollama(model, messages):
                    yield chunk.encode('utf-8')  # Ensure bytes are yielded
            except Exception as e:
                app.logger.error(f"Error during response generation: {str(e)}")
                yield json.dumps({"error": str(e)}).encode('utf-8')

        return Response(response_generator(), content_type='application/json')
    
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

# WebSocket connection to handle real-time updates
connected_clients = set()

@app.websocket('/ws')
async def ws():
    connected_clients.add(websocket._get_current_object())
    try:
        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(data)
    finally:
        connected_clients.remove(websocket._get_current_object())

async def handle_websocket_message(data):
    if data['type'] == 'update_connection':
        await broadcast_connection_update(data)
    elif data['type'] == 'send_response':
        await forward_response(data)

async def broadcast_connection_update(data):
    for client in connected_clients:
        await client.send_json(data)

async def forward_response(data):
    target_client = next((client for client in connected_clients if client.id == data['target']), None)
    if target_client:
        await client.send_json(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
