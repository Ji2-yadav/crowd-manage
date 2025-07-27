# Project Drishti - AI Event Safety System

Real-time crowd monitoring and safety management system for large events.

## Project Structure

```
project-drishti/
├── simulator/          # Venue simulation service
│   ├── backend/        # Flask API (port 3001)
│   └── frontend/       # Dashboard UI
├── agent/              # AI monitoring service  
│   ├── backend/        # Gemini agent API (port 5001)
│   └── frontend/       # Chat interface
└── docs/               # API documentation
```

## Quick Start

### 1. Simulator Service
```bash
cd simulator/backend
pip install -r requirements.txt
python server.py
# Open simulator/frontend/index.html in browser
```

### 2. Agent Service
```bash
cd agent/backend
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key"
python conversation_api.py
# Open agent/frontend/chat.html in browser
```

## Key Features

- **Real-time Monitoring** - Live venue state with 2-second updates
- **Event Simulation** - Trigger emergencies (Fire, Medical, Security, etc.)
- **AI Response** - Proactive agent with tool-based actions
- **Gradual Evacuation** - Realistic 10-second evacuation simulation
- **Auto-resolution** - Alerts resolve based on actions taken

## Services Communication

- Simulator exposes REST API on port 3001
- Agent connects to simulator API for state/actions
- Frontend dashboards poll their respective backends