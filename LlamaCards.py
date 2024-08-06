import json
from quart import Quart, request, jsonify, render_template, send_from_directory, websocket, Response
from quart_cors import cors
import subprocess
import httpx
import os

app = Quart(__name__)
app = cors(app, allow_origin="*")

# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable tracemalloc for debugging
import tracemalloc
tracemalloc.start()

# Global variable for Ollama endpoint
ollama_endpoint = 'http://elitekrew.ddns.net:5000'

# Function to make a request to Ollama without streaming
async def query_ollama(model, messages, context_size, endpoint):
    url = f"{endpoint}/api/chat"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model.strip(),  # Trim any extraneous spaces from model name
        "messages": messages,
        "stream": False,
        "context_size": context_size
    }

    async with httpx.AsyncClient(timeout=60.0) as client:  # Increase timeout to 60 seconds
        response = await client.post(url, json=data, headers=headers)
        if response.status_code != 200:
            app.logger.error(f"Failed to get a valid response from Ollama API: {response.status_code}")
            raise ValueError(f"Failed to get a valid response from Ollama API: {response.status_code}")

        return response.json()

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/webgpu')
async def webgpu():
    return await render_template('WebGPU.html')

@app.route('/SD')
async def sd():
    return await render_template('SD/index.html')

@app.route('/dist/<path:filename>')
async def serve_dist(filename):
    return await send_from_directory('templates/SD/dist', filename)

@app.route('/api/models', methods=['GET'])
async def get_models():
    try:
        # Run the 'ollama list' command to get the list of models
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(result.stderr)

        # Parse the result and extract model names
        lines = result.stdout.strip().split('\n')
        models = [line.split('\t')[0].strip() for line in lines if '\t' in line]  # Trim any extraneous spaces
        return jsonify(models)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['OPTIONS', 'POST'])
async def chat():
    if request.method == 'OPTIONS':
        return Response(status=204, headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        })
    
    try:
        data = await request.json
        model = data['model']
        messages = data['messages']
        context_size = data.get('context_size', 2048)
        endpoint = data.get('endpoint', ollama_endpoint)
        
        app.logger.debug(f"Received request for model: {model} with messages: {messages}, context size: {context_size}, and endpoint: {endpoint}")

        response_data = await query_ollama(model, messages, context_size, endpoint)
        return jsonify(response_data), 200
    
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/update-endpoint', methods=['POST'])
async def update_endpoint():
    global ollama_endpoint
    try:
        data = await request.json
        ollama_endpoint = data['endpoint']
        app.logger.debug(f"Updated Ollama endpoint to: {ollama_endpoint}")
        return jsonify({"message": "Endpoint updated successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error updating endpoint: {str(e)}")
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
        await target_client.send_json(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
