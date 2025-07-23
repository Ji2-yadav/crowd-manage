#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from src.api.main import app
from src.core.agent_framework import GeminiAgentFramework
from src.simulator.crowd_simulator import CrowdSimulator

# Load environment variables
load_dotenv()

def main():
    """Main entry point for the application"""
    print("🚀 Starting Crowd Management Agentic AI System...")
    # Check for required environment variables
    required_env_vars = ["GEMINI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file or environment configuration.")
        return
    
    # Start the FastAPI server
    import uvicorn
    
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("🤖 AI agents are ready for crowd management tasks")
    print("🎭 Crowd simulator is running")
    
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        log_level="info"
    )
main()
# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("\n👋 Shutting down Crowd Management System...")
#     except Exception as e:
#         print(f"❌ Error starting application: {e}")
#         sys.exit(1)
