import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

# Google ADK imports
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool, GenerateContentResponse
from google.generativeai import caching
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.schemas import AgentRole, AgentMessage, AgentResponse, ToolCall
from ..tools.base_tools import BaseTool
from ..config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class ModelConfig:
    """Configuration for Gemini models"""
    model_name: str = "gemini-1.5-pro"
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_output_tokens: int = 2048
    safety_settings: Optional[Dict] = None
    
    def to_generation_config(self):
        """Convert to Gemini GenerationConfig"""
        return genai.GenerationConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            max_output_tokens=self.max_output_tokens,
        )


class GeminiAgentFramework:
    """Core framework for Gemini-powered agents with tool calling"""
    
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        self.model_name = model_name
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.tools_registry: Dict[str, BaseTool] = {}
        
        # Configure Gemini
        api_key = settings.google_cloud.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("No Gemini API key found - some features may be limited")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def register_agent(self, agent: 'BaseAgent'):
        """Register an agent in the framework"""
        self.agents[agent.agent_id] = agent
        agent._framework = self
        logger.info(f"Registered agent: {agent.agent_id}")
    
    def register_tool(self, tool: BaseTool):
        """Register a tool in the framework"""
        self.tools_registry[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name"""
        if tool_name not in self.tools_registry:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        
        tool = self.tools_registry[tool_name]
        return await tool.execute(**kwargs)
    
    async def send_message_to_agent(self, agent_id: str, message: str, context: Optional[Dict] = None) -> AgentResponse:
        """Send a message to a specific agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent '{agent_id}' not found")
        
        agent = self.agents[agent_id]
        return await agent.process_message(message, context)


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, agent_id: str, role: AgentRole, system_prompt: str, tools: Optional[List[BaseTool]] = None):
        self.agent_id = agent_id
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.conversation_history: List[AgentMessage] = []
        self._framework: Optional[GeminiAgentFramework] = None
    
    def _create_gemini_tools(self) -> List[Tool]:
        """Convert agent tools to Gemini tool format"""
        if not self.tools:
            return []
        
        function_declarations = []
        for tool in self.tools:
            definition = tool.get_definition()
            
            # Convert parameters to Gemini format
            properties = {}
            required = []
            
            for param in definition.parameters:
                param_schema = {"type": param.type, "description": param.description}
                if param.enum_values:
                    param_schema["enum"] = param.enum_values
                
                properties[param.name] = param_schema
                if param.required:
                    required.append(param.name)
            
            function_declarations.append(
                FunctionDeclaration(
                    name=definition.name,
                    description=definition.description,
                    parameters={
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                )
            )
        
        return [Tool(function_declarations=function_declarations)] if function_declarations else []
    
    async def process_message(self, message: str, context: Optional[Dict] = None) -> AgentResponse:
        """Process a message and return response"""
        try:
            # Check if framework is available
            if not self._framework:
                logger.warning(f"Agent {self.agent_id} has no framework reference, using mock response")
                return AgentResponse(
                    agent_id=self.agent_id,
                    role=self.role,
                    content=f"Mock response from {self.agent_id}: {message[:100]}..."
                )
            
            # Add message to history
            agent_message = AgentMessage(role="user", content=message)
            self.conversation_history.append(agent_message)
            
            # Prepare conversation for Gemini
            conversation_text = self._build_conversation_text(context)
            
            # Create chat with tools using framework's model
            gemini_tools = self._create_gemini_tools()
            chat = self._framework.model.start_chat(history=[])
            
            # Send message
            response = await asyncio.to_thread(
                chat.send_message,
                conversation_text,
                tools=gemini_tools if gemini_tools else None
            )
            
            # Process tool calls if any
            tool_results = []
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        tool_result = await self._execute_function_call(part.function_call)
                        tool_results.append(tool_result)
            
            # Get text response
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Add assistant response to history
            assistant_message = AgentMessage(role="assistant", content=response_text)
            self.conversation_history.append(assistant_message)
            
            return AgentResponse(
                agent_id=self.agent_id,
                role=self.role,
                content=response_text,
                tool_results=tool_results if tool_results else None
            )
            
        except Exception as e:
            logger.error(f"Error processing message in agent {self.agent_id}: {str(e)}")
            return AgentResponse(
                agent_id=self.agent_id,
                role=self.role,
                content=f"Error processing request: {str(e)}"
            )
    
    async def _execute_function_call(self, function_call) -> Dict[str, Any]:
        """Execute a function call from Gemini"""
        try:
            function_name = function_call.name
            function_args = dict(function_call.args)
            
            if self._framework:
                result = await self._framework.execute_tool(function_name, **function_args)
                return {
                    "tool_name": function_name,
                    "arguments": function_args,
                    "result": result
                }
            else:
                return {
                    "tool_name": function_name,
                    "arguments": function_args,
                    "error": "No framework available for tool execution"
                }
                
        except Exception as e:
            logger.error(f"Error executing function call: {str(e)}")
            return {
                "tool_name": function_call.name,
                "arguments": dict(function_call.args),
                "error": str(e)
            }
    
    def _build_conversation_text(self, context: Optional[Dict] = None) -> str:
        """Build conversation text for Gemini"""
        conversation = f"System: {self.system_prompt}\n\n"
        
        if context:
            conversation += f"Context: {json.dumps(context, indent=2)}\n\n"
        
        # Add recent conversation history
        for msg in self.conversation_history[-10:]:  # Last 10 messages
            conversation += f"{msg.role.title()}: {msg.content}\n"
        
        return conversation
