LlamaCards Web App
LlamaCards is a versatile web application that offers a dynamic node-based interface for real-time interaction with various language and vision models. The app allows users to create, connect, and manage cards representing different functionalities, making it a powerful tool for customizing and controlling interactions with models hosted within Ollama.

Features
Interactive Node-Based Interface:

Create, connect, and manage cards representing different functionalities.
Drag-and-drop interface for easy customization of card layouts.
Real-Time Processing:

Concurrent processing of connected output cards.
Sequential processing of input cards to ensure data integrity.
Handles real-time updates and interactions using WebSockets.
Customizable Models:

Switch between different language and vision models with ease.
Supports a variety of models hosted within Ollama.
Embedding and Retrieval-Augmented Generation (RAG):

Embed text into a database for later retrieval.
Use the RAG card to combine prompts with stored data for enhanced responses.
Vision Card:

Supports image input from files or webcam streams.
Processes images and provides descriptions or analyses in real-time.
Repeater Card:

Automate sending prompts at specified intervals.
Ideal for recurring tasks or monitoring applications.
Comprehensive Logging:

Detailed logging for debugging and monitoring the application’s performance.
Dynamic Connections:

Cards connected to multiple outputs process concurrently.
Cards with multiple input connections wait for all inputs to complete before processing.
User-Friendly Settings:

Customize default model, context size, and other settings directly from the web interface.
Save and load card layouts for easy reuse.
Technologies Used
Quart: A Python ASGI web framework based on Flask.
aiohttp: Asynchronous HTTP client/server framework.
WebSockets: For real-time, bidirectional communication between the server and clients.
JavaScript: For dynamic client-side interactions.
HTML/CSS: For structuring and styling the web interface.
HTTPX: Proxy server to handle CORS issues when adjusting endpoints.
Getting Started
Prerequisites
Python 3.8 or higher
pip (Python package installer)
Installation
Clone the Repository:

bash
Copy code
git clone https://github.com/l33tkr3w/llamacards.git
cd llamacards-webapp
Create a virtual environment (optional but recommended):

bash
Copy code
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Install Dependencies:

bash
Copy code
pip install -r requirements.txt
Running the Application
Start the Quart Server:

bash
Copy code
python LlamaCards.py
Access the Web App: Open your web browser and navigate to http://localhost:5000.

Usage
Use the web interface to create and connect cards.
Each card can interact with configured language and vision models, sending prompts and receiving real-time responses.
Monitor and log all interactions for analysis and debugging.
License
This project is licensed under the MIT License.

Contributing
Contributions are welcome! Please submit a Pull Request or open an Issue for any bugs or feature requests.

Contact
For any questions or inquiries, please contact blackhatworks@gmail.com.
