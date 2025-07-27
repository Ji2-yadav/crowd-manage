# Simulator Service

Event venue simulation with real-time monitoring dashboard.

## Structure
- `backend/` - Flask API server simulating venue state
- `frontend/` - Dashboard UI for visualization and control

## Running the Simulator

### Backend
```bash
cd backend
pip install -r requirements.txt
python server.py
```
Server runs on http://localhost:3001

### Frontend
Open `frontend/index.html` in a web browser

## Features
- Real-time zone monitoring
- Event triggering (Fire, Medical Emergency, etc.)
- Personnel and gate management
- Gradual evacuation simulation