# LlamaCards Web App

LlamaCards is a web application that provides a dynamic interface for interacting with Large Language Models (LLMs) in real-time. This app allows users to create and connect cards, each representing different functionalities such as sending prompts and receiving responses from various language models.

## Features

- **Interactive Cards**: Create and manage cards that interact with different language models.
- **Real-time Communication**: Utilizes WebSocket connections to handle real-time updates and interactions.
- **Customizable Models**: Easily switch between different language models for varied responses.
- **Detailed Logging**: Comprehensive logging to debug and monitor the application's performance.

## Technologies Used

- **Quart**: A Python ASGI web framework based on Flask.
- **aiohttp**: Asynchronous HTTP client/server framework.
- **WebSockets**: For real-time, bidirectional communication between the server and clients.
- **JavaScript**: For dynamic client-side interactions.
- **HTML/CSS**: For structuring and styling the web interface.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the Repository**:
    bash
    git clone https://github.com/l33tkr3w/llamacards.git
    cd llamacards-webapp
    

2. **Create a virtual environment** (optional but recommended):
    bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    

3. **Install Dependencies**:
    bash
    pip install -r requirements.txt
    

### Running the Application

1. **Start the Quart Server**:
    bash
    python LlamaCards.py
    

2. **Access the Web App**:
    Open your web browser and navigate to `http://localhost:5000`.

### Usage

- Create and connect cards in the web interface.
- Each card can send prompts and receive responses from the configured language model.
- Monitor real-time interactions and responses.


## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue for any bugs or feature requests.

## Contact

For any questions or inquiries, please contact [blackhatworks@gmail.com](mailto:blackhatworks@gmail.com).

