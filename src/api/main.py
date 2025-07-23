from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any
import asyncio
import json
import numpy as np
from datetime import datetime

from ..core.agent_framework import GeminiAgentFramework
from ..agents.specialized_agents import (
    MovementPredictionAgent, ActionAgent, LostAndFoundAgent, SummarizationAgent, VisualizationAgent
)
from ..tools.base_tools import CrowdAnalysisTool, NotificationTool, ActionRecommendationTool, CameraSearchTool
from ..tools.visualization_tools import CrowdVisualizationTool, AlertVisualizationTool, MapVisualizationTool
from ..simulator.crowd_simulator import CrowdSimulator
from ..models.schemas import AgentRole

app = FastAPI(title="Crowd Management Agentic AI", version="1.0.0")

# Global instances
framework = GeminiAgentFramework()
simulator = CrowdSimulator()
websocket_connections: List[WebSocket] = []

# Initialize the system
@app.on_event("startup")
async def startup_event():
    """Initialize agents and tools on startup"""
    
    # Register tools
    framework.register_tool(CrowdAnalysisTool())
    framework.register_tool(NotificationTool())
    framework.register_tool(ActionRecommendationTool())
    framework.register_tool(CameraSearchTool())
    framework.register_tool(CrowdVisualizationTool())
    framework.register_tool(AlertVisualizationTool())
    framework.register_tool(MapVisualizationTool())
    
    # Register agents
    framework.register_agent(MovementPredictionAgent())
    framework.register_agent(ActionAgent())
    framework.register_agent(LostAndFoundAgent())
    framework.register_agent(SummarizationAgent())
    framework.register_agent(VisualizationAgent())
    
    # Start simulation
    asyncio.create_task(simulator.start_simulation())
    print("🚀 Crowd Management System initialized successfully!")


def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


@app.get("/api/locations/status")
async def get_locations_status():
    """Get status of all locations"""
    return await simulator.get_all_locations_status()


@app.get("/api/locations/{location_id}")
async def get_location_details(location_id: str):
    """Get detailed information about a specific location"""
    return await simulator.get_location_data(location_id)


@app.post("/api/agents/movement_prediction/analyze")
async def analyze_movement(request: Dict[str, Any]):
    """Trigger movement analysis agent"""
    location_id = request.get("location_id", "central_plaza")
    agent = framework.agents.get("movement_prediction_agent")
    if not agent:
        raise HTTPException(status_code=404, detail="Movement prediction agent not found")
    
    result = await agent.analyze_location(location_id)
    return result


@app.post("/api/agents/action/generate")
async def generate_actions(request: Dict[str, Any]):
    """Trigger action generation agent"""
    agent = framework.agents.get("action_agent")
    if not agent:
        raise HTTPException(status_code=404, detail="Action agent not found")
    
    result = await agent.generate_action_plan(
        request.get("location_id"),
        request.get("situation"),
        request.get("severity")
    )
    return result


@app.post("/api/agents/lost_and_found/search")
async def search_person(request: Dict[str, Any]):
    """Trigger lost and found search agent"""
    agent = framework.agents.get("lost_and_found_agent")
    if not agent:
        raise HTTPException(status_code=404, detail="Lost and found agent not found")
    
    result = await agent.search_person(
        request.get("person_description"),
        request.get("last_seen_location")
    )
    return result


@app.post("/api/agents/summarization/summary")
async def get_zone_summary(request: Dict[str, Any]):
    """Get zone summary from summarization agent"""
    agent = framework.agents.get("summarization_agent")
    if not agent:
        raise HTTPException(status_code=404, detail="Summarization agent not found")
    
    result = await agent.generate_zone_summary(
        request.get("zone_name"),
        request.get("query")
    )
    return result


@app.post("/api/simulation/incident")
async def simulate_incident(request: Dict[str, Any]):
    """Simulate an incident in the crowd simulator"""
    result = await simulator.simulate_incident(
        request.get("location_id"),
        request.get("incident_type")
    )
    return result


@app.post("/api/simulation/action")
async def apply_action(request: Dict[str, Any]):
    """Apply a crowd management action in the simulator"""
    result = await simulator.apply_action(
        request.get("location_id"),
        request.get("action_type"),
        request.get("parameters", {})
    )
    return result


@app.get("/api/visualization/{viz_type}")
async def get_visualization_data(viz_type: str, location_ids: str = None):
    """Get visualization data of specified type"""
    location_list = location_ids.split(',') if location_ids else None
    result = None
    
    try:
        if viz_type == "density_heatmap":
            tool = framework.tools_registry.get("generate_crowd_visualization")
            if tool:
                result = await tool.execute("density_heatmap", location_list)
        elif viz_type == "flow_chart":
            tool = framework.tools_registry.get("generate_crowd_visualization")
            if tool:
                result = await tool.execute("flow_chart", location_list, 60)
        elif viz_type == "capacity_chart":
            tool = framework.tools_registry.get("generate_crowd_visualization")
            if tool:
                result = await tool.execute("capacity_chart", location_list)
        elif viz_type == "trend_analysis":
            tool = framework.tools_registry.get("generate_crowd_visualization")
            if tool:
                result = await tool.execute("trend_analysis", location_list, 60)
        elif viz_type == "alert_dashboard":
            tool = framework.tools_registry.get("generate_alert_visualization")
            if tool:
                result = await tool.execute("all", 24)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"Visualization type {viz_type} not found")
        
        # Convert numpy types to native Python types
        result = convert_numpy_types(result)
        return result
        
    except Exception as e:
        # If there's still an error, return a safe fallback
        if viz_type == "alert_dashboard":
            return {
                "summary": {
                    "total_alerts": 0,
                    "resolution_rate": 0,
                    "avg_response_time": 0,
                    "severity_distribution": {
                        "low": 0,
                        "medium": 0,
                        "high": 0,
                        "critical": 0
                    }
                },
                "data": [],
                "error": f"Failed to generate visualization: {str(e)}"
            }
        else:
            return {
                "data": [],
                "error": f"Failed to generate visualization: {str(e)}"
            }


@app.post("/api/agents/visualization/generate")
async def generate_visualization(request: Dict[str, Any]):
    """Trigger visualization generation agent"""
    agent = framework.agents.get("visualization_agent")
    if not agent:
        raise HTTPException(status_code=404, detail="Visualization agent not found")
    
    viz_type = request.get("visualization_type", "density_heatmap")
    location_ids = request.get("location_ids")
    
    try:
        result = await agent.generate_crowd_visualization(viz_type, location_ids)
        # Convert numpy types to native Python types
        result = convert_numpy_types(result)
        return result
    except Exception as e:
        return {
            "agent_response": f"Error generating visualization: {str(e)}",
            "tool_results": []
        }


@app.get("/api/visualization/crowd_map")
async def get_crowd_map(map_type: str = "density", zoom_level: int = 16):
    """Generate crowd map visualization data"""
    try:
        tool = framework.tools_registry.get("generate_crowd_map")
        if tool:
            result = await tool.execute(map_type, zoom_level)
            # Ensure data structure is complete
            if result and "data" in result:
                # Validate required fields exist
                map_data = result["data"]
                if "markers" not in map_data:
                    map_data["markers"] = []
                if "zones" not in map_data:
                    map_data["zones"] = []
                if "flow_lines" not in map_data:
                    map_data["flow_lines"] = []
                if "heatmap_points" not in map_data:
                    map_data["heatmap_points"] = []
                    
                result = convert_numpy_types(result)
                return result
            else:
                # Return fallback structure
                return {
                    "type": "crowd_map",
                    "map_type": map_type,
                    "data": {
                        "center": {"lat": 40.7589, "lng": -73.9851},
                        "zoom": zoom_level,
                        "markers": [],
                        "zones": [],
                        "flow_lines": [],
                        "heatmap_points": []
                    },
                    "total_crowd": 0,
                    "avg_density": 0,
                    "timestamp": datetime.now().isoformat(),
                    "error": "No map data available"
                }
        else:
            raise HTTPException(status_code=404, detail="Map visualization tool not found")
    except Exception as e:
        # Return safe fallback data structure
        return {
            "type": "crowd_map",
            "map_type": map_type,
            "data": {
                "center": {"lat": 40.7589, "lng": -73.9851},
                "zoom": zoom_level,
                "markers": [],
                "zones": [],
                "flow_lines": [],
                "heatmap_points": []
            },
            "total_crowd": 0,
            "avg_density": 0,
            "timestamp": datetime.now().isoformat(),
            "error": f"Failed to generate map: {str(e)}"
        }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive and send periodic updates
            status = await simulator.get_all_locations_status()
            await websocket.send_json({
                "type": "status_update",
                "data": status,
                "timestamp": datetime.now().isoformat()
            })
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)


@app.get("/")
async def get_dashboard():
    """Serve the main dashboard"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crowd Management Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1400px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
            .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .chart-container { height: 300px; position: relative; }
            .heatmap { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 20px; }
            .heatmap-cell { padding: 15px; border-radius: 8px; color: white; font-weight: bold; text-align: center; }
            .heatmap-cell.green { background: #27ae60; }
            .heatmap-cell.yellow { background: #f39c12; }
            .heatmap-cell.orange { background: #e67e22; }
            .heatmap-cell.red { background: #e74c3c; }
            .btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #2980b9; }
            .btn.danger { background: #e74c3c; }
            .btn.danger:hover { background: #c0392b; }
            .btn.viz { background: #9b59b6; }
            .btn.viz:hover { background: #8e44ad; }
            .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .status.low { background: #d4edda; color: #155724; }
            .status.medium { background: #fff3cd; color: #856404; }
            .status.high { background: #f8d7da; color: #721c24; }
            .status.critical { background: #f5c6cb; color: #721c24; font-weight: bold; }
            #log { height: 200px; overflow-y: scroll; background: #1e1e1e; color: #00ff00; padding: 10px; font-family: monospace; }
            .tabs { display: flex; background: #ecf0f1; border-radius: 8px; margin-bottom: 20px; }
            .tab { flex: 1; padding: 10px; text-align: center; cursor: pointer; border-radius: 8px; }
            .tab.active { background: #3498db; color: white; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏟️ Crowd Management AI Dashboard</h1>
                <p>Real-time crowd monitoring and AI-powered management system with advanced visualizations</p>
            </div>
            
            <div class="tabs">
                <div class="tab active" onclick="switchTab('overview')">📊 Overview</div>
                <div class="tab" onclick="switchTab('charts')">📈 Analytics</div>
                <div class="tab" onclick="switchTab('heatmap')">🗺️ Heatmap</div>
                <div class="tab" onclick="switchTab('map')">🌍 Live Map</div>
                <div class="tab" onclick="switchTab('alerts')">🚨 Alerts</div>
            </div>
            
            <div id="overview" class="tab-content active">
                <div class="grid">
                    <div class="card">
                        <h3>📊 Location Status</h3>
                        <div id="locations"></div>
                        <button class="btn" onclick="refreshStatus()">Refresh Status</button>
                    </div>
                    
                    <div class="card">
                        <h3>🤖 Agent Commands</h3>
                        <button class="btn" onclick="analyzeMovement()">Analyze Movement</button>
                        <button class="btn" onclick="generateActions()">Generate Actions</button>
                        <button class="btn" onclick="searchPerson()">Search Person</button>
                        <button class="btn" onclick="getZoneSummary()">Zone Summary</button>
                        <hr>
                        <h4>📊 Visualization</h4>
                        <button class="btn viz" onclick="generateVisualization('density_heatmap')">Density Heatmap</button>
                        <button class="btn viz" onclick="generateVisualization('capacity_chart')">Capacity Chart</button>
                        <hr>
                        <h4>🚨 Simulate Incidents</h4>
                        <button class="btn danger" onclick="simulateIncident('stampede_risk')">Stampede Risk</button>
                        <button class="btn danger" onclick="simulateIncident('blocked_exit')">Blocked Exit</button>
                    </div>
                </div>
            </div>
            
            <div id="charts" class="tab-content">
                <div class="grid">
                    <div class="card">
                        <h3>📈 Crowd Flow Trends</h3>
                        <div class="chart-container">
                            <canvas id="flowChart"></canvas>
                        </div>
                        <button class="btn" onclick="updateFlowChart()">Update Flow Chart</button>
                    </div>
                    
                    <div class="card">
                        <h3>📊 Capacity Utilization</h3>
                        <div class="chart-container">
                            <canvas id="capacityChart"></canvas>
                        </div>
                        <button class="btn" onclick="updateCapacityChart()">Update Capacity</button>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📉 Density Trends & Predictions</h3>
                    <div class="chart-container">
                        <canvas id="trendChart"></canvas>
                    </div>
                    <button class="btn" onclick="updateTrendChart()">Update Trends</button>
                </div>
            </div>
            
            <div id="heatmap" class="tab-content">
                <div class="card">
                    <h3>🗺️ Crowd Density Heatmap</h3>
                    <div id="heatmapContainer" class="heatmap"></div>
                    <button class="btn" onclick="updateHeatmap()">Update Heatmap</button>
                </div>
            </div>
            
            <div id="map" class="tab-content">
                <div class="grid">
                    <div class="card">
                        <h3>🌍 Real-Time Crowd Map</h3>
                        <div style="margin-bottom: 10px;">
                            <button class="btn" onclick="updateMapType('density')">Density View</button>
                            <button class="btn" onclick="updateMapType('flow')">Flow View</button>
                            <button class="btn" onclick="updateMapType('zones')">Zone View</button>
                        </div>
                        <div id="mapContainer" style="height: 500px; border: 1px solid #ddd; border-radius: 8px; position: relative;">
                            <div id="loadingMap" style="display: flex; align-items: center; justify-content: center; height: 100%; color: #666;">
                                🗺️ Loading interactive map...
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>📊 Map Legend</h3>
                        <div id="mapLegend">
                            <div style="margin: 10px 0;">
                                <strong>Density Levels:</strong><br>
                                <span style="color: #27ae60;">● Low (0-30%)</span><br>
                                <span style="color: #f39c12;">● Medium (30-60%)</span><br>
                                <span style="color: #e67e22;">● High (60-80%)</span><br>
                                <span style="color: #e74c3c;">● Critical (80%+)</span>
                            </div>
                            <div style="margin: 10px 0;">
                                <strong>Flow Intensity:</strong><br>
                                <span style="color: #3498db;">— Light Flow</span><br>
                                <span style="color: #9b59b6;">— Medium Flow</span><br>
                                <span style="color: #e74c3c;">— Heavy Flow</span>
                            </div>
                        </div>
                        <div id="mapStats"></div>
                    </div>
                </div>
            </div>
            
            <div id="alerts" class="tab-content">
                <div class="grid">
                    <div class="card">
                        <h3>🚨 Alert Summary</h3>
                        <div class="chart-container">
                            <canvas id="alertChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>📊 Alert Statistics</h3>
                        <div id="alertStats"></div>
                        <button class="btn" onclick="updateAlertDashboard()">Update Alerts</button>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>📝 System Log</h3>
                <div id="log"></div>
            </div>
        </div>
        
        <script>
            let flowChart, capacityChart, trendChart, alertChart;
            let crowdMap = null;
            let currentMapType = 'density';
            
            const log = document.getElementById('log');
            const locations = document.getElementById('locations');
            
            function switchTab(tabName) {
                // Hide all tab contents
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Remove active class from all tabs
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected tab content
                document.getElementById(tabName).classList.add('active');
                
                // Add active class to selected tab
                event.target.classList.add('active');
            }
            
            function addLog(message) {
                const time = new Date().toLocaleTimeString();
                log.innerHTML += `[${time}] ${message}\\n`;
                log.scrollTop = log.scrollHeight;
            }
            
            async function apiCall(endpoint, method = 'GET', body = null) {
                try {
                    const options = { method, headers: { 'Content-Type': 'application/json' } };
                    if (body) options.body = JSON.stringify(body);
                    
                    const response = await fetch(endpoint, options);
                    const data = await response.json();
                    return data;
                } catch (error) {
                    addLog(`❌ Error: ${error.message}`);
                    return null;
                }
            }
            
            function initCharts() {
                // Flow Chart
                const flowCtx = document.getElementById('flowChart').getContext('2d');
                flowChart = new Chart(flowCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: []
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true, title: { display: true, text: 'Flow Rate' } }
                        }
                    }
                });
                
                // Capacity Chart
                const capacityCtx = document.getElementById('capacityChart').getContext('2d');
                capacityChart = new Chart(capacityCtx, {
                    type: 'bar',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Current Capacity',
                            data: [],
                            backgroundColor: 'rgba(52, 152, 219, 0.8)'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true, max: 100, title: { display: true, text: 'Utilization %' } }
                        }
                    }
                });
                
                // Trend Chart
                const trendCtx = document.getElementById('trendChart').getContext('2d');
                trendChart = new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: []
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true, max: 1, title: { display: true, text: 'Density' } }
                        }
                    }
                });
                
                // Alert Chart
                const alertCtx = document.getElementById('alertChart').getContext('2d');
                alertChart = new Chart(alertCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Low', 'Medium', 'High', 'Critical'],
                        datasets: [{
                            data: [0, 0, 0, 0],
                            backgroundColor: ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }
            
            async function updateFlowChart() {
                addLog('📈 Updating flow chart...');
                const data = await apiCall('/api/visualization/flow_chart');
                if (data && data.data) {
                    const locations = [...new Set(data.data.map(d => d.location))];
                    const timestamps = [...new Set(data.data.map(d => new Date(d.timestamp).toLocaleTimeString()))];
                    
                    flowChart.data.labels = timestamps;
                    flowChart.data.datasets = locations.map((location, i) => ({
                        label: location,
                        data: data.data.filter(d => d.location === location).map(d => d.flow_rate),
                        borderColor: `hsl(${i * 60}, 70%, 50%)`,
                        fill: false
                    }));
                    flowChart.update();
                    addLog('✅ Flow chart updated');
                }
            }
            
            async function updateCapacityChart() {
                addLog('📊 Updating capacity chart...');
                const data = await apiCall('/api/visualization/capacity_chart');
                if (data && data.data) {
                    capacityChart.data.labels = data.data.map(d => d.location);
                    capacityChart.data.datasets[0].data = data.data.map(d => d.utilization);
                    capacityChart.update();
                    addLog('✅ Capacity chart updated');
                }
            }
            
            async function updateTrendChart() {
                addLog('📉 Updating trend analysis...');
                const data = await apiCall('/api/visualization/trend_analysis');
                if (data && data.data && data.data.length > 0) {
                    const firstLocation = data.data[0];
                    const historical = firstLocation.historical;
                    const predictions = firstLocation.predictions;
                    
                    const allData = [...historical, ...predictions];
                    const labels = allData.map(d => new Date(d.timestamp).toLocaleTimeString());
                    
                    trendChart.data.labels = labels;
                    trendChart.data.datasets = [
                        {
                            label: 'Historical',
                            data: historical.map(d => d.density),
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            fill: false
                        },
                        {
                            label: 'Predicted',
                            data: [...Array(historical.length).fill(null), ...predictions.map(d => d.density)],
                            borderColor: '#e74c3c',
                            borderDash: [5, 5],
                            fill: false
                        }
                    ];
                    trendChart.update();
                    addLog('✅ Trend analysis updated');
                }
            }
            
            async function updateHeatmap() {
                addLog('🗺️ Updating heatmap...');
                const data = await apiCall('/api/visualization/density_heatmap');
                if (data && data.data) {
                    const container = document.getElementById('heatmapContainer');
                    container.innerHTML = data.data.map(loc => `
                        <div class="heatmap-cell ${loc.intensity}">
                            <div><strong>${loc.location}</strong></div>
                            <div>${loc.count}/${loc.capacity}</div>
                            <div>${Math.round(loc.density * 100)}%</div>
                        </div>
                    `).join('');
                    addLog('✅ Heatmap updated');
                }
            }
            
            async function updateAlertDashboard() {
                addLog('🚨 Updating alert dashboard...');
                const data = await apiCall('/api/visualization/alert_dashboard');
                if (data && data.summary) {
                    const summary = data.summary;
                    
                    // Update alert chart
                    alertChart.data.datasets[0].data = [
                        summary.severity_distribution.low || 0,
                        summary.severity_distribution.medium || 0,
                        summary.severity_distribution.high || 0,
                        summary.severity_distribution.critical || 0
                    ];
                    alertChart.update();
                    
                    // Update alert stats
                    document.getElementById('alertStats').innerHTML = `
                        <div class="status medium">Total Alerts: ${summary.total_alerts}</div>
                        <div class="status low">Resolution Rate: ${summary.resolution_rate}%</div>
                        <div class="status ${summary.avg_response_time > 10 ? 'high' : 'low'}">Avg Response: ${summary.avg_response_time} min</div>
                    `;
                    
                    addLog('✅ Alert dashboard updated');
                }
            }
            
            async function generateVisualization(vizType) {
                addLog(`📊 Generating ${vizType}...`);
                const data = await apiCall('/api/agents/visualization/generate', 'POST', {
                    visualization_type: vizType
                });
                if (data) {
                    addLog(`📊 Visualization Agent: ${data.agent_response.substring(0, 100)}...`);
                    
                    // Auto-update relevant charts
                    if (vizType === 'density_heatmap') {
                        updateHeatmap();
                    } else if (vizType === 'capacity_chart') {
                        updateCapacityChart();
                    }
                }
            }
            
            function initMap() {
                // Create a simple map visualization using canvas
                const mapContainer = document.getElementById('mapContainer');
                mapContainer.innerHTML = `
                    <canvas id="crowdMapCanvas" width="800" height="500" style="width: 100%; height: 100%; border-radius: 8px;"></canvas>
                    <div id="mapControls" style="position: absolute; top: 10px; right: 10px; background: white; padding: 10px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <button class="btn" onclick="toggleHeatmap()" style="padding: 5px 10px; font-size: 12px;">Toggle Heatmap</button>
                    </div>
                `;
                
                // Initialize canvas map
                updateCrowdMap();
            }
            
            async function updateCrowdMap() {
                addLog(`🗺️ Updating crowd map (${currentMapType} view)...`);
                try {
                    const data = await apiCall(`/api/visualization/crowd_map?map_type=${currentMapType}`);
                    if (data && data.data) {
                        // Ensure all required arrays exist
                        const mapData = data.data;
                        mapData.markers = mapData.markers || [];
                        mapData.zones = mapData.zones || [];
                        mapData.flow_lines = mapData.flow_lines || [];
                        mapData.heatmap_points = mapData.heatmap_points || [];
                        
                        drawCrowdMap(mapData);
                        updateMapStats(data);
                        
                        if (data.error) {
                            addLog(`⚠️ Map warning: ${data.error}`);
                        } else {
                            addLog('✅ Crowd map updated');
                        }
                    } else {
                        addLog('❌ No map data received');
                    }
                } catch (error) {
                    addLog(`❌ Failed to update map: ${error.message}`);
                    // Draw empty map on error
                    drawCrowdMap({
                        markers: [],
                        zones: [],
                        flow_lines: [],
                        heatmap_points: []
                    });
                }
            }
            
            function drawCrowdMap(mapData) {
                const canvas = document.getElementById('crowdMapCanvas');
                if (!canvas) return;
                
                const ctx = canvas.getContext('2d');
                const width = canvas.width;
                const height = canvas.height;
                
                // Clear canvas
                ctx.clearRect(0, 0, width, height);
                
                // Draw background
                ctx.fillStyle = '#f8f9fa';
                ctx.fillRect(0, 0, width, height);
                
                // Draw venue outline
                ctx.strokeStyle = '#2c3e50';
                ctx.lineWidth = 3;
                ctx.strokeRect(50, 50, width - 100, height - 100);
                
                // Draw zones - safely handle array
                if (mapData.zones && Array.isArray(mapData.zones)) {
                    mapData.zones.forEach(zone => {
                        try {
                            const x = Math.abs(((zone.center.lng + 73.9851) * 10000) % width);
                            const y = Math.abs(((zone.center.lat - 40.7589) * 10000) % height);
                            const radius = Math.max(20, Math.min(100, zone.radius / 2 || 30));
                            
                            ctx.beginPath();
                            ctx.arc(x, y, radius, 0, 2 * Math.PI);
                            ctx.fillStyle = (zone.color || '#3498db') + '40'; // Add transparency
                            ctx.fill();
                            ctx.strokeStyle = zone.color || '#3498db';
                            ctx.lineWidth = 2;
                            ctx.stroke();
                        } catch (e) {
                            console.warn('Error drawing zone:', e);
                        }
                    });
                }
                
                // Draw flow lines - safely handle array
                if (mapData.flow_lines && Array.isArray(mapData.flow_lines)) {
                    mapData.flow_lines.forEach(line => {
                        try {
                            const startX = Math.abs(((line.start.lng + 73.9851) * 10000) % width);
                            const startY = Math.abs(((line.start.lat - 40.7589) * 10000) % height);
                            const endX = Math.abs(((line.end.lng + 73.9851) * 10000) % width);
                            const endY = Math.abs(((line.end.lat - 40.7589) * 10000) % height);
                            
                            ctx.beginPath();
                            ctx.moveTo(startX, startY);
                            ctx.lineTo(endX, endY);
                            ctx.strokeStyle = line.color || '#3498db';
                            ctx.lineWidth = Math.max(1, Math.min(10, line.width || 3));
                            ctx.stroke();
                            
                            // Draw arrow
                            const angle = Math.atan2(endY - startY, endX - startX);
                            const arrowX = endX - 10 * Math.cos(angle);
                            const arrowY = endY - 10 * Math.sin(angle);
                            
                            ctx.beginPath();
                            ctx.moveTo(endX, endY);
                            ctx.lineTo(arrowX - 5 * Math.cos(angle - Math.PI/6), arrowY - 5 * Math.sin(angle - Math.PI/6));
                            ctx.moveTo(endX, endY);
                            ctx.lineTo(arrowX - 5 * Math.cos(angle + Math.PI/6), arrowY - 5 * Math.sin(angle + Math.PI/6));
                            ctx.stroke();
                        } catch (e) {
                            console.warn('Error drawing flow line:', e);
                        }
                    });
                }
                
                // Draw markers - safely handle array
                if (mapData.markers && Array.isArray(mapData.markers)) {
                    mapData.markers.forEach(marker => {
                        try {
                            const x = Math.abs(((marker.position.lng + 73.9851) * 10000) % width);
                            const y = Math.abs(((marker.position.lat - 40.7589) * 10000) % height);
                            const size = marker.size === 'large' ? 12 : marker.size === 'medium' ? 8 : 6;
                            
                            // Draw marker circle
                            ctx.beginPath();
                            ctx.arc(x, y, size, 0, 2 * Math.PI);
                            ctx.fillStyle = marker.color || '#3498db';
                            ctx.fill();
                            ctx.strokeStyle = '#fff';
                            ctx.lineWidth = 2;
                            ctx.stroke();
                            
                            // Draw label
                            ctx.fillStyle = '#2c3e50';
                            ctx.font = '12px Arial';
                            ctx.textAlign = 'center';
                            const title = marker.title || 'Location';
                            ctx.fillText(title.split(' ')[0], x, y - size - 5);
                            
                            // Draw count
                            ctx.font = '10px Arial';
                            ctx.fillText(`${marker.count || 0}`, x, y + 3);
                        } catch (e) {
                            console.warn('Error drawing marker:', e);
                        }
                    });
                }
                
                // Draw legend
                ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
                ctx.fillRect(10, 10, 200, 120);
                ctx.strokeStyle = '#ddd';
                ctx.strokeRect(10, 10, 200, 120);
                
                ctx.fillStyle = '#2c3e50';
                ctx.font = '14px Arial';
                ctx.textAlign = 'left';
                ctx.fillText('Crowd Map Legend', 20, 30);
                
                const legendItems = [
                    { color: '#27ae60', text: 'Low Density' },
                    { color: '#f39c12', text: 'Medium Density' },
                    { color: '#e67e22', text: 'High Density' },
                    { color: '#e74c3c', text: 'Critical Density' }
                ];
                
                legendItems.forEach((item, i) => {
                    ctx.fillStyle = item.color;
                    ctx.beginPath();
                    ctx.arc(30, 50 + i * 20, 6, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    ctx.fillStyle = '#2c3e50';
                    ctx.font = '12px Arial';
                    ctx.textAlign = 'left';
                    ctx.fillText(item.text, 45, 55 + i * 20);
                });
                
                // Draw status message if no data
                if ((!mapData.markers || mapData.markers.length === 0) && 
                    (!mapData.zones || mapData.zones.length === 0)) {
                    ctx.fillStyle = '#7f8c8d';
                    ctx.font = '16px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText('No crowd data available', width / 2, height / 2);
                    ctx.font = '12px Arial';
                    ctx.fillText('Map will update when data becomes available', width / 2, height / 2 + 25);
                }
            }
            
            function updateMapStats(data) {
                const statsContainer = document.getElementById('mapStats');
                if (statsContainer) {
                    statsContainer.innerHTML = `
                        <div style="margin-top: 20px; padding: 10px; background: #ecf0f1; border-radius: 4px;">
                            <h4>📊 Current Statistics</h4>
                            <div>Total Crowd: <strong>${data.total_crowd || 0}</strong></div>
                            <div>Average Density: <strong>${Math.round((data.avg_density || 0) * 100)}%</strong></div>
                            <div>Active Zones: <strong>${(data.data.markers || []).length}</strong></div>
                            <div>Flow Lines: <strong>${(data.data.flow_lines || []).length}</strong></div>
                            <div style="margin-top: 10px; font-size: 12px; color: #666;">
                                Last Updated: ${new Date(data.timestamp).toLocaleTimeString()}
                            </div>
                            ${data.error ? `<div style="color: #e74c3c; font-size: 12px; margin-top: 5px;">⚠️ ${data.error}</div>` : ''}
                        </div>
                    `;
                }
            }
            
            function updateMapType(mapType) {
                currentMapType = mapType;
                updateCrowdMap();
                addLog(`🗺️ Switched to ${mapType} view`);
            }
            
            function toggleHeatmap() {
                addLog('🔥 Toggling heatmap overlay...');
                // This would toggle heatmap overlay in a real implementation
            }
            
            // Initialize charts when page loads
            window.onload = function() {
                initCharts();
                initMap();
                refreshStatus();
                updateFlowChart();
                updateCapacityChart();
                updateHeatmap();
                updateAlertDashboard();
                addLog('🚀 Dashboard initialized with visualizations and real-time map');
            };
            
            // Auto-refresh visualizations every 30 seconds
            setInterval(() => {
                if (document.getElementById('charts').classList.contains('active')) {
                    updateFlowChart();
                    updateCapacityChart();
                    updateTrendChart();
                } else if (document.getElementById('heatmap').classList.contains('active')) {
                    updateHeatmap();
                } else if (document.getElementById('alerts').classList.contains('active')) {
                    updateAlertDashboard();
                }
            }, 30000);

            // Auto-refresh map every 15 seconds when map tab is active
            setInterval(() => {
                if (document.getElementById('map').classList.contains('active')) {
                    updateCrowdMap();
                }
            }, 15000);
        </script>
    </body>
    </html>
    """)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)