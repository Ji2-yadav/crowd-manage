# Agent Service

AI-powered safety monitoring agent with chat interface.

## Structure
- `backend/` - Gemini-powered conversation agent and API
- `frontend/` - Chat interface for interaction

## Running the Agent

### Backend
```bash
cd backend
pip install -r requirements.txt

# Set up environment variable
export GEMINI_API_KEY="your-api-key"

# Run the API server
python conversation_api.py
```
Server runs on http://localhost:5001

### Frontend
Open `frontend/chat.html` in a web browser

## Features
- Proactive safety monitoring
- Tool-based actions (dispatch, evacuate, etc.)
- Real-time system status display
- Function call visualization