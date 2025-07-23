import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.core.agent_framework import GeminiAgentFramework, BaseAgent
from src.agents.specialized_agents import MovementPredictionAgent, ActionAgent
from src.tools.base_tools import CrowdAnalysisTool, NotificationTool
from src.models.schemas import AgentRole


class TestAgentFramework(unittest.TestCase):
    """Test cases for the agent framework"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.framework = GeminiAgentFramework("gemini-1.5-flash")  # Use flash for faster testing
        
    def test_framework_initialization(self):
        """Test framework initializes correctly"""
        self.assertIsNotNone(self.framework)
        self.assertEqual(len(self.framework.agents), 0)
        self.assertEqual(len(self.framework.tools_registry), 0)
    
    def test_tool_registration(self):
        """Test tool registration"""
        tool = CrowdAnalysisTool()
        self.framework.register_tool(tool)
        
        self.assertIn(tool.name, self.framework.tools_registry)
        self.assertEqual(self.framework.tools_registry[tool.name], tool)
    
    def test_agent_registration(self):
        """Test agent registration"""
        agent = MovementPredictionAgent()
        self.framework.register_agent(agent)
        
        self.assertIn(agent.agent_id, self.framework.agents)
        self.assertEqual(self.framework.agents[agent.agent_id], agent)
        self.assertEqual(agent._framework, self.framework)


class TestSpecializedAgents(unittest.TestCase):
    """Test cases for specialized agents"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.movement_agent = MovementPredictionAgent()
        self.action_agent = ActionAgent()
    
    def test_movement_agent_initialization(self):
        """Test movement prediction agent initialization"""
        self.assertEqual(self.movement_agent.role, AgentRole.MOVEMENT_PREDICTION)
        self.assertEqual(self.movement_agent.agent_id, "movement_prediction_agent")
        self.assertGreater(len(self.movement_agent.tools), 0)
    
    def test_action_agent_initialization(self):
        """Test action agent initialization"""
        self.assertEqual(self.action_agent.role, AgentRole.ACTION_AGENT)
        self.assertEqual(self.action_agent.agent_id, "action_agent")
        self.assertGreater(len(self.action_agent.tools), 0)


class TestTools(unittest.TestCase):
    """Test cases for agent tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.crowd_tool = CrowdAnalysisTool()
        self.notification_tool = NotificationTool()
    
    async def test_crowd_analysis_tool(self):
        """Test crowd analysis tool execution"""
        result = await self.crowd_tool.execute(location_id="test_location")
        
        self.assertIn("location_id", result)
        self.assertIn("current_density", result)
        self.assertIn("recommendation", result)
        self.assertEqual(result["location_id"], "test_location")
    
    async def test_notification_tool(self):
        """Test notification tool execution"""
        result = await self.notification_tool.execute(
            message="Test alert",
            severity="medium",
            location_id="test_location"
        )
        
        self.assertIn("status", result)
        self.assertIn("notification_id", result)
        self.assertEqual(result["status"], "sent")
    
    def test_tool_definitions(self):
        """Test tool definitions are properly formatted"""
        crowd_def = self.crowd_tool.get_definition()
        notification_def = self.notification_tool.get_definition()
        
        self.assertEqual(crowd_def.name, "analyze_crowd_data")
        self.assertGreater(len(crowd_def.parameters), 0)
        
        self.assertEqual(notification_def.name, "send_notification")
        self.assertGreater(len(notification_def.parameters), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.framework = GeminiAgentFramework("gemini-1.5-flash")
        
        # Register tools
        self.framework.register_tool(CrowdAnalysisTool())
        self.framework.register_tool(NotificationTool())
        
        # Register agents
        self.framework.register_agent(MovementPredictionAgent())
        self.framework.register_agent(ActionAgent())
    
    def test_complete_system_setup(self):
        """Test that the complete system sets up correctly"""
        self.assertEqual(len(self.framework.tools_registry), 2)
        self.assertEqual(len(self.framework.agents), 2)
        
        # Check agents have framework reference
        for agent in self.framework.agents.values():
            self.assertEqual(agent._framework, self.framework)


async def run_async_tests():
    """Run async test methods"""
    test_tools = TestTools()
    test_tools.setUp()
    
    print("🧪 Running async tool tests...")
    await test_tools.test_crowd_analysis_tool()
    await test_tools.test_notification_tool()
    print("✅ Async tool tests completed")


def run_tests():
    """Run all tests"""
    print("🧪 Starting Agent Framework Tests...")
    
    # Run sync tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run async tests
    asyncio.run(run_async_tests())
    
    print("🎉 All tests completed!")


if __name__ == "__main__":
    run_tests()
