from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
from collections import deque
import requests
from google.genai import types
from gemini_helpers import call_google_llm_with_tools, parse_function_call, extract_text_response
from tools import (
    get_zone_summary,
    get_personnel_status,
    get_map,
    dispatch_unit,
    make_announcement,
    toggle_gate,
    list_all_zones,
    get_personnel_by_zone,
    list_gates_in_zone,
    evacuate_zone,
    activate_crowd_control_protocol,
    dispatch_fire_brigade
)

app = Flask(__name__)
CORS(app)

# Tool mapping from function name to actual function
TOOL_FUNCTIONS = {
    "get_zone_summary": get_zone_summary,
    "get_personnel_status": get_personnel_status,
    "get_map": get_map,
    "dispatch_unit": dispatch_unit,
    "make_announcement": make_announcement,
    "toggle_gate": toggle_gate,
    "list_all_zones": list_all_zones,
    "get_personnel_by_zone": get_personnel_by_zone,
    "list_gates_in_zone": list_gates_in_zone,
    "evacuate_zone": evacuate_zone,
    "activate_crowd_control_protocol": activate_crowd_control_protocol,
    "dispatch_fire_brigade": dispatch_fire_brigade
}

# Store conversation sessions
sessions = {}

# Response queues for streaming
response_queues = {}

# Alert queues for each session
alert_queues = {}

# Track most recent session for alerts
most_recent_session = None

def setup_tool_declarations():
    """Set up the function declarations for the tool calling API."""
    return [
        types.FunctionDeclaration(
            name="get_zone_summary",
            description="Get a summary of the specified zone's crowd density and risk status.",
            parameters={
                "type": "object",
                "properties": {
                    "zone_id": {
                        "type": "string",
                        "description": "Zone identifier (e.g., 'hall_1_lower', 'outdoor_plaza')",
                    }
                },
                "required": ["zone_id"],
            },
        ),
        types.FunctionDeclaration(
            name="get_personnel_status",
            description="Find available personnel in a specific zone, optionally filtered by unit type.",
            parameters={
                "type": "object",
                "properties": {
                    "zone_id": {
                        "type": "string",
                        "description": "Zone identifier to check for personnel",
                    },
                    "unit_type": {
                        "type": "string",
                        "description": "Type of personnel to filter ('medical', 'security', or 'all')",
                        "enum": ["medical", "security", "all"],
                        "default": "all"
                    }
                },
                "required": ["zone_id"],
            },
        ),
        types.FunctionDeclaration(
            name="get_map",
            description="Get an ASCII map visualization of a specific zone.",
            parameters={
                "type": "object",
                "properties": {
                    "zone_id": {
                        "type": "string",
                        "description": "Zone identifier for which to retrieve the map",
                    }
                },
                "required": ["zone_id"],
            },
        ),
        types.FunctionDeclaration(
            name="dispatch_unit",
            description="Dispatch an available personnel unit to a specific location and update their status. Auto-resolves MedicalEmergency alerts if dispatching medical unit. Auto-resolves SecurityThreat alerts if dispatching security unit.",
            parameters={
                "type": "object",
                "properties": {
                    "personnel_id": {
                        "type": "string",
                        "description": "Personnel unit identifier (e.g., 'med_01', 'sec_02')",
                    },
                    "destination_details": {
                        "type": "string",
                        "description": "Description of the destination location",
                    }
                },
                "required": ["personnel_id", "destination_details"],
            },
        ),
        types.FunctionDeclaration(
            name="make_announcement",
            description="Make a public announcement in a specific zone.",
            parameters={
                "type": "object",
                "properties": {
                    "zone_id": {
                        "type": "string",
                        "description": "Zone identifier where the announcement should be made",
                    },
                    "message": {
                        "type": "string",
                        "description": "The announcement message to broadcast",
                    }
                },
                "required": ["zone_id", "message"],
            },
        ),
        types.FunctionDeclaration(
            name="toggle_gate",
            description="Set a gate's status to open or closed for crowd control.",
            parameters={
                "type": "object",
                "properties": {
                    "gate_id": {
                        "type": "string",
                        "description": "Gate identifier (e.g., 'g1_main', 'g2_conference_link')",
                    },
                    "status": {
                        "type": "string",
                        "description": "New status for the gate",
                        "enum": ["open", "closed"]
                    }
                },
                "required": ["gate_id", "status"],
            },
        ),
        types.FunctionDeclaration(
            name="list_all_zones",
            description="Returns a list of all available zone IDs in the venue.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.FunctionDeclaration(
            name="get_personnel_by_zone",
            description="Gets a structured list of all personnel in a specific zone, including their ID, name, type, and status.",
            parameters={
                "type": "object",
                "properties": {
                    "zone_id": {
                        "type": "string",
                        "description": "Zone identifier to check for personnel",
                    }
                },
                "required": ["zone_id"],
            },
        ),
        types.FunctionDeclaration(
            name="list_gates_in_zone",
            description="Gets a structured list of all gates in a specific zone, including their ID and status.",
            parameters={
                "type": "object",
                "properties": {
                    "zone_id": {
                        "type": "string",
                        "description": "Zone identifier to check for gates",
                    }
                },
                "required": ["zone_id"],
            },
        ),
        types.FunctionDeclaration(
            name="evacuate_zone",
            description="Initiates a full evacuation protocol for a specified zone or the entire venue. Opens all fire and emergency exits. Fire alerts auto-resolve after evacuation completes.",
            parameters={
                "type": "object",
                "properties": {
                    "zone_id": {
                        "type": "string",
                        "description": "Zone identifier to evacuate, or 'all' for full venue evacuation",
                    }
                },
                "required": ["zone_id"],
            },
        ),
        types.FunctionDeclaration(
            name="activate_crowd_control_protocol",
            description="Triggers crowd control measures to mitigate dangerous overcrowding or stampede. Auto-resolves Overcrowding and Stampede alerts. Opens non-main gates and reduces zone density by dispersing people.",
            parameters={
                "type": "object",
                "properties": {
                    "zone_id": {
                        "type": "string",
                        "description": "Zone identifier where crowd control is needed",
                    }
                },
                "required": ["zone_id"],
            },
        ),
        types.FunctionDeclaration(
            name="dispatch_fire_brigade",
            description="Dispatches fire brigade units to a specified zone. Typically used for fire emergencies or situations requiring specialized fire response.",
            parameters={
                "type": "object",
                "properties": {
                    "zone_id": {
                        "type": "string",
                        "description": "Zone identifier where fire brigade is needed",
                    }
                },
                "required": ["zone_id"],
            },
        ),
    ]

def get_system_prompt():
    return """
You are **Project Drishti**, an AI-powered situational awareness platform for large-scale event safety. Your primary mission is to act as a proactive central nervous system for the event's command center, providing actionable intelligence and executing commands to ensure attendee safety.

You are interacting with a human commander. Your communication must be professional, concise, and direct. Omit conversational fillers.

---

### Primary Directive & Default Behavior

Your primary directive is to **maintain event safety and stability**.

---

### Core Heuristics & Behavior

1.  **Discover Before Acting**: If you need an ID (`zone_id`, `gate_id`, `personnel_id`) that is not explicitly mentioned, you **must** first use a discovery tool (`list_all_zones`, `get_personnel_by_zone`, `list_gates_in_zone`) to find the correct ID. Do not guess.

2.  **Proactive Incident Response Flow**: When a critical alert is found, you **must act immediately**. Do not wait for the commander's instruction. Follow this sequence: **Detect** -> **Analyze** -> **Plan** -> **Execute** -> **Report**.
    * **Resource Rule**: When planning, you must dispatch the **correct type** of unit for the incident (e.g., 'medical' for a medical emergency). If the correct type is not available in the immediate zone, you **must** expand your search to adjacent zones before dispatching an incorrect unit type as a last resort.
    * **Access Rule**: When analyzing a bottleneck or access issue, you **must** check for closed gates in the zone using `list_gates_in_zone` that could be opened to improve flow.
    * **Critical Response Rule**: 
        - For Fire alerts: Use `evacuate_zone` immediately
        - For Stampede or Overcrowding alerts: Use `activate_crowd_control_protocol` immediately
        - For MedicalEmergency: Dispatch medical personnel
        - For SecurityThreat: Dispatch security personnel

3.  **Synthesize, Don't Dump**: Do not output raw data from your tools. Synthesize the information into a brief, human-readable summary.

4.  **Confirm All Actions**: After executing an action (`dispatch_unit`, `toggle_gate`, `make_announcement`), always state the outcome of that action clearly.

---

### Behavioral Guidelines
- Summarize the actions taken to the commander - when you do take actions. You must state the situation that was taking place and justify your actions. Don't sound robotic. Be precise.
- When you message the commander - you must sound natural. 
- If you make annoucements - don't repeat it exactly to the commander.
- If you get the zone ID wrong or the response suggests that the zone does not exist, use the tool which can list all zones that will give you the list of zone IDs available.
- NEVER ask the user to use a tool. The tools are available only to you and you must not explicitly state your tool names to the user.
- Match the langugage of the user.
- In case of fire, you must evacuate and also call the fire brigade.
- Whenever you use crowd control protocol, you must also make an appropriate announcement.
- Even if the user talks in another language, you must make the tool calls in English and the tool responses will also be in English. You must respond to the user in the language that the user is using.
"""

def execute_function_call(function_call):
    """Execute a function call and return the result."""
    function_name = function_call.name
    
    # Parse arguments
    args = {}
    if hasattr(function_call, 'args') and function_call.args:
        args = dict(function_call.args)
    
    # Execute the function
    if function_name in TOOL_FUNCTIONS:
        try:
            result = TOOL_FUNCTIONS[function_name](**args)
            return {
                "result": str(result),
                "function_name": function_name,
                "args": args
            }
        except Exception as e:
            return {
                "error": f"Error executing {function_name}: {str(e)}",
                "function_name": function_name,
                "args": args
            }
    else:
        return {
            "error": f"Unknown function: {function_name}",
            "function_name": function_name
        }

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from the web UI."""
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    user_message = data.get('message', '')
    
    # Initialize session and queue if needed
    if session_id not in sessions:
        sessions[session_id] = {
            'messages': [],
            'tools': types.Tool(function_declarations=setup_tool_declarations())
        }
    if session_id not in response_queues:
        response_queues[session_id] = deque()
    if session_id not in alert_queues:
        alert_queues[session_id] = deque()
    
    # Track this as most recent session
    global most_recent_session
    most_recent_session = session_id
    
    session = sessions[session_id]
    queue = response_queues[session_id]
    
    # Add user message
    session['messages'].append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)]
    ))
    
    # Clear queue for new conversation
    queue.clear()
    
    # Start processing in background thread
    def process_async():
        try:
            response = call_google_llm_with_tools(
                request_id=None,
                model="gemini-2.5-flash",
                messages=session['messages'],
                sp=get_system_prompt(),
                tools=[session['tools']],
                user_id=None
            )
            
            # Handle function calls
            max_function_calls = 15
            function_call_count = 0
            first_text_sent = False
            
            while function_call_count < max_function_calls:
                has_function_call, function_call = parse_function_call(response)
                
                if has_function_call:
                    # Extract any text before the function call
                    text_response = extract_text_response(response)
                    if text_response and not first_text_sent:
                        # Send initial text immediately
                        queue.append({
                            'type': 'text',
                            'content': text_response
                        })
                        first_text_sent = True
                    
                    function_call_count += 1
                    
                    # Add assistant's response to messages
                    if response.candidates and response.candidates[0].content:
                        session['messages'].append(response.candidates[0].content)
                    
                    # Execute function and send to queue immediately
                    function_result = execute_function_call(function_call)
                    queue.append({
                        'type': 'function_call',
                        'content': function_result
                    })
                    
                    # Create function response
                    function_response_part = types.Part.from_function_response(
                        name=function_call.name,
                        response={"result": function_result.get("result", function_result.get("error", "Unknown error"))}
                    )
                    
                    session['messages'].append(types.Content(
                        role="user",
                        parts=[function_response_part]
                    ))
                    
                    # Get next response
                    response = call_google_llm_with_tools(
                        request_id=None,
                        model="gemini-2.5-flash",
                        messages=session['messages'],
                        sp=get_system_prompt(),
                        tools=[session['tools']],
                        user_id=None
                    )
                else:
                    # No more function calls
                    text = extract_text_response(response)
                    if text:
                        queue.append({
                            'type': 'text',
                            'content': text
                        })
                        session['messages'].append(types.Content(
                            role="model",
                            parts=[types.Part.from_text(text=text)]
                        ))
                    break
            
            # Mark end of response
            queue.append({'type': 'end'})
            
        except Exception as e:
            queue.append({
                'type': 'error',
                'content': str(e)
            })
    
    # Start processing thread
    thread = threading.Thread(target=process_async)
    thread.daemon = True
    thread.start()
    
    # Return immediately with session info
    return jsonify({
        'status': 'processing',
        'session_id': session_id
    })

@app.route('/reset', methods=['POST'])
def reset_session():
    """Reset a conversation session."""
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    
    if session_id in sessions:
        del sessions[session_id]
    
    return jsonify({'status': 'success'})

@app.route('/poll', methods=['POST'])
def poll_queue():
    """Poll for new items in the response queue."""
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    
    if session_id not in response_queues:
        return jsonify({'items': [], 'complete': True})
    
    queue = response_queues[session_id]
    items = []
    complete = False
    
    # Get up to 10 items from queue
    for _ in range(10):
        if queue:
            item = queue.popleft()
            if item['type'] == 'end':
                complete = True
                break
            items.append(item)
        else:
            break
    
    return jsonify({
        'items': items,
        'complete': complete
    })

@app.route('/poll-alerts', methods=['POST'])
def poll_alerts():
    """Poll for new alerts."""
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    
    if session_id not in alert_queues:
        return jsonify({'alerts': []})
    
    alert_queue = alert_queues[session_id]
    alerts = []
    
    # Get all pending alerts
    while alert_queue:
        alerts.append(alert_queue.popleft())
    
    return jsonify({'alerts': alerts})

@app.route('/alert', methods=['POST'])
def receive_alert():
    """Receive alert from mock server and process it."""
    data = request.get_json()
    alert_type = data.get('type')
    zone_id = data.get('zone')
    
    # Get the most recent session or create a default one
    session_id = most_recent_session if most_recent_session else 'default'
    
    # Initialize alert queue if needed
    if session_id not in alert_queues:
        alert_queues[session_id] = deque()
    
    # Add alert notification to alert queue for frontend to display immediately
    alert_queues[session_id].append({
        'type': alert_type,
        'zone': zone_id,
        'message': f"I see a {alert_type.replace('Emergency', ' emergency').lower()} in zone {zone_id}. I need to take action."
    })
    
    # Create alert message for the agent
    alert_message = f"<alert>{alert_type} in zone {zone_id}</alert>"
    
    # Call our own chat endpoint to process the alert
    chat_data = {
        'session_id': session_id,
        'message': alert_message
    }
    
    # Make internal request to chat endpoint
    try:
        import os
        port = int(os.environ.get('PORT', 5001))
        response = requests.post(f'https://agent-backend-880917788492.us-central1.run.app/chat', json=chat_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    print("\n" + "="*50)
    print("Project Drishti Conversation API")
    print("="*50)
    print(f"Server starting on http://localhost:{port}")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)