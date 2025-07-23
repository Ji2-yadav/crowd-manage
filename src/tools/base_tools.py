from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel


class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    enum_values: Optional[List[str]] = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: List[ToolParameter]


class BaseTool(ABC):
    """Base class for all agent tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Get the tool definition for the agent"""
        pass


class CrowdAnalysisTool(BaseTool):
    """Tool for analyzing crowd data at specific locations"""
    
    def __init__(self):
        super().__init__(
            name="analyze_crowd_data",
            description="Analyze crowd density, flow, and movement patterns at a specific location"
        )
    
    async def execute(self, location_id: str, time_window: int = 5) -> Dict[str, Any]:
        # Simulate crowd analysis
        try:
            from ..simulator.crowd_simulator import CrowdSimulator
            simulator = CrowdSimulator()
            location_data = await simulator.get_location_data(location_id)
            
            # Handle error responses from simulator
            if "error" in location_data:
                # Return fallback data for demo purposes
                location_data = {
                    "density": 0.45,
                    "flow_rate": 5.0,
                    "name": location_id.replace("_", " ").title(),
                    "current_count": 150,
                    "max_capacity": 300
                }
        except Exception as e:
            # Fallback data if simulator is unavailable
            location_data = {
                "density": 0.45,
                "flow_rate": 5.0,
                "name": location_id.replace("_", " ").title(),
                "current_count": 150,
                "max_capacity": 300
            }
        
        return {
            "location_id": location_id,
            "current_density": location_data.get("density", 0.0),
            "flow_rate": location_data.get("flow_rate", 0.0),
            "predicted_congestion": location_data.get("density", 0.0) > 0.7,
            "recommendation": "Monitor closely" if location_data.get("density", 0.0) > 0.5 else "Normal"
        }
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(name="location_id", type="string", description="ID of the location to analyze"),
                ToolParameter(name="time_window", type="integer", description="Time window in minutes", required=False)
            ]
        )


class NotificationTool(BaseTool):
    """Tool for sending notifications to authorities"""
    
    def __init__(self):
        super().__init__(
            name="send_notification",
            description="Send alert notifications to crowd control authorities"
        )
    
    async def execute(self, message: str, severity: str, location_id: str) -> Dict[str, Any]:
        # Simulate notification sending
        print(f"🚨 ALERT [{severity.upper()}] at {location_id}: {message}")
        
        return {
            "status": "sent",
            "notification_id": f"notif_{location_id}_{severity}",
            "timestamp": "2025-07-22T10:30:00Z",
            "recipients": ["control_center", "field_staff"]
        }
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(name="message", type="string", description="Alert message content"),
                ToolParameter(name="severity", type="string", description="Alert severity level", 
                            enum_values=["low", "medium", "high", "critical"]),
                ToolParameter(name="location_id", type="string", description="Location where alert originated")
            ]
        )


class ActionRecommendationTool(BaseTool):
    """Tool for generating crowd management action recommendations"""
    
    def __init__(self):
        super().__init__(
            name="recommend_actions",
            description="Generate specific crowd management actions based on current situation"
        )
    
    async def execute(self, location_id: str, crowd_density: float, issue_type: str) -> Dict[str, Any]:
        actions = []
        
        if crowd_density > 0.8:
            actions.append({
                "type": "halt_crowd",
                "description": f"Temporarily halt crowd entry at {location_id}",
                "priority": "high",
                "duration": 15
            })
        
        if crowd_density > 0.6:
            actions.append({
                "type": "deploy_staff",
                "description": f"Deploy additional crowd control staff to {location_id}",
                "priority": "medium",
                "staff_count": 3
            })
        
        if issue_type == "stampede_risk":
            actions.append({
                "type": "place_barrier",
                "description": f"Install temporary barriers at {location_id} to control flow",
                "priority": "critical",
                "barrier_count": 2
            })
        
        return {
            "location_id": location_id,
            "recommended_actions": actions,
            "total_actions": len(actions),
            "estimated_resolution_time": sum(action.get("duration", 10) for action in actions)
        }
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(name="location_id", type="string", description="Location requiring action"),
                ToolParameter(name="crowd_density", type="number", description="Current crowd density (0-1)"),
                ToolParameter(name="issue_type", type="string", description="Type of crowd issue detected",
                            enum_values=["congestion", "stampede_risk", "blocked_exit", "panic"])
            ]
        )


class CameraSearchTool(BaseTool):
    """Tool for searching person across camera feeds"""
    
    def __init__(self):
        super().__init__(
            name="search_cameras",
            description="Search for a person across multiple camera feeds"
        )
    
    async def execute(self, person_description: str, search_area: str, time_range: int = 60) -> Dict[str, Any]:
        # Simulate camera search
        cameras_searched = [f"cam_{i}" for i in range(1, 6)]
        potential_matches = []
        
        # Simulate finding matches
        if "red shirt" in person_description.lower():
            potential_matches.append({
                "camera_id": "cam_3",
                "timestamp": "2025-07-22T10:25:00Z",
                "confidence": 0.85,
                "location": "West Gate"
            })
        
        return {
            "search_query": person_description,
            "cameras_searched": cameras_searched,
            "matches_found": len(potential_matches),
            "potential_matches": potential_matches,
            "search_duration": f"{time_range} minutes",
            "recommendation": "Check drone feed in West Gate area" if potential_matches else "Expand search area"
        }
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(name="person_description", type="string", description="Description of person to find"),
                ToolParameter(name="search_area", type="string", description="Area to focus search on"),
                ToolParameter(name="time_range", type="integer", description="Time range in minutes to search", required=False)
            ]
        )
