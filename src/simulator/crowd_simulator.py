import asyncio
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from ..models.schemas import LocationStatus, CrowdData, Alert


class CrowdSimulator:
    """Simulates crowd movements and provides data for agent testing"""
    
    def __init__(self):
        self.locations = {
            "main_entrance": {"name": "Main Entrance", "max_capacity": 500, "current": 150},
            "west_gate": {"name": "West Gate", "max_capacity": 300, "current": 120},
            "east_gate": {"name": "East Gate", "max_capacity": 300, "current": 80},
            "north_exit": {"name": "North Exit", "max_capacity": 200, "current": 45},
            "south_exit": {"name": "South Exit", "max_capacity": 200, "current": 30},
            "central_plaza": {"name": "Central Plaza", "max_capacity": 1000, "current": 450},
            "food_court": {"name": "Food Court", "max_capacity": 400, "current": 220},
            "stage_area": {"name": "Stage Area", "max_capacity": 800, "current": 600},
        }
        
        self.connections = {
            "main_entrance": ["central_plaza"],
            "west_gate": ["central_plaza", "food_court"],
            "east_gate": ["central_plaza", "stage_area"],
            "central_plaza": ["main_entrance", "west_gate", "east_gate", "food_court", "stage_area"],
            "food_court": ["west_gate", "central_plaza", "south_exit"],
            "stage_area": ["east_gate", "central_plaza", "north_exit"],
            "north_exit": ["stage_area"],
            "south_exit": ["food_court"],
        }
        
        self.running = False
        self.simulation_speed = 1.0  # seconds per update
        self.initialized = True  # Add initialization flag
    
    async def start_simulation(self):
        """Start the crowd simulation"""
        self.running = True
        print("🎭 Starting crowd simulation...")
        
        while self.running:
            await self._update_crowd_positions()
            await asyncio.sleep(self.simulation_speed)
    
    def stop_simulation(self):
        """Stop the crowd simulation"""
        self.running = False
        print("⏹️ Crowd simulation stopped.")
    
    async def _update_crowd_positions(self):
        """Update crowd positions based on movement patterns"""
        for location_id in self.locations:
            location = self.locations[location_id]
            
            # Simulate crowd flow
            flow_change = random.randint(-20, 25)
            
            # Apply some realistic constraints
            if location["current"] + flow_change < 0:
                flow_change = -location["current"]
            elif location["current"] + flow_change > location["max_capacity"]:
                flow_change = location["max_capacity"] - location["current"]
            
            location["current"] = max(0, location["current"] + flow_change)
            
            # Generate alerts for high density
            density = location["current"] / location["max_capacity"]
            if density > 0.8:
                await self._generate_alert(location_id, "high", f"High crowd density at {location['name']}")
            elif density > 0.9:
                await self._generate_alert(location_id, "critical", f"Critical crowd density at {location['name']}")
    
    async def _generate_alert(self, location_id: str, severity: str, message: str):
        """Generate an alert for crowd management"""
        print(f"⚠️ [{severity.upper()}] {message}")
    
    async def get_location_data(self, location_id: str) -> Dict[str, Any]:
        """Get current data for a specific location"""
        if location_id not in self.locations:
            return {"error": f"Location {location_id} not found"}
        
        location = self.locations[location_id]
        density = location["current"] / location["max_capacity"]
        
        return {
            "location_id": location_id,
            "name": location["name"],
            "current_count": location["current"],
            "max_capacity": location["max_capacity"],
            "density": density,
            "flow_rate": random.uniform(-10, 15),  # Simulated flow rate
            "status": self._get_density_status(density),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_density_status(self, density: float) -> str:
        """Get density status string"""
        if density < 0.3:
            return "low"
        elif density < 0.6:
            return "medium"
        elif density < 0.8:
            return "high"
        else:
            return "critical"
    
    async def get_all_locations_status(self) -> List[Dict[str, Any]]:
        """Get status for all locations"""
        status_list = []
        for location_id in self.locations:
            status = await self.get_location_data(location_id)
            if "error" not in status:  # Only include valid locations
                status_list.append(status)
        
        # Ensure we always return some data
        if not status_list:
            # Return default demo data if no valid locations
            status_list = [
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
                }
            ]
        
        return status_list

    async def simulate_incident(self, location_id: str, incident_type: str):
        """Simulate an incident at a specific location"""
        if location_id not in self.locations:
            return {"error": f"Location {location_id} not found"}
        
        location = self.locations[location_id]
        
        if incident_type == "stampede_risk":
            # Increase crowd suddenly
            increase = min(100, location["max_capacity"] - location["current"])
            location["current"] += increase
            await self._generate_alert(location_id, "critical", f"Stampede risk detected at {location['name']}")
        
        elif incident_type == "blocked_exit":
            # Simulate blocked exit (increases crowd in connected areas)
            for connected_location in self.connections.get(location_id, []):
                if connected_location in self.locations:
                    self.locations[connected_location]["current"] = min(
                        self.locations[connected_location]["max_capacity"],
                        self.locations[connected_location]["current"] + 50
                    )
            await self._generate_alert(location_id, "high", f"Exit blocked at {location['name']}")
        
        return {
            "incident_type": incident_type,
            "location_id": location_id,
            "status": "simulated",
            "timestamp": datetime.now().isoformat()
        }
    
    async def apply_action(self, location_id: str, action_type: str, parameters: Dict = None):
        """Apply a crowd management action in the simulation"""
        if location_id not in self.locations:
            return {"error": f"Location {location_id} not found"}
        
        location = self.locations[location_id]
        parameters = parameters or {}
        
        if action_type == "halt_crowd":
            # Reduce crowd flow into this location
            reduction = min(50, location["current"])
            location["current"] -= reduction
            print(f"🛑 Crowd halted at {location['name']}, reduced by {reduction}")
        
        elif action_type == "place_barrier":
            # Redirect crowd flow
            barrier_count = parameters.get("barrier_count", 1)
            reduction = min(30 * barrier_count, location["current"])
            location["current"] -= reduction
            print(f"🚧 {barrier_count} barriers placed at {location['name']}, crowd reduced by {reduction}")
        
        elif action_type == "deploy_staff":
            # Improve crowd flow efficiency
            staff_count = parameters.get("staff_count", 2)
            if location["current"] > location["max_capacity"] * 0.7:
                reduction = min(20 * staff_count, location["current"])
                location["current"] -= reduction
                print(f"👮 {staff_count} staff deployed at {location['name']}, crowd managed better")
        
        return {
            "action_type": action_type,
            "location_id": location_id,
            "parameters": parameters,
            "status": "applied",
            "timestamp": datetime.now().isoformat()
        }
