from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import requests
import threading
import time

app = Flask(__name__)
CORS(app)

# Mock state
state = {
    "zones": {
        "hall_1_lower": {
            "area_sqm": 5000,
            "num_people": 4900,
            "density_sqm_per_person": 1.02,
            "bottleneck_risk": "critical",
            "active_alerts": []
        },
        "hall_1_upper": {
            "area_sqm": 3000,
            "num_people": 2100,
            "density_sqm_per_person": 1.43,
            "bottleneck_risk": "high",
            "active_alerts": []
        },
        "hall_2": {
            "area_sqm": 4000,
            "num_people": 2800,
            "density_sqm_per_person": 1.43,
            "bottleneck_risk": "medium",
            "active_alerts": []
        },
        "entrance_lobby": {
            "area_sqm": 1500,
            "num_people": 800,
            "density_sqm_per_person": 1.88,
            "bottleneck_risk": "high",
            "active_alerts": []
        },
        "food_court": {
            "area_sqm": 2000,
            "num_people": 600,
            "density_sqm_per_person": 3.33,
            "bottleneck_risk": "low",
            "active_alerts": []
        }
    },
    "personnel": {
        "med_01": {
            "name": "Priya Singh",
            "type": "medical",
            "status": "available",
            "current_zone": "hall_1_lower"
        },
        "med_02": {
            "name": "Raj Kumar",
            "type": "medical",
            "status": "available",
            "current_zone": "hall_2"
        },
        "sec_01": {
            "name": "Amit Verma",
            "type": "security",
            "status": "dispatched",
            "current_zone": "entrance_lobby"
        },
        "sec_02": {
            "name": "Neha Patel",
            "type": "security",
            "status": "available",
            "current_zone": "food_court"
        }
    },
    "gates": {
        "main_entrance": {
            "zone_id": "entrance_lobby",
            "status": "open",
            "type": "main_gate"
        },
        "e1_fire_exit": {
            "zone_id": "hall_1_lower",
            "status": "closed",
            "type": "fire_exit"
        },
        "e2_emergency_exit": {
            "zone_id": "hall_1_upper",
            "status": "closed",
            "type": "emergency_exit"
        },
        "e3_service_exit": {
            "zone_id": "hall_2",
            "status": "closed",
            "type": "service_exit"
        }
    }
}

def log_request(method, path, body=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] {method} {path}")
    if body:
        print(f"Body: {json.dumps(body, indent=2)}")
    print("-" * 50)

def remove_alert_from_zone(zone_id, alert_type):
    """Helper function to remove an alert from a zone."""
    if zone_id in state['zones'] and alert_type in state['zones'][zone_id]['active_alerts']:
        state['zones'][zone_id]['active_alerts'].remove(alert_type)
        print(f"Resolved {alert_type} alert in {zone_id}")
        return True
    return False

def gradual_evacuate_zone(zone_id):
    """Gradually reduce people count to 0 over 10 seconds."""
    if zone_id not in state['zones']:
        return
    
    initial_count = state['zones'][zone_id]['num_people']
    steps = 20  # 20 updates over 10 seconds
    
    for i in range(steps):
        current_count = state['zones'][zone_id]['num_people']
        # Reduce by 5% of initial count each step
        reduction = int(initial_count * 0.05)
        new_count = max(0, current_count - reduction)
        
        state['zones'][zone_id]['num_people'] = new_count
        if new_count > 0:
            state['zones'][zone_id]['density_sqm_per_person'] = (
                state['zones'][zone_id]['area_sqm'] / new_count
            )
        else:
            state['zones'][zone_id]['density_sqm_per_person'] = 0
        
        print(f"Evacuating {zone_id}: {current_count} -> {new_count}")
        time.sleep(0.5)
    
    # Ensure it's 0 at the end
    state['zones'][zone_id]['num_people'] = 0
    state['zones'][zone_id]['density_sqm_per_person'] = 0
    
    # Set risk to low when zone is empty
    state['zones'][zone_id]['bottleneck_risk'] = 'low'
    
    # Resolve Fire alerts after evacuation
    remove_alert_from_zone(zone_id, 'Fire')
    print(f"Evacuation of {zone_id} complete - risk set to low")

def gradual_overcrowd_zone(zone_id, event_type):
    """Gradually increase people count to 3000 over 5 seconds."""
    if zone_id not in state['zones']:
        return
    
    initial_count = state['zones'][zone_id]['num_people']
    target_count = 3000
    
    steps = 10  # 10 updates over 5 seconds
    
    # Calculate change per step (can be increase or decrease)
    if initial_count != target_count:
        change_per_step = (target_count - initial_count) // steps
    else:
        # Already at target
        return
    
    for i in range(steps):
        current_count = state['zones'][zone_id]['num_people']
        if change_per_step > 0:
            new_count = min(target_count, current_count + change_per_step)
        else:
            new_count = max(target_count, current_count + change_per_step)
        
        state['zones'][zone_id]['num_people'] = new_count
        state['zones'][zone_id]['density_sqm_per_person'] = (
            state['zones'][zone_id]['area_sqm'] / new_count
        )
        
        print(f"Overcrowding {zone_id}: {current_count} -> {new_count}")
        time.sleep(0.5)
    
    # Ensure we reach the target
    state['zones'][zone_id]['num_people'] = target_count
    state['zones'][zone_id]['density_sqm_per_person'] = (
        state['zones'][zone_id]['area_sqm'] / target_count
    )
    
    final_density = state['zones'][zone_id]['density_sqm_per_person']
    print(f"Overcrowding of {zone_id} complete: {initial_count} -> {target_count} people (density: {final_density:.2f} m²/person)")
    
    # Send alert to conversation API after overcrowding completes
    try:
        alert_response = requests.post('https://agent-backend-880917788492.us-central1.run.app/alert', json={
            'type': event_type,
            'zone': zone_id
        })
        print(f"Alert sent to conversation API: {alert_response.status_code}")
    except Exception as e:
        print(f"Failed to send alert to conversation API: {e}")

def gradual_crowd_control(zone_id):
    """Gradually reduce people count to 500 over 10 seconds."""
    if zone_id not in state['zones']:
        return
    
    initial_count = state['zones'][zone_id]['num_people']
    target_count = 500
    steps = 20  # 20 updates over 10 seconds
    
    # Calculate reduction per step
    if initial_count > target_count:
        reduction_per_step = (initial_count - target_count) // steps
    else:
        # If already below 500, no need to reduce
        return
    
    for i in range(steps):
        current_count = state['zones'][zone_id]['num_people']
        new_count = max(target_count, current_count - reduction_per_step)
        
        state['zones'][zone_id]['num_people'] = new_count
        state['zones'][zone_id]['density_sqm_per_person'] = (
            state['zones'][zone_id]['area_sqm'] / new_count
        )
        
        print(f"Crowd control in {zone_id}: {current_count} -> {new_count}")
        time.sleep(0.5)
    
    # Ensure we reach exactly 500
    state['zones'][zone_id]['num_people'] = target_count
    state['zones'][zone_id]['density_sqm_per_person'] = (
        state['zones'][zone_id]['area_sqm'] / target_count
    )
    
    # Update risk level to low when crowd is controlled
    state['zones'][zone_id]['bottleneck_risk'] = 'low'
    
    # Resolve Overcrowding and Stampede alerts
    remove_alert_from_zone(zone_id, 'Overcrowding')
    remove_alert_from_zone(zone_id, 'Stampede')
    
    final_density = state['zones'][zone_id]['density_sqm_per_person']
    print(f"Crowd control in {zone_id} complete: {initial_count} -> {target_count} people (density: {final_density:.2f} m²/person)")

def get_zone_for_destination(destination_details):
    """Extract zone from destination details string."""
    # Simple heuristic - check if any zone name appears in the destination
    for zone_id in state['zones'].keys():
        if zone_id.lower() in destination_details.lower():
            return zone_id
    # Check for zone names in the destination
    zone_keywords = {
        'hall 1': 'hall_1_lower',
        'hall 2': 'hall_2',
        'entrance': 'entrance_lobby',
        'food': 'food_court',
        'lobby': 'entrance_lobby'
    }
    for keyword, zone in zone_keywords.items():
        if keyword in destination_details.lower():
            return zone
    return None

@app.route('/state', methods=['GET'])
def get_state():
    log_request('GET', '/state')
    return jsonify(state)

@app.route('/event', methods=['POST'])
def trigger_event():
    data = request.get_json()
    log_request('POST', '/event', data)
    
    event_type = data.get('type')
    zone = data.get('zone')
    
    # Validate zone
    if zone not in state['zones']:
        return jsonify({
            "status": "error",
            "message": "Invalid zone_id provided."
        }), 400
    
    # Validate event type
    valid_types = ["Overcrowding", "MedicalEmergency", "Fire", "SecurityThreat", "Stampede"]
    if event_type not in valid_types:
        return jsonify({
            "status": "error",
            "message": "Invalid event type provided."
        }), 400
    
    # Add alert to zone
    if event_type not in state['zones'][zone]['active_alerts']:
        state['zones'][zone]['active_alerts'].append(event_type)
        print(f"Added {event_type} alert to {zone}")
    
    # Simulate state changes based on event type
    if event_type == "Fire":
        # Open fire exits in affected zone
        for gate_id, gate in state['gates'].items():
            if gate['zone_id'] == zone and gate['type'] in ['fire_exit', 'emergency_exit']:
                state['gates'][gate_id]['status'] = 'open'
                print(f"Opened gate {gate_id}")
    
    if event_type in ["Overcrowding", "Stampede"]:
        state['zones'][zone]['bottleneck_risk'] = 'critical'
        print(f"Set {zone} risk to critical")
        
        # For Overcrowding, start gradual population increase
        if event_type == "Overcrowding":
            print(f"Starting overcrowding simulation for {zone}")
            thread = threading.Thread(target=gradual_overcrowd_zone, args=(zone, event_type))
            thread.daemon = True
            thread.start()
    
    # Send alert to conversation API (except for Overcrowding which sends after 5s)
    if event_type != "Overcrowding":
        try:
            alert_response = requests.post('/alert', json={
                'type': event_type,
                'zone': zone
            })
            print(f"Alert sent to conversation API: {alert_response.status_code}")
        except Exception as e:
            print(f"Failed to send alert to conversation API: {e}")
    
    return jsonify({
        "status": "success",
        "message": f"{event_type} event triggered in {zone}"
    })

@app.route('/actions/toggle-gate', methods=['POST'])
def toggle_gate():
    data = request.get_json()
    log_request('POST', '/actions/toggle-gate', data)
    
    gate_id = data.get('gate_id')
    status = data.get('status')
    
    if gate_id not in state['gates']:
        return jsonify({
            "status": "error",
            "message": "Invalid gate_id provided."
        }), 400
    
    state['gates'][gate_id]['status'] = status
    print(f"Set gate {gate_id} to {status}")
    
    return jsonify({
        "status": "success",
        "message": f"Gate {gate_id} has been set to {status}"
    })

@app.route('/actions/dispatch-unit', methods=['POST'])
def dispatch_unit():
    data = request.get_json()
    log_request('POST', '/actions/dispatch-unit', data)
    
    personnel_id = data.get('personnel_id')
    destination = data.get('destination_details')
    
    if personnel_id not in state['personnel']:
        return jsonify({
            "status": "error",
            "message": "Invalid personnel_id provided."
        }), 400
    
    # Get unit details
    unit = state['personnel'][personnel_id]
    unit_type = unit.get('type')
    
    # Update unit status
    state['personnel'][personnel_id]['status'] = 'dispatched'
    print(f"Dispatched {personnel_id} to {destination}")
    
    # Resolve alerts based on unit type and destination
    destination_zone = get_zone_for_destination(destination)
    if destination_zone:
        # Medical units resolve MedicalEmergency alerts
        if unit_type == 'medical':
            remove_alert_from_zone(destination_zone, 'MedicalEmergency')
        # Security units resolve SecurityThreat alerts
        elif unit_type == 'security':
            remove_alert_from_zone(destination_zone, 'SecurityThreat')
    
    return jsonify({
        "status": "success",
        "message": f"Unit {personnel_id} dispatched successfully"
    })

@app.route('/actions/make-announcement', methods=['POST'])
def make_announcement():
    data = request.get_json()
    log_request('POST', '/actions/make-announcement', data)
    
    zone_id = data.get('zone_id')
    message = data.get('message')
    
    print(f"Announcement for {zone_id}: {message}")
    
    return jsonify({
        "status": "success",
        "message": f"Announcement for {zone_id} acknowledged"
    })

@app.route('/actions/evacuate', methods=['POST'])
def evacuate():
    data = request.get_json()
    log_request('POST', '/actions/evacuate', data)
    
    zone_id = data.get('zone_id')
    
    if zone_id != 'all' and zone_id not in state['zones']:
        return jsonify({
            "status": "error",
            "message": "Invalid zone_id provided."
        }), 400
    
    # Open all emergency exits
    for gate_id, gate in state['gates'].items():
        if zone_id == 'all' or gate['zone_id'] == zone_id:
            if gate['type'] != 'main_gate':
                state['gates'][gate_id]['status'] = 'open'
                print(f"Opened gate {gate_id}")
    
    # Start gradual evacuation in background threads
    if zone_id == 'all':
        for zone in state['zones']:
            print(f"Starting evacuation of {zone}")
            thread = threading.Thread(target=gradual_evacuate_zone, args=(zone,))
            thread.daemon = True
            thread.start()
    else:
        print(f"Starting evacuation of {zone_id}")
        thread = threading.Thread(target=gradual_evacuate_zone, args=(zone_id,))
        thread.daemon = True
        thread.start()
    
    return jsonify({
        "status": "success",
        "message": f"Evacuation protocol initiated for zone_id: {zone_id}"
    })

@app.route('/actions/activate-crowd-control-protocol', methods=['POST'])
def activate_crowd_control():
    data = request.get_json()
    log_request('POST', '/actions/activate-crowd-control-protocol', data)
    
    zone_id = data.get('zone_id')
    
    if zone_id not in state['zones']:
        return jsonify({
            "status": "error",
            "message": "Invalid zone_id provided."
        }), 400
    
    # Open non-main gates in zone
    for gate_id, gate in state['gates'].items():
        if gate['zone_id'] == zone_id and gate['type'] != 'main_gate':
            state['gates'][gate_id]['status'] = 'open'
            print(f"Opened gate {gate_id}")
    
    # Start gradual crowd reduction in background thread
    print(f"Starting crowd control protocol for {zone_id}")
    thread = threading.Thread(target=gradual_crowd_control, args=(zone_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "success",
        "message": f"Crowd control protocol activated for zone_id: {zone_id}"
    })

@app.route('/actions/dispatch-fire-brigade', methods=['POST'])
def dispatch_fire_brigade():
    data = request.get_json()
    log_request('POST', '/actions/dispatch-fire-brigade', data)
    
    zone_id = data.get('zone_id')
    
    if zone_id not in state['zones']:
        return jsonify({
            "status": "error",
            "message": "Invalid zone_id provided."
        }), 400
    
    # Log fire brigade dispatch
    print(f"Fire brigade dispatched to {zone_id}")
    
    # Open fire and emergency exits in the zone
    for gate_id, gate in state['gates'].items():
        if gate['zone_id'] == zone_id and gate['type'] in ['fire_exit', 'emergency_exit']:
            state['gates'][gate_id]['status'] = 'open'
            print(f"Opened gate {gate_id}")
    
    # Fire alerts will be resolved after evacuation if needed
    # The fire brigade arrival doesn't immediately resolve the alert
    # as the situation needs to be assessed and handled
    
    return jsonify({
        "status": "success",
        "message": f"Fire brigade dispatched to zone_id: {zone_id}"
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Project Drishti Mock Server")
    print("="*50)
    print("Server starting on http://localhost:3001")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=3001, debug=True)