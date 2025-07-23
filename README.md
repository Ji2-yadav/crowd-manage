# Crowd Simulator with Agentic AI

A scalable agentic AI system for crowd management and safety using Google ADK with Gemini models.

## Architecture

- **Agent Framework**: Modular agent system with tool calling capabilities
- **AI Models**: Google Gemini Pro/Flash models via Google ADK
- **Communication**: Event-driven architecture with Redis pub/sub
- **APIs**: FastAPI for REST endpoints and WebSocket support
- **Tools**: Extensible tool system for agent capabilities

## Features

- Multiple specialized agents (Movement Prediction, Action, Lost & Found, etc.)
- Real-time crowd monitoring and analysis
- Stampede prediction and prevention
- Lost and found person tracking
- Natural language situational summaries
- Crowd simulator for testing and demonstration

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Google Cloud credentials
```

3. Run the simulator:
```bash
python main.py
```

4. Access the web interface:
```
http://localhost:8000
```

## Project Structure

```
src/
├── agents/          # Agent implementations
├── tools/           # Tool definitions for agents
├── models/          # Data models and schemas
├── core/            # Core framework components
├── simulator/       # Crowd simulation logic
├── api/             # FastAPI endpoints
└── utils/           # Utility functions
```

## License

MIT License
