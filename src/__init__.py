"""
Initialization module for the Crowd Management Agentic AI system
"""

__version__ = "1.0.0"
__author__ = "Agentic AI Team"
__description__ = "Scalable crowd management system using Google ADK and Gemini models"

# Core exports
from .core.agent_framework import GeminiAgentFramework, BaseAgent
from .models.schemas import AgentRole, AgentMessage, AgentResponse

# Agent exports
from .agents.specialized_agents import (
    MovementPredictionAgent,
    ActionAgent, 
    LostAndFoundAgent,
    SummarizationAgent
)

# Tool exports
from .tools.base_tools import (
    BaseTool,
    CrowdAnalysisTool,
    NotificationTool,
    ActionRecommendationTool,
    CameraSearchTool
)

# Simulator exports
from .simulator.crowd_simulator import CrowdSimulator

__all__ = [
    # Core
    "GeminiAgentFramework",
    "BaseAgent",
    "AgentRole",
    "AgentMessage", 
    "AgentResponse",
    
    # Agents
    "MovementPredictionAgent",
    "ActionAgent",
    "LostAndFoundAgent", 
    "SummarizationAgent",
    
    # Tools
    "BaseTool",
    "CrowdAnalysisTool",
    "NotificationTool",
    "ActionRecommendationTool",
    "CameraSearchTool",
    
    # Simulator
    "CrowdSimulator"
]
