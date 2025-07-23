from typing import Dict, Any, List, Optional
import json
import base64
from datetime import datetime, timedelta
import numpy as np
from ..tools.base_tools import BaseTool, ToolDefinition, ToolParameter


class CrowdVisualizationTool(BaseTool):
    """Tool for generating crowd visualization data and charts"""
    
    def __init__(self):
        super().__init__(
            name="generate_crowd_visualization",
            description="Generate visualization data for crowd density, flow patterns, and analytics"
        )
    
    async def execute(self, visualization_type: str, location_ids: List[str] = None, time_range: int = 60) -> Dict[str, Any]:
        """Generate visualization data based on type and parameters"""
        from ..simulator.crowd_simulator import CrowdSimulator
        simulator = CrowdSimulator()
        
        if visualization_type == "density_heatmap":
            return await self._generate_density_heatmap(simulator, location_ids)
        elif visualization_type == "flow_chart":
            return await self._generate_flow_chart(simulator, location_ids, time_range)
        elif visualization_type == "capacity_chart":
            return await self._generate_capacity_chart(simulator, location_ids)
        elif visualization_type == "trend_analysis":
            return await self._generate_trend_analysis(simulator, location_ids, time_range)
        else:
            return {"error": f"Unknown visualization type: {visualization_type}"}
    
    async def _generate_density_heatmap(self, simulator, location_ids: List[str] = None) -> Dict[str, Any]:
        """Generate heatmap data for crowd density"""
        if not location_ids:
            locations = await simulator.get_all_locations_status()
        else:
            locations = []
            for loc_id in location_ids:
                loc_data = await simulator.get_location_data(loc_id)
                if "error" not in loc_data:
                    locations.append(loc_data)
        
        heatmap_data = []
        for loc in locations:
            heatmap_data.append({
                "location": loc["name"],
                "location_id": loc["location_id"],
                "density": loc["density"],
                "intensity": self._get_density_color(loc["density"]),
                "count": loc["current_count"],
                "capacity": loc["max_capacity"]
            })
        
        return {
            "type": "density_heatmap",
            "data": heatmap_data,
            "max_density": max(loc["density"] for loc in locations) if locations else 0,
            "avg_density": sum(loc["density"] for loc in locations) / len(locations) if locations else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_flow_chart(self, simulator, location_ids: List[str], time_range: int) -> Dict[str, Any]:
        """Generate flow chart data showing crowd movement trends"""
        flow_data = []
        
        for i in range(time_range // 5):  # Data points every 5 minutes
            timestamp = datetime.now() - timedelta(minutes=time_range - (i * 5))
            
            for loc_id in (location_ids or ["central_plaza", "west_gate", "east_gate", "stage_area"]):
                loc_data = await simulator.get_location_data(loc_id)
                if "error" not in loc_data:
                    # Simulate historical flow data
                    flow_rate = np.random.normal(loc_data["flow_rate"], 5)
                    flow_data.append({
                        "timestamp": timestamp.isoformat(),
                        "location": loc_data["name"],
                        "location_id": loc_id,
                        "flow_rate": flow_rate,
                        "density": loc_data["density"] + np.random.normal(0, 0.1)
                    })
        
        return {
            "type": "flow_chart",
            "data": flow_data,
            "time_range": time_range,
            "locations": len(location_ids) if location_ids else 4,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_capacity_chart(self, simulator, location_ids: List[str]) -> Dict[str, Any]:
        """Generate capacity utilization chart"""
        if not location_ids:
            locations = await simulator.get_all_locations_status()
        else:
            locations = []
            for loc_id in location_ids:
                loc_data = await simulator.get_location_data(loc_id)
                if "error" not in loc_data:
                    locations.append(loc_data)
        
        capacity_data = []
        for loc in locations:
            utilization = (loc["current_count"] / loc["max_capacity"]) * 100
            status = self._get_capacity_status(utilization)
            
            capacity_data.append({
                "location": loc["name"],
                "location_id": loc["location_id"],
                "current": loc["current_count"],
                "capacity": loc["max_capacity"],
                "utilization": round(utilization, 1),
                "status": status,
                "available": loc["max_capacity"] - loc["current_count"]
            })
        
        return {
            "type": "capacity_chart",
            "data": capacity_data,
            "total_current": sum(loc["current_count"] for loc in locations),
            "total_capacity": sum(loc["max_capacity"] for loc in locations),
            "avg_utilization": sum((loc["current_count"] / loc["max_capacity"]) * 100 for loc in locations) / len(locations) if locations else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_trend_analysis(self, simulator, location_ids: List[str], time_range: int) -> Dict[str, Any]:
        """Generate trend analysis with predictions"""
        trend_data = []
        predictions = []
        
        for loc_id in (location_ids or ["central_plaza", "west_gate", "east_gate"]):
            loc_data = await simulator.get_location_data(loc_id)
            if "error" not in loc_data:
                # Generate historical trend (simulated)
                historical_points = []
                for i in range(12):  # 12 data points (1 hour with 5-min intervals)
                    timestamp = datetime.now() - timedelta(minutes=60 - (i * 5))
                    density = loc_data["density"] + np.random.normal(0, 0.15)
                    density = max(0, min(1, density))  # Clamp between 0-1
                    
                    historical_points.append({
                        "timestamp": timestamp.isoformat(),
                        "density": density,
                        "count": int(density * loc_data["max_capacity"])
                    })
                
                # Generate prediction (next 30 minutes)
                future_points = []
                current_trend = np.random.choice([-0.05, 0, 0.05], p=[0.3, 0.4, 0.3])  # Decreasing, stable, increasing
                
                for i in range(6):  # 6 future points (30 minutes)
                    timestamp = datetime.now() + timedelta(minutes=(i + 1) * 5)
                    predicted_density = loc_data["density"] + (current_trend * (i + 1))
                    predicted_density = max(0, min(1, predicted_density))
                    
                    future_points.append({
                        "timestamp": timestamp.isoformat(),
                        "density": predicted_density,
                        "count": int(predicted_density * loc_data["max_capacity"]),
                        "confidence": max(0.5, 0.9 - (i * 0.1))  # Decreasing confidence
                    })
                
                trend_data.append({
                    "location": loc_data["name"],
                    "location_id": loc_id,
                    "historical": historical_points,
                    "predictions": future_points,
                    "trend_direction": "increasing" if current_trend > 0 else "decreasing" if current_trend < 0 else "stable"
                })
        
        return {
            "type": "trend_analysis",
            "data": trend_data,
            "analysis_period": time_range,
            "prediction_period": 30,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_density_color(self, density: float) -> str:
        """Get color intensity for density heatmap"""
        if density < 0.3:
            return "green"
        elif density < 0.6:
            return "yellow"
        elif density < 0.8:
            return "orange"
        else:
            return "red"
    
    def _get_capacity_status(self, utilization: float) -> str:
        """Get status based on capacity utilization"""
        if utilization < 50:
            return "low"
        elif utilization < 70:
            return "medium"
        elif utilization < 85:
            return "high"
        else:
            return "critical"
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="visualization_type", 
                    type="string", 
                    description="Type of visualization to generate",
                    enum_values=["density_heatmap", "flow_chart", "capacity_chart", "trend_analysis"]
                ),
                ToolParameter(
                    name="location_ids", 
                    type="array", 
                    description="List of location IDs to include", 
                    required=False
                ),
                ToolParameter(
                    name="time_range", 
                    type="integer", 
                    description="Time range in minutes for temporal data", 
                    required=False
                )
            ]
        )


class AlertVisualizationTool(BaseTool):
    """Tool for generating alert and incident visualizations"""
    
    def __init__(self):
        super().__init__(
            name="generate_alert_visualization",
            description="Generate visualization data for alerts, incidents, and safety metrics"
        )
    
    async def execute(self, alert_type: str = "all", time_period: int = 24) -> Dict[str, Any]:
        """Generate alert visualization data"""
        # Simulate alert data
        alert_types = ["stampede_risk", "high_density", "blocked_exit", "lost_person", "medical_emergency"]
        severity_levels = ["low", "medium", "high", "critical"]
        
        alerts = []
        for i in range(20):  # Generate 20 sample alerts
            timestamp = datetime.now() - timedelta(hours=np.random.randint(0, time_period))
            alerts.append({
                "alert_id": f"alert_{i:03d}",
                "type": np.random.choice(alert_types),
                "severity": np.random.choice(severity_levels),
                "location": np.random.choice(["central_plaza", "west_gate", "east_gate", "stage_area", "food_court"]),
                "timestamp": timestamp.isoformat(),
                "resolved": np.random.choice([True, False], p=[0.8, 0.2]),
                "response_time": np.random.randint(2, 15) if np.random.choice([True, False], p=[0.8, 0.2]) else None
            })
        
        # Filter by alert type if specified
        if alert_type != "all":
            alerts = [a for a in alerts if a["type"] == alert_type]
        
        # Generate summary statistics
        total_alerts = len(alerts)
        resolved_alerts = len([a for a in alerts if a["resolved"]])
        avg_response_time = np.mean([a["response_time"] for a in alerts if a["response_time"]]) if any(a["response_time"] for a in alerts) else 0
        
        severity_counts = {}
        for severity in severity_levels:
            severity_counts[severity] = len([a for a in alerts if a["severity"] == severity])
        
        return {
            "type": "alert_visualization",
            "alerts": alerts,
            "summary": {
                "total_alerts": total_alerts,
                "resolved_alerts": resolved_alerts,
                "resolution_rate": round((resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0, 1),
                "avg_response_time": round(avg_response_time, 1),
                "severity_distribution": severity_counts
            },
            "time_period": time_period,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="alert_type", 
                    type="string", 
                    description="Type of alerts to visualize", 
                    enum_values=["all", "stampede_risk", "high_density", "blocked_exit", "lost_person", "medical_emergency"],
                    required=False
                ),
                ToolParameter(
                    name="time_period", 
                    type="integer", 
                    description="Time period in hours to analyze", 
                    required=False
                )
            ]
        )


class MapVisualizationTool(BaseTool):
    """Tool for generating real-time crowd map visualizations"""
    
    def __init__(self):
        super().__init__(
            name="generate_crowd_map",
            description="Generate real-time map visualization with crowd density and flow data"
        )
    
    async def execute(self, map_type: str = "density", zoom_level: int = 16) -> Dict[str, Any]:
        """Generate map visualization data"""
        try:
            from ..simulator.crowd_simulator import CrowdSimulator
            simulator = CrowdSimulator()
            
            # Simulated venue coordinates (example: large stadium/event venue)
            venue_center = {"lat": 40.7589, "lng": -73.9851}  # Near Times Square for demo
            
            # Get all location data with error handling
            try:
                locations = await simulator.get_all_locations_status()
                if not locations:
                    # Generate fallback demo data if simulator returns empty
                    locations = self._generate_fallback_locations()
            except Exception as e:
                print(f"Error getting locations from simulator: {e}")
                locations = self._generate_fallback_locations()
            
            # Generate map markers and zones
            map_data = {
                "center": venue_center,
                "zoom": zoom_level,
                "markers": [],
                "heatmap_points": [],
                "zones": [],
                "flow_lines": []
            }
            
            # Define location coordinates (relative to venue center)
            location_coords = {
                "main_entrance": {"lat": 40.7580, "lng": -73.9840},
                "west_gate": {"lat": 40.7585, "lng": -73.9860},
                "east_gate": {"lat": 40.7585, "lng": -73.9830},
                "north_exit": {"lat": 40.7600, "lng": -73.9851},
                "south_exit": {"lat": 40.7570, "lng": -73.9851},
                "central_plaza": {"lat": 40.7589, "lng": -73.9851},
                "food_court": {"lat": 40.7580, "lng": -73.9855},
                "stage_area": {"lat": 40.7595, "lng": -73.9845}
            }
            
            # Process locations data
            if locations and len(locations) > 0:
                for loc in locations:
                    if isinstance(loc, dict) and "error" not in loc:
                        loc_id = loc.get("location_id", "unknown")
                        coords = location_coords.get(loc_id, venue_center)
                        density = max(0.0, min(1.0, float(loc.get("density", 0))))
                        
                        # Create marker for each location
                        marker = {
                            "id": loc_id,
                            "position": coords,
                            "title": loc.get("name", "Unknown Location"),
                            "density": density,
                            "count": int(loc.get("current_count", 0)),
                            "capacity": int(loc.get("max_capacity", 100)),
                            "status": loc.get("status", "unknown"),
                            "color": self._get_marker_color(density),
                            "size": self._get_marker_size(int(loc.get("current_count", 0)), int(loc.get("max_capacity", 100)))
                        }
                        map_data["markers"].append(marker)
                        
                        # Add heatmap points
                        intensity = density * 100
                        for i in range(max(1, int(intensity // 10) + 1)):  # Create multiple points for higher density
                            heatmap_point = {
                                "lat": coords["lat"] + np.random.normal(0, 0.0002),
                                "lng": coords["lng"] + np.random.normal(0, 0.0002),
                                "weight": density
                            }
                            map_data["heatmap_points"].append(heatmap_point)
                        
                        # Create zones (circular areas around locations)
                        zone = {
                            "center": coords,
                            "radius": 50 + (density * 100),  # Radius based on density
                            "color": self._get_zone_color(density),
                            "opacity": 0.3 + (density * 0.4),
                            "location": loc.get("name", "Unknown Location"),
                            "density": density
                        }
                        map_data["zones"].append(zone)
            
            # Generate flow lines between connected locations
            if map_type in ["flow", "density"]:
                connections = [
                    ("main_entrance", "central_plaza"),
                    ("west_gate", "central_plaza"),
                    ("east_gate", "central_plaza"),
                    ("central_plaza", "food_court"),
                    ("central_plaza", "stage_area"),
                    ("food_court", "south_exit"),
                    ("stage_area", "north_exit")
                ]
                
                for start_id, end_id in connections:
                    if start_id in location_coords and end_id in location_coords:
                        start_coords = location_coords[start_id]
                        end_coords = location_coords[end_id]
                        
                        # Simulate flow intensity
                        flow_intensity = np.random.uniform(0.1, 1.0)
                        
                        flow_line = {
                            "start": start_coords,
                            "end": end_coords,
                            "intensity": flow_intensity,
                            "color": self._get_flow_color(flow_intensity),
                            "width": 2 + (flow_intensity * 8),
                            "direction": np.random.choice(["bidirectional", "start_to_end", "end_to_start"])
                        }
                        map_data["flow_lines"].append(flow_line)
            
            # Calculate totals
            total_crowd = sum(marker["count"] for marker in map_data["markers"])
            avg_density = sum(marker["density"] for marker in map_data["markers"]) / len(map_data["markers"]) if map_data["markers"] else 0
            
            return {
                "type": "crowd_map",
                "map_type": map_type,
                "data": map_data,
                "timestamp": datetime.now().isoformat(),
                "total_crowd": total_crowd,
                "avg_density": avg_density
            }
            
        except Exception as e:
            print(f"Error in map visualization: {e}")
            # Return safe fallback structure on any error
            return self._generate_fallback_map_data(map_type, zoom_level)
    
    def _generate_fallback_locations(self) -> List[Dict[str, Any]]:
        """Generate fallback location data when simulator is unavailable"""
        return [
            {
                "location_id": "central_plaza",
                "name": "Central Plaza", 
                "current_count": 450,
                "max_capacity": 1000,
                "density": 0.45,
                "flow_rate": 5.0,
                "status": "medium",
                "timestamp": datetime.now().isoformat()
            },
            {
                "location_id": "stage_area",
                "name": "Stage Area",
                "current_count": 600, 
                "max_capacity": 800,
                "density": 0.75,
                "flow_rate": 8.5,
                "status": "high",
                "timestamp": datetime.now().isoformat()
            },
            {
                "location_id": "food_court",
                "name": "Food Court",
                "current_count": 220,
                "max_capacity": 400, 
                "density": 0.55,
                "flow_rate": 3.2,
                "status": "medium",
                "timestamp": datetime.now().isoformat()
            }
        ]
    
    def _generate_fallback_map_data(self, map_type: str, zoom_level: int) -> Dict[str, Any]:
        """Generate fallback map data with demo locations"""
        venue_center = {"lat": 40.7589, "lng": -73.9851}
        
        # Generate demo markers
        demo_locations = [
            {"id": "central_plaza", "name": "Central Plaza", "lat": 40.7589, "lng": -73.9851, "density": 0.45, "count": 450, "capacity": 1000},
            {"id": "stage_area", "name": "Stage Area", "lat": 40.7595, "lng": -73.9845, "density": 0.75, "count": 600, "capacity": 800},
            {"id": "food_court", "name": "Food Court", "lat": 40.7580, "lng": -73.9855, "density": 0.55, "count": 220, "capacity": 400}
        ]
        
        markers = []
        zones = []
        heatmap_points = []
        
        for loc in demo_locations:
            # Create marker
            marker = {
                "id": loc["id"],
                "position": {"lat": loc["lat"], "lng": loc["lng"]},
                "title": loc["name"],
                "density": loc["density"],
                "count": loc["count"],
                "capacity": loc["capacity"],
                "status": "demo",
                "color": self._get_marker_color(loc["density"]),
                "size": self._get_marker_size(loc["count"], loc["capacity"])
            }
            markers.append(marker)
            
            # Create zone
            zone = {
                "center": {"lat": loc["lat"], "lng": loc["lng"]},
                "radius": 50 + (loc["density"] * 100),
                "color": self._get_zone_color(loc["density"]),
                "opacity": 0.3 + (loc["density"] * 0.4),
                "location": loc["name"],
                "density": loc["density"]
            }
            zones.append(zone)
            
            # Create heatmap points
            for i in range(max(1, int(loc["density"] * 10))):
                heatmap_point = {
                    "lat": loc["lat"] + np.random.normal(0, 0.0002),
                    "lng": loc["lng"] + np.random.normal(0, 0.0002),
                    "weight": loc["density"]
                }
                heatmap_points.append(heatmap_point)
        
        return {
            "type": "crowd_map",
            "map_type": map_type,
            "data": {
                "center": venue_center,
                "zoom": zoom_level,
                "markers": markers,
                "zones": zones,
                "flow_lines": [],
                "heatmap_points": heatmap_points
            },
            "timestamp": datetime.now().isoformat(),
            "total_crowd": sum(loc["count"] for loc in demo_locations),
            "avg_density": sum(loc["density"] for loc in demo_locations) / len(demo_locations),
            "note": "Demo data - simulator unavailable"
        }
    def _get_marker_color(self, density: float) -> str:
        """Get marker color based on density"""
        if density < 0.3:
            return "#27ae60"
        elif density < 0.6:
            return "#f39c12"
        elif density < 0.8:
            return "#e67e22"
        else:
            return "#e74c3c"
    
    def _get_marker_size(self, count: int, capacity: int) -> str:
        """Get marker size based on capacity utilization"""
        utilization = count / capacity if capacity > 0 else 0
        if utilization < 0.3:
            return "small"
        elif utilization < 0.7:
            return "medium"
        else:
            return "large"
    
    def _get_zone_color(self, density: float) -> str:
        """Get zone color based on density"""
        return self._get_marker_color(density)
    
    def _get_flow_color(self, intensity: float) -> str:
        """Get flow line color based on intensity"""
        if intensity < 0.3:
            return "#3498db"
        elif intensity < 0.7:
            return "#9b59b6"
        else:
            return "#e74c3c"
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="map_type",
                    type="string",
                    description="Type of map visualization to generate",
                    enum_values=["density", "flow", "zones"],
                    required=False
                ),
                ToolParameter(
                    name="zoom_level",
                    type="integer",
                    description="Map zoom level (10-20)",
                    required=False
                )
            ]
        )
