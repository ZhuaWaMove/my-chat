# Claude Agent

A simple web-based agent using Claude API with session persistence and local deployment.

## Features

- **Chat Interface**: Clean web interface for interacting with Claude
- **Session Persistence**: All conversations are saved locally in SQLite database
- **Session Management**: Create, view, and delete chat sessions
- **Local Deployment**: Runs entirely on your local machine
- **Simple Setup**: Easy configuration with environment variables

## Requirements

- Python 3.8+
- Claude API key from [Anthropic Console](https://console.anthropic.com/)

## Installation

1. Clone this repository or download the source code.

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the environment file and set your API key:
```bash
cp .env.example .env
```

5. Edit `.env` file and add your Claude API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Running the Application

### Quick Start (Windows)
Double-click `start.bat` or run:
```cmd
start.bat
```

### Quick Start (Linux/Mac)
```bash
chmod +x start.sh
./start.sh
```

### Manual Start
Start the application:
```bash
python run.py
```

Or use uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to `http://localhost:8000`

## Usage

### Web Interface
- **New Chat**: Click "New Chat" button to start a new conversation
- **Send Message**: Type your message and press Enter or click the send button
- **View History**: Select any conversation from the sidebar to view its history
- **Delete Sessions**: Currently, sessions can be deleted via API (UI deletion coming soon)

### API Endpoints
- `POST /api/chat/` - Send a message and get response
- `GET /api/sessions/` - List all chat sessions
- `GET /api/sessions/{session_id}` - Get a specific session with messages
- `POST /api/sessions/` - Create a new session
- `DELETE /api/sessions/{session_id}` - Delete a session

## Project Structure

```
claude-agent/
├── app/
│   ├── api/              # API routes
│   │   ├── chat.py
│   │   └── sessions.py
│   ├── core/             # Core configuration
│   │   └── config.py
│   ├── db/               # Database setup
│   │   └── session.py
│   ├── models/           # SQLAlchemy models
│   │   └── chat.py
│   ├── schemas/          # Pydantic schemas
│   │   └── chat.py
│   ├── services/         # Business logic
│   │   ├── chat.py
│   │   └── claude.py
│   ├── static/           # Static files (CSS, JS)
│   ├── templates/        # HTML templates
│   │   └── index.html
│   └── main.py           # FastAPI application
├── .env.example          # Example environment variables
├── requirements.txt      # Python dependencies
├── run.py               # Application entry point
└── README.md            # This file
```

## Configuration

### Environment Variables
- `ANTHROPIC_API_KEY` (required): Your Claude API key
- `ANTHROPIC_MODEL` (optional): Claude model to use (default: claude-3-5-sonnet-20241022)
- `DATABASE_URL` (optional): Database connection string (default: SQLite)
- `SESSION_EXPIRY_HOURS` (optional): Session expiry time in hours (default: 24)

### Model Selection
You can change the Claude model by setting the `ANTHROPIC_MODEL` environment variable. Supported models include:
- `claude-3-5-sonnet-20241022` (default)
- `claude-3-opus-20240229`
- `claude-3-haiku-20240307`
- Other available Claude models

## Database

The application uses SQLite by default, which creates a `claude_agent.db` file in the project directory. All chat sessions and messages are stored here.

To use a different database, modify the `DATABASE_URL` environment variable.

## Development

### Running Tests
*(Test suite to be implemented)*

### Code Style
This project uses standard Python conventions. Consider using:
- Black for code formatting
- isort for import sorting
- mypy for type checking

### Adding Features
1. New API endpoints: Add to `app/api/`
2. New database models: Add to `app/models/`
3. Business logic: Add to `app/services/`
4. Frontend changes: Modify `app/templates/index.html` and `app/static/`

## License

This project is for educational and personal use. Please comply with Anthropic's API terms of service.

## Acknowledgements

- [Anthropic](https://www.anthropic.com/) for the Claude API
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for ORM
