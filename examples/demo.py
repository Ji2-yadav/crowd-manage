#!/usr/bin/env python3

"""
Example usage script for the Crowd Management Agentic AI System
This script demonstrates how to use the various agents and tools programmatically.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.agent_framework import GeminiAgentFramework
from src.agents.specialized_agents import (
    MovementPredictionAgent, ActionAgent, LostAndFoundAgent, SummarizationAgent
)
from src.tools.base_tools import CrowdAnalysisTool, NotificationTool, ActionRecommendationTool, CameraSearchTool
from src.simulator.crowd_simulator import CrowdSimulator

# Load environment variables
load_dotenv()

async def setup_system():
    """Initialize the complete agentic AI system"""
    print("🚀 Setting up Crowd Management AI System...")
    
    # Initialize framework
    framework = GeminiAgentFramework()
    simulator = CrowdSimulator()
    
    # Register tools
    print("🔧 Registering tools...")
    framework.register_tool(CrowdAnalysisTool())
    framework.register_tool(NotificationTool())
    framework.register_tool(ActionRecommendationTool())
    framework.register_tool(CameraSearchTool())
    
    # Register agents
    print("🤖 Registering agents...")
    framework.register_agent(MovementPredictionAgent())
    framework.register_agent(ActionAgent())
    framework.register_agent(LostAndFoundAgent())
    framework.register_agent(SummarizationAgent())
    
    return framework, simulator

async def demonstrate_movement_prediction(framework):
    """Demonstrate movement prediction agent capabilities"""
    print("\n" + "="*60)
    print("📊 DEMONSTRATING MOVEMENT PREDICTION AGENT")
    print("="*60)
    
    agent = framework.agents["movement_prediction_agent"]
    
    # Analyze a high-traffic location
    result = await agent.analyze_location("central_plaza")
    
    print("🔍 Analysis Result:")
    print(f"Response: {result['agent_response']}")
    
    if result.get('tool_results'):
        print("\n🛠️ Tool Results:")
        for tool_result in result['tool_results']:
            print(f"  - {tool_result['tool_name']}: {tool_result['result']}")

async def demonstrate_action_agent(framework):
    """Demonstrate action agent capabilities"""
    print("\n" + "="*60)
    print("⚡ DEMONSTRATING ACTION AGENT")
    print("="*60)
    
    agent = framework.agents["action_agent"]
    
    # Generate action plan for high density scenario
    result = await agent.generate_action_plan(
        location_id="stage_area",
        situation="High crowd density detected with potential stampede risk",
        severity="high"
    )
    
    print("🎯 Action Plan:")
    print(f"Response: {result['agent_response']}")
    
    if result.get('tool_results'):
        print("\n🛠️ Tool Results:")
        for tool_result in result['tool_results']:
            print(f"  - {tool_result['tool_name']}: {tool_result['result']}")

async def demonstrate_lost_and_found(framework):
    """Demonstrate lost and found agent capabilities"""
    print("\n" + "="*60)
    print("🔍 DEMONSTRATING LOST AND FOUND AGENT")
    print("="*60)
    
    agent = framework.agents["lost_and_found_agent"]
    
    # Search for a missing person
    result = await agent.search_person(
        person_description="Adult male, approximately 30 years old, wearing red shirt and blue jeans, carrying black backpack",
        last_seen_location="west_gate"
    )
    
    print("👤 Search Result:")
    print(f"Response: {result['agent_response']}")
    
    if result.get('tool_results'):
        print("\n🛠️ Tool Results:")
        for tool_result in result['tool_results']:
            print(f"  - {tool_result['tool_name']}: {tool_result['result']}")

async def demonstrate_summarization(framework):
    """Demonstrate summarization agent capabilities"""
    print("\n" + "="*60)
    print("📋 DEMONSTRATING SUMMARIZATION AGENT")
    print("="*60)
    
    agent = framework.agents["summarization_agent"]
    
    # Generate zone summary
    result = await agent.generate_zone_summary(
        zone_name="West Zone",
        query="Provide a comprehensive security assessment including crowd density, potential risks, and recommendations"
    )
    
    print("📊 Zone Summary:")
    print(f"Response: {result['agent_response']}")
    
    if result.get('tool_results'):
        print("\n🛠️ Tool Results:")
        for tool_result in result['tool_results']:
            print(f"  - {tool_result['tool_name']}: {tool_result['result']}")

async def demonstrate_simulation(simulator):
    """Demonstrate simulation capabilities"""
    print("\n" + "="*60)
    print("🎭 DEMONSTRATING CROWD SIMULATION")
    print("="*60)
    
    # Get current status
    print("📊 Current Location Status:")
    locations = await simulator.get_all_locations_status()
    for location in locations[:4]:  # Show first 4 locations
        density_pct = int(location['density'] * 100)
        print(f"  • {location['name']}: {location['current_count']}/{location['max_capacity']} ({density_pct}% - {location['status']})")
    
    # Simulate an incident
    print("\n🚨 Simulating stampede risk at Central Plaza...")
    incident_result = await simulator.simulate_incident("central_plaza", "stampede_risk")
    print(f"Incident Status: {incident_result['status']}")
    
    # Apply crowd management action
    print("\n🛑 Applying crowd management action...")
    action_result = await simulator.apply_action("central_plaza", "halt_crowd")
    print(f"Action Status: {action_result['status']}")

async def demonstrate_agent_collaboration(framework):
    """Demonstrate how agents can work together"""
    print("\n" + "="*60)
    print("🤝 DEMONSTRATING AGENT COLLABORATION")
    print("="*60)
    
    # Step 1: Movement agent detects issue
    print("1️⃣ Movement agent analyzing situation...")
    movement_agent = framework.agents["movement_prediction_agent"]
    analysis = await movement_agent.analyze_location("food_court")
    print(f"   Analysis: {analysis['agent_response'][:100]}...")
    
    # Step 2: Action agent generates plan based on analysis
    print("\n2️⃣ Action agent creating response plan...")
    action_agent = framework.agents["action_agent"]
    action_plan = await action_agent.generate_action_plan(
        location_id="food_court",
        situation="Crowd congestion detected in analysis",
        severity="medium"
    )
    print(f"   Action Plan: {action_plan['agent_response'][:100]}...")
    
    # Step 3: Summarization agent provides executive summary
    print("\n3️⃣ Summarization agent generating executive summary...")
    summary_agent = framework.agents["summarization_agent"]
    summary = await summary_agent.generate_zone_summary(
        zone_name="Food Court Area",
        query="Summarize current situation and response actions"
    )
    print(f"   Summary: {summary['agent_response'][:100]}...")

async def main():
    """Main demonstration function"""
    print("🎬 Starting Crowd Management AI Demonstration")
    print("============================================")
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: GEMINI_API_KEY not found in environment")
        print("📝 Some agent demonstrations may use mock responses")
        print("💡 Set your GEMINI_API_KEY in .env file for full functionality")
    
    try:
        # Setup system
        framework, simulator = await setup_system()
        
        # Run demonstrations
        await demonstrate_simulation(simulator)
        await demonstrate_movement_prediction(framework)
        await demonstrate_action_agent(framework)
        await demonstrate_lost_and_found(framework)
        await demonstrate_summarization(framework)
        await demonstrate_agent_collaboration(framework)
        
        print("\n" + "="*60)
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("🚀 To start the web interface, run: python main.py")
        print("📚 Check README.md for more usage examples")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        print("💡 Make sure you have set up your environment correctly")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Demonstration interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
