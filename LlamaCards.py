import json
from datetime import datetime
from quart import Quart, request, jsonify, render_template, send_from_directory, Response, websocket
from quart_cors import cors
import subprocess
import httpx
import logging
import chromadb

app = Quart(__name__)
app = cors(app, allow_origin="*")

logging.basicConfig(level=logging.DEBUG)

ollama_endpoint = 'http://192.168.0.27:11434'
embedding_model = "mxbai-embed-large"  # Embedding model used

# Initialize ChromaDB client with the default settings for persistent storage
client = chromadb.Client()  # This will use the default configuration for persistence

# Initialize a dictionary to hold collections by their names
collections = {}

async def query_ollama(model, messages, context_size, endpoint):
    url = f"{endpoint}/api/chat"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model.strip(),
        "messages": messages,
        "stream": False,
        "context_size": context_size
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=data, headers=headers)
        if response.status_code != 200:
            app.logger.error(f"Failed to get a valid response from Ollama API: {response.status_code}")
            raise ValueError(f"Failed to get a valid response from Ollama API: {response.status_code}")

        return response.json()

async def get_text_embedding(text):
    url = f"{ollama_endpoint}/api/embeddings"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": embedding_model,
        "prompt": text
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=data, headers=headers)
        app.logger.debug(f"Raw API Response: {response.text}")
        if response.status_code != 200:
            app.logger.error(f"Failed to get embedding from Ollama API: {response.status_code}")
            raise ValueError(f"Failed to get embedding from Ollama API: {response.status_code}")

        if "application/json" in response.headers.get("Content-Type", ""):
            try:
                embedding_response = response.json()
                return embedding_response.get('embedding', [])
            except json.JSONDecodeError as e:
                app.logger.error(f"JSON decode error: {str(e)}")
                raise ValueError(f"Failed to parse embedding response: {str(e)}")
        else:
            app.logger.error("Non-JSON response received.")
            raise ValueError("Received non-JSON response from API.")

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
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(result.stderr)
        lines = result.stdout.strip().split('\n')
        models = [line.split('\t')[0].strip() for line in lines if '\t' in line]
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

@app.route('/api/embed', methods=['POST'])
async def embed_text():
    try:
        data = await request.json
        text = data['text']
        table_name = data['table_name']

        # Get embedding from the embedding model
        embedding = await get_text_embedding(text)

        if not embedding:
            raise ValueError("Failed to generate embedding.")

        # Prefix the timestamp to the text
        timestamp = datetime.now().isoformat()  # Get the current timestamp
        text_with_timestamp = f"{timestamp}: {text}"

        # Get or create the collection with the specified table name
        if table_name not in collections:
            collections[table_name] = client.get_or_create_collection(name=table_name)
        collection = collections[table_name]

        # Check if a document with the same ID already exists
        existing_documents = collection.get()["documents"]
        doc_id = str(len(existing_documents))  # Default to a new ID

        for idx, existing_document in enumerate(existing_documents):
            if existing_document.strip().startswith(text.strip()):  # Assuming a simple match
                # If a document with the same text already exists, append the new content
                existing_document += f"\n{text_with_timestamp}"
                collection.update(ids=[str(idx)], documents=[existing_document], embeddings=[embedding])
                return jsonify({"message": "Content appended to existing document", "timestamp": timestamp}), 200

        # If no match is found, add a new document
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text_with_timestamp],
            metadatas=[{"timestamp": timestamp}]
        )

        return jsonify({"message": "Embedding inserted successfully", "timestamp": timestamp}), 200
    except KeyError as e:
        app.logger.error(f"Missing key in request data: {str(e)}")
        return jsonify({"error": f"Missing key: {str(e)}"}), 400
    except ValueError as e:
        app.logger.error(f"Error processing embedding: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tables', methods=['GET'])
async def get_tables():
    try:
        # Return the list of table names (collection names)
        table_names = list(collections.keys())
        return jsonify(table_names)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
async def generate_rag():
    try:
        data = await request.json
        prompt = data['prompt']
        table_name = data['table_name']

        if table_name not in collections:
            app.logger.error(f"Table {table_name} does not exist.")
            return jsonify({"error": f"Table {table_name} does not exist."}), 404

        collection = collections[table_name]

        # Step 1: Get the embedding for the prompt
        prompt_embedding = await get_text_embedding(prompt)

        # Step 2: Query ChromaDB for the most relevant document in the selected collection
        results = collection.query(
            query_embeddings=[prompt_embedding],
            n_results=1
        )

        if not results['documents']:
            app.logger.error("No relevant documents found.")
            return jsonify({"error": "No relevant documents found."}), 404

        # Retrieve the most relevant document
        relevant_data = results['documents'][0][0]

        # Step 3: Use Ollama to generate a response
        combined_prompt = f"Using this data: {relevant_data} {prompt}"
        response_data = await query_ollama("gemma2:2b", [{"role": "user", "content": combined_prompt}], 8096, ollama_endpoint)

        if response_data.get("message", {}).get("content"):
            return jsonify({"response": response_data["message"]["content"]}), 200
        else:
            app.logger.error("LLM response did not contain content.")
            return jsonify({"error": "LLM response did not contain content."}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in generate_rag: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

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
