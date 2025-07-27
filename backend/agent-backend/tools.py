import requests
from typing import List, Dict, Any

# --- Constants ---
API_BASE_URL = 'https://simulator-backend-880917788492.us-central1.run.app'  # Update this to match your backend URL

# --- Helper Functions ---
def _get_state() -> dict:
    """Fetches the complete simulation state from the backend."""
    try:
        response = requests.get(f'{API_BASE_URL}/state')
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise Exception(f"Error fetching state from backend: {str(e)}")

def _post_action(endpoint: str, data: dict) -> dict:
    """Posts an action to the backend and returns the response."""
    try:
        response = requests.post(f'{API_BASE_URL}{endpoint}', json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise Exception(f"Error posting to {endpoint}: {str(e)}")

# --- Information Retrieval Tools ---

def get_zone_summary(zone_id: str) -> str:
    """Gets a summary of the specified zone's status."""
    state = _get_state()
    zone_data = state.get('zones', {}).get(zone_id)
    
    if not zone_data:
        return f"Error: Zone '{zone_id}' not found. Use tool 'list_all_zones' to get a list of available zones."
    
    # Build comprehensive summary
    summary_parts = [
        f"Zone: {zone_id}",
        f"Area: {zone_data.get('area_sqm', 'N/A')} sqm",
        f"People: {zone_data.get('num_people', 'N/A')}",
        f"Density: {zone_data.get('density_sqm_per_person', 'N/A')} sqm/person",
        f"Bottleneck Risk: {zone_data.get('bottleneck_risk', 'N/A')}"
    ]
    
    active_alerts = zone_data.get('active_alerts', [])
    if active_alerts:
        summary_parts.append(f"Active Alerts: {', '.join(active_alerts)}")
    else:
        summary_parts.append("No active alerts")
    
    return "\n".join(summary_parts)

def get_personnel_status(zone_id: str, unit_type: str = 'all') -> str:
    """Finds available personnel in a specific zone. unit_type can be 'medical', 'security', or 'all'."""
    state = _get_state()
    personnel = state.get('personnel', {})
    available_units = []
    
    for unit_id, details in personnel.items():
        if details.get('status') == 'available' and details.get('current_zone') == zone_id:
            if unit_type == 'all' or details.get('type') == unit_type:
                available_units.append(f"- {unit_id} ({details.get('name', 'N/A')}, {details.get('type')})")
                
    if not available_units:
        return f"No available '{unit_type}' units found in {zone_id}."
        
    return f"Available units in {zone_id}:\n" + "\n".join(available_units)

def list_all_zones() -> List[str]:
    """Returns a list of all available zone IDs."""
    state = _get_state()
    return list(state.get('zones', {}).keys())

def get_personnel_by_zone(zone_id: str) -> List[Dict[str, Any]]:
    """Gets a structured list of all personnel in a specific zone, including their ID, name, type, and status."""
    state = _get_state()
    personnel_in_zone = []
    
    for unit_id, details in state.get('personnel', {}).items():
        if details.get('current_zone') == zone_id:
            personnel_in_zone.append({
                "id": unit_id,
                "name": details.get("name"),
                "type": details.get("type"),
                "status": details.get("status")
            })
    
    return personnel_in_zone
    
def list_gates_in_zone(zone_id: str) -> List[Dict[str, Any]]:
    """Gets a structured list of all gates in a specific zone, including their ID and status."""
    state = _get_state()
    gates_in_zone = []
    
    for gate_id, details in state.get('gates', {}).items():
        if details.get('zone_id') == zone_id:
            gates_in_zone.append({
                "id": gate_id,
                "status": details.get("status"),
                "type": details.get("type")
            })
    
    return gates_in_zone

# --- Action & State Change Tools ---

def dispatch_unit(personnel_id: str, destination_details: str) -> str:
    """Dispatches a unit to a location and updates their status.
    Auto-resolves MedicalEmergency alerts if dispatching medical unit.
    Auto-resolves SecurityThreat alerts if dispatching security unit."""
    
    # First check the unit type to know which alerts to resolve
    state = _get_state()
    unit = state.get('personnel', {}).get(personnel_id)
    
    if not unit:
        return f"Error: Personnel '{personnel_id}' not found."
    
    # Make the dispatch request
    response = _post_action('/actions/dispatch-unit', {
        'personnel_id': personnel_id,
        'destination_details': destination_details
    })
    
    if response.get('status') == 'success':
        unit_type = unit.get('type')
        unit_name = unit.get('name', personnel_id)
        
        # Alert resolution is handled by the backend based on unit type
        if unit_type == 'medical':
            return f"Success: Medical unit {personnel_id} ({unit_name}) dispatched to '{destination_details}'. Medical emergencies in the area will be resolved."
        elif unit_type == 'security':
            return f"Success: Security unit {personnel_id} ({unit_name}) dispatched to '{destination_details}'. Security threats in the area will be resolved."
        else:
            return f"Success: Unit {personnel_id} ({unit_name}) dispatched to '{destination_details}'."
    else:
        return response.get('message', 'Unknown error occurred')

def make_announcement(zone_id: str, message: str) -> str:
    """Makes a public announcement in a specific zone."""
    response = _post_action('/actions/make-announcement', {
        'zone_id': zone_id,
        'message': message
    })
    
    if response.get('status') == 'success':
        return f"Announcement successfully made in {zone_id}: \"{message}\""
    else:
        return response.get('message', 'Unknown error occurred')

def toggle_gate(gate_id: str, status: str) -> str:
    """Sets a gate's status to 'open' or 'closed'."""
    if status not in ['open', 'closed']:
        return f"Error: Invalid status '{status}'. Use 'open' or 'closed'."
    
    response = _post_action('/actions/toggle-gate', {
        'gate_id': gate_id,
        'status': status
    })
    
    if response.get('status') == 'success':
        return f"Success: Gate {gate_id} has been set to '{status}'."
    else:
        return response.get('message', 'Unknown error occurred')

def evacuate_zone(zone_id: str) -> str:
    """Initiates a full evacuation protocol for a specified zone or the entire venue.
    Opens all fire and emergency exits in the target zone(s).
    Fire alerts auto-resolve after evacuation completes."""
    
    response = _post_action('/actions/evacuate', {
        'zone_id': zone_id
    })
    
    if response.get('status') == 'success':
        if zone_id == 'all':
            return "Success: Full venue evacuation protocol initiated. All emergency exits are opening. Fire alerts will be resolved upon completion."
        else:
            return f"Success: Evacuation protocol initiated for zone {zone_id}. Emergency exits are opening. Fire alerts will be resolved upon completion."
    else:
        return response.get('message', 'Unknown error occurred')

def activate_crowd_control_protocol(zone_id: str) -> str:
    """Triggers crowd control measures to mitigate dangerous overcrowding or stampede.
    Auto-resolves Overcrowding and Stampede alerts.
    Opens non-main gates and reduces zone density by dispersing people."""
    
    response = _post_action('/actions/activate-crowd-control-protocol', {
        'zone_id': zone_id
    })
    
    if response.get('status') == 'success':
        return f"Success: Crowd control protocol activated for zone {zone_id}. Non-main gates are opening to disperse crowds. Overcrowding and stampede alerts will be resolved."
    else:
        return response.get('message', 'Unknown error occurred')

def dispatch_fire_brigade(zone_id: str) -> str:
    """Dispatches fire brigade units to a specified zone.
    Typically used for fire emergencies or situations requiring specialized fire response."""
    
    response = _post_action('/actions/dispatch-fire-brigade', {
        'zone_id': zone_id
    })
    
    if response.get('status') == 'success':
        return f"Success: Fire brigade units dispatched to zone {zone_id}. Fire response team is en route."
    else:
        return response.get('message', 'Unknown error occurred')

# --- Legacy Map Function (kept for compatibility) ---
def get_map(zone_id: str) -> str:
    """Returns a pre-written ASCII map of a zone."""
    maps = {
        "hall_1_lower": (
            "--- Hall 1 (Lower) ---\n"
            "| E1--[Stage]--E2 |\n"
            "|      -||-        |\n"
            "| [F&B]    [Med]   |\n"
            "--------------------"
        ),
        "outdoor_plaza": (
            "--- Outdoor Plaza ---\n"
            "  [Reg]    [Smoking]\n"
            "    |          |\n"
            "---(G1 Main Entrance)---\n"
            "         |           \n"
            "     To Hall 1"
        )
    }
    return maps.get(zone_id, f"No map available for {zone_id}.")

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    print("--- Testing Tools ---")
    
    # Info Retrieval
    print("\n1. Getting Zone Summary:")
    print(get_zone_summary('hall_1_lower'))
    
    print("\n2. Getting Personnel Status:")
    print(get_personnel_status('hall_1_lower', 'medical'))
    
    print("\n3. Listing All Zones:")
    print(list_all_zones())
    
    print("\n--- Testing Complete ---")