from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    DATA_INGESTION = "data_ingestion"
    MOVEMENT_PREDICTION = "movement_prediction"
    ACTION_AGENT = "action_agent"
    LOST_AND_FOUND = "lost_and_found"
    NOTIFICATION = "notification"
    SUMMARIZATION = "summarization"
    VISUALIZATION = "visualization"


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]
    tool_id: Optional[str] = None


class AgentMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_calls: Optional[List[ToolCall]] = None


class AgentResponse(BaseModel):
    agent_id: str
    role: AgentRole
    content: str
    tool_results: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: Optional[float] = None


class CrowdData(BaseModel):
    location_id: str
    person_count: int
    density: float
    velocity: Dict[str, float]  # x, y components
    timestamp: datetime = Field(default_factory=datetime.now)


class LocationStatus(BaseModel):
    location_id: str
    name: str
    current_capacity: int
    max_capacity: int
    density_level: str  # low, medium, high, critical
    flow_rate: float
    timestamp: datetime = Field(default_factory=datetime.now)


class Alert(BaseModel):
    alert_id: str
    severity: str  # low, medium, high, critical
    message: str
    location_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    resolved: bool = False


class Person(BaseModel):
    person_id: str
    description: str
    last_seen_location: str
    last_seen_time: datetime
    clothing: str
    photo_url: Optional[str] = None


class ActionItem(BaseModel):
    action_id: str
    action_type: str  # halt_crowd, place_barrier, deploy_staff, reroute
    location_id: str
    description: str
    priority: int
    estimated_duration: int  # minutes
    status: str = "pending"  # pending, active, completed
    timestamp: datetime = Field(default_factory=datetime.now)
