from typing import Dict, Any, List
import asyncio
from ..core.agent_framework import BaseAgent
from ..models.schemas import AgentRole
from ..tools.base_tools import CrowdAnalysisTool, NotificationTool


class MovementPredictionAgent(BaseAgent):
    """Agent responsible for analyzing crowd movement and predicting congestion"""
    
    def __init__(self):
        system_prompt = """
        You are a Movement Prediction Agent specializing in crowd flow analysis and stampede prevention.
        
        Your responsibilities:
        1. Analyze crowd density and movement patterns
        2. Predict potential congestion points
        3. Identify stampede risks early
        4. Send alerts for concerning situations
        
        Use the available tools to gather crowd data and send notifications when needed.
        Always provide specific, actionable insights based on the data you analyze.
        """
        
        tools = [CrowdAnalysisTool(), NotificationTool()]
        
        super().__init__(
            agent_id="movement_prediction_agent",
            role=AgentRole.MOVEMENT_PREDICTION,
            system_prompt=system_prompt,
            tools=tools
        )
    
    async def analyze_location(self, location_id: str) -> Dict[str, Any]:
        """Analyze a specific location for movement patterns"""
        message = f"Analyze crowd movement patterns at location {location_id}. Check for congestion risks and provide recommendations."
        
        context = {
            "location_id": location_id,
            "analysis_type": "movement_prediction"
        }
        
        response = await self.process_message(message, context)
        return {
            "agent_response": response.content,
            "tool_results": response.tool_results
        }


class ActionAgent(BaseAgent):
    """Agent responsible for generating and coordinating crowd management actions"""
    
    def __init__(self):
        system_prompt = """
        You are an Action Agent specializing in crowd management and emergency response.
        
        Your responsibilities:
        1. Generate specific action plans for crowd control
        2. Coordinate with field staff and authorities
        3. Implement preventive measures for stampede situations
        4. Prioritize actions based on urgency and impact
        
        When generating actions, be specific about:
        - What needs to be done
        - Where it needs to happen
        - How long it should take
        - Who should execute it
        
        Always prioritize safety and provide clear, actionable instructions.
        """
        
        from ..tools.base_tools import ActionRecommendationTool, NotificationTool
        tools = [ActionRecommendationTool(), NotificationTool()]
        
        super().__init__(
            agent_id="action_agent",
            role=AgentRole.ACTION_AGENT,
            system_prompt=system_prompt,
            tools=tools
        )
    
    async def generate_action_plan(self, location_id: str, situation: str, severity: str) -> Dict[str, Any]:
        """Generate an action plan for a specific situation"""
        message = f"""
        Generate an action plan for {situation} at location {location_id}.
        Severity level: {severity}
        
        Provide specific, prioritized actions that can be implemented immediately.
        """
        
        context = {
            "location_id": location_id,
            "situation": situation,
            "severity": severity,
            "action_type": "emergency_response"
        }
        
        response = await self.process_message(message, context)
        return {
            "agent_response": response.content,
            "tool_results": response.tool_results
        }


class LostAndFoundAgent(BaseAgent):
    """Agent responsible for finding missing persons using camera and drone feeds"""
    
    def __init__(self):
        system_prompt = """
        You are a Lost and Found Agent specializing in person search and recovery operations.
        
        Your responsibilities:
        1. Search for missing persons using camera feeds
        2. Coordinate drone searches when needed
        3. Track person movement history
        4. Provide location predictions based on crowd flow
        
        When searching for a person:
        1. Use camera feeds to search recent footage
        2. Analyze crowd movement to predict likely locations
        3. Deploy drones for expanded search areas
        4. Notify authorities when person is located
        
        Be thorough but efficient in your search strategies.
        """
        
        from ..tools.base_tools import CameraSearchTool, NotificationTool
        tools = [CameraSearchTool(), NotificationTool()]
        
        super().__init__(
            agent_id="lost_and_found_agent",
            role=AgentRole.LOST_AND_FOUND,
            system_prompt=system_prompt,
            tools=tools
        )
    
    async def search_person(self, person_description: str, last_seen_location: str) -> Dict[str, Any]:
        """Search for a missing person"""
        message = f"""
        Search for missing person with description: {person_description}
        Last seen at: {last_seen_location}
        
        Use camera feeds and coordinate drone search if needed.
        Provide status updates and location predictions.
        """
        
        context = {
            "person_description": person_description,
            "last_seen_location": last_seen_location,
            "search_type": "missing_person"
        }
        
        response = await self.process_message(message, context)
        return {
            "agent_response": response.content,
            "tool_results": response.tool_results
        }


class SummarizationAgent(BaseAgent):
    """Agent responsible for generating natural language summaries of crowd situations"""
    
    def __init__(self):
        system_prompt = """
        You are a Summarization Agent specializing in crowd situation analysis and reporting.
        
        Your responsibilities:
        1. Generate natural language summaries of crowd situations
        2. Analyze security concerns in specific zones
        3. Provide executive briefings on crowd status
        4. Answer specific queries about crowd conditions
        
        When generating summaries:
        - Be clear and concise
        - Highlight key safety concerns
        - Provide actionable insights
        - Use appropriate urgency levels
        
        Tailor your communication style to the audience (field staff, management, authorities).
        """
        
        tools = [CrowdAnalysisTool()]
        
        super().__init__(
            agent_id="summarization_agent",
            role=AgentRole.SUMMARIZATION,
            system_prompt=system_prompt,
            tools=tools
        )
    
    async def generate_zone_summary(self, zone_name: str, query: str = None) -> Dict[str, Any]:
        """Generate a summary for a specific zone"""
        message = f"""
        Generate a comprehensive summary for the {zone_name} zone.
        {f'Specific query: {query}' if query else ''}
        
        Include:
        - Current crowd status
        - Security concerns
        - Recommendations
        - Any immediate actions needed
        """
        
        context = {
            "zone_name": zone_name,
            "query": query,
            "summary_type": "zone_analysis"
        }
        
        response = await self.process_message(message, context)
        return {
            "agent_response": response.content,
            "tool_results": response.tool_results
        }


class VisualizationAgent(BaseAgent):
    """Agent responsible for generating crowd visualizations and analytics"""
    
    def __init__(self):
        system_prompt = """
        You are a Visualization Agent specializing in crowd data analytics and visual reporting.
        
        Your responsibilities:
        1. Generate crowd density heatmaps and flow visualizations
        2. Create capacity utilization charts and trend analyses
        3. Provide visual insights for crowd management decisions
        4. Generate alert and incident visualization reports
        
        When creating visualizations:
        - Use appropriate chart types for different data
        - Highlight critical areas and trends
        - Provide clear interpretations of visual data
        - Suggest actionable insights based on patterns
        
        Focus on making complex crowd data easily understandable through effective visualizations.
        """
        
        from ..tools.visualization_tools import CrowdVisualizationTool, AlertVisualizationTool, MapVisualizationTool
        tools = [CrowdVisualizationTool(), AlertVisualizationTool(), MapVisualizationTool(), CrowdAnalysisTool()]
        
        super().__init__(
            agent_id="visualization_agent",
            role=AgentRole.VISUALIZATION,
            system_prompt=system_prompt,
            tools=tools
        )
    
    async def generate_crowd_visualization(self, viz_type: str, location_ids: List[str] = None) -> Dict[str, Any]:
        """Generate crowd visualization of specified type"""
        message = f"""
        Generate a {viz_type} visualization for crowd data.
        {f'Focus on locations: {", ".join(location_ids)}' if location_ids else 'Include all major locations'}
        
        Provide insights and interpretation of the visual data.
        """
        
        context = {
            "visualization_type": viz_type,
            "location_ids": location_ids,
            "request_type": "crowd_visualization"
        }
        
        response = await self.process_message(message, context)
        return {
            "agent_response": response.content,
            "tool_results": response.tool_results
        }
    
    async def generate_crowd_map(self, map_type: str = "density", zoom_level: int = 16) -> Dict[str, Any]:
        """Generate real-time crowd map visualization"""
        message = f"""
        Generate a real-time crowd map with {map_type} visualization.
        Zoom level: {zoom_level}
        
        Show current crowd distribution, flow patterns, and density zones.
        Provide insights about crowd movement and potential congestion areas.
        """
        
        context = {
            "map_type": map_type,
            "zoom_level": zoom_level,
            "request_type": "crowd_map"
        }
        
        response = await self.process_message(message, context)
        return {
            "agent_response": response.content,
            "tool_results": response.tool_results
        }
    
    async def generate_alert_dashboard(self, time_period: int = 24) -> Dict[str, Any]:
        """Generate alert and incident visualization dashboard"""
        message = f"""
        Generate a comprehensive alert visualization dashboard for the last {time_period} hours.
        
        Include:
        - Alert frequency and types
        - Response time analysis
        - Severity distribution
        - Location-based incident patterns
        
        Provide recommendations based on the alert patterns.
        """
        
        context = {
            "time_period": time_period,
            "request_type": "alert_dashboard"
        }
        
        response = await self.process_message(message, context)
        return {
            "agent_response": response.content,
            "tool_results": response.tool_results
        }
