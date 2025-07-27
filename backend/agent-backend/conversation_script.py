#!/usr/bin/env python3
"""
Conversation script using Gemini with tool calling capabilities.
Uses functions from tools.py for actual tool execution.
"""

import sys
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
    activate_crowd_control_protocol
)

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
    "activate_crowd_control_protocol": activate_crowd_control_protocol
}

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
            description="Dispatch an available personnel unit to a specific location and update their status.",
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
    ]

def execute_function_call(function_call):
    """Execute a function call and return the result."""
    function_name = function_call.name
    
    # Parse arguments
    args = {}
    if hasattr(function_call, 'args') and function_call.args:
        args = dict(function_call.args)
    
    print(f"\n🔧 Executing tool: {function_name}")
    print(f"   Arguments: {args}")
    
    # Execute the function
    if function_name in TOOL_FUNCTIONS:
        try:
            result = TOOL_FUNCTIONS[function_name](**args)
            print(f"   Result: {result}")
            return {"result": str(result)}
        except Exception as e:
            error_msg = f"Error executing {function_name}: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {"error": error_msg}
    else:
        error_msg = f"Unknown function: {function_name}"
        print(f"   ❌ {error_msg}")
        return {"error": error_msg}
    
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

---

### Tool Definitions & Usage

#### Discovery Tools
* **`list_all_zones()`**
    * **Purpose**: To get a list of all official `zone_id`s for the event.
    * **When to Use**: Call this to know what zones exist or to resolve an ambiguous zone name from a user command.

* **`get_personnel_by_zone(zone_id: str)`**
    * **Purpose**: To get a structured list of all personnel within a specific zone.
    * **When to Use**: Call this when you need to know who is in a specific area or need to find a `personnel_id` to dispatch.

* **`list_gates_in_zone(zone_id: str)`**
    * **Purpose**: To get a structured list of all gates in a specific zone, including their ID and status.
    * **When to Use**: Use this to identify relevant gates to open or close when managing crowd flow or incident access.

#### Information Retrieval Tools
* **`get_zone_summary(zone_id: str)`**
    * **Purpose**: To get a human-readable summary of a zone's current conditions, including crowd density and bottleneck risk.
    * **When to Use**: Use this as your primary tool to assess the situation in any given zone.

* **`get_personnel_status(zone_id: str, unit_type: str)`**
    * **Purpose**: To get a quick, pre-formatted string of *available* personnel in a zone.
    * **When to Use**: For a quick check. For dispatch planning, `get_personnel_by_zone` is superior.

* **`get_map(zone_id: str)`**
    * **Purpose**: To display a simple ASCII map of a zone.
    * **When to Use**: Only when a commander explicitly asks for a map or visual layout.

#### Action Tools
* **`toggle_gate(gate_id: str, status: str)`**
    * **Purpose**: To open or close a specific gate. The `status` must be `'open'` or `'closed'`.
    * **When to Use**: To manage crowd flow, such as opening an alternative exit to ease congestion or closing an entrance during a security incident.

* **`dispatch_unit(personnel_id: str, destination_details: str)`**
    * **Purpose**: To send a specific unit to a location. Auto-resolves MedicalEmergency alerts if dispatching medical unit. Auto-resolves SecurityThreat alerts if dispatching security unit.
    * **When to Use**: To respond to medical emergencies or security incidents. You must have a valid `personnel_id`.

* **`make_announcement(zone_id: str, message: str)`**
    * **Purpose**: To broadcast a message over the public announcement system in a specific zone.
    * **When to Use**: To give instructions to the crowd, such as directing them to an alternative exit or advising them to clear an area.

* **`evacuate_zone(zone_id: str)`**
    * **Purpose**: To initiate a full evacuation protocol. Opens all fire and emergency exits. Fire alerts auto-resolve after evacuation.
    * **When to Use**: For critical situations like fire alerts or when immediate evacuation is necessary. Can evacuate a single zone or entire venue with zone_id='all'.

* **`activate_crowd_control_protocol(zone_id: str)`**
    * **Purpose**: To mitigate overcrowding or stampede risks. Auto-resolves Overcrowding and Stampede alerts. Opens non-main gates and disperses crowds to reduce density.
    * **When to Use**: When detecting dangerous crowd density, stampede risks, or overcrowding alerts. This is a step below full evacuation.
"""

def run_conversation():
    """Run the interactive conversation with tool calling."""
    # System prompt
    system_prompt = get_system_prompt()

    # Setup tools
    tools = types.Tool(function_declarations=setup_tool_declarations())
    
    # Initialize conversation
    messages = []
    max_function_calls = 15
    
    print("🎭 Event Venue Management Assistant")
    print("Type 'exit' to quit\n")
    
    while True:
        # Get user input
        user_input = input("\n👤 You: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\n👋 Goodbye!")
            break
        
        # Add user message to conversation
        messages.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_input)]
        ))
        
        try:
            # Call LLM with tools
            response = call_google_llm_with_tools(
                request_id=None,
                model="gemini-2.5-flash",
                messages=messages,
                sp=system_prompt,
                tools=[tools],
                user_id=None
            )
            
            # Process function calls in a loop
            function_call_count = 0
            final_response = None
            
            while function_call_count < max_function_calls:
                has_function_call, function_call = parse_function_call(response)
                
                if has_function_call:
                    # First, check if there's any text response to display before executing the function
                    text_response = extract_text_response(response)
                    if text_response:
                        print(f"\n🤖 Assistant: {text_response}")
                    
                    function_call_count += 1
                    
                    # Add the assistant's response (including function call) to messages
                    if response.candidates and response.candidates[0].content:
                        messages.append(response.candidates[0].content)
                    
                    # Execute function call
                    function_result = execute_function_call(function_call)
                    
                    # Create function response and add to messages
                    function_response_part = types.Part.from_function_response(
                        name=function_call.name,
                        response=function_result
                    )
                    
                    messages.append(types.Content(
                        role="user",
                        parts=[function_response_part]
                    ))
                    
                    # Get next response from LLM
                    response = call_google_llm_with_tools(
                        request_id=None,
                        model="gemini-2.5-flash",
                        messages=messages,
                        sp=system_prompt,
                        tools=[tools],
                        user_id=None
                    )
                    
                else:
                    # No more function calls - extract final text response
                    final_response = extract_text_response(response)
                    if not final_response:
                        # Try fallback to response.text
                        if hasattr(response, 'text') and response.text:
                            final_response = response.text
                        else:
                            final_response = "I'm sorry, I couldn't process your request properly. Please try again."
                    break
            
            # Handle max function calls reached
            if function_call_count >= max_function_calls:
                print(f"\n⚠️  Maximum function calls ({max_function_calls}) reached")
                final_response = "I'm having trouble completing your request."
                # Extract any text from the last response
                last_text = extract_text_response(response)
                if last_text:
                    final_response = last_text
                elif hasattr(response, 'text') and response.text:
                    final_response = response.text
            
            # Display final response
            if final_response:
                print(f"\n🤖 Assistant: {final_response}")
                
                # Add assistant's final response to messages
                messages.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=final_response)]
                ))
            
            print(f"\n[Completed with {function_call_count} function call(s)]")
                    
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # No need to check for data.json anymore since we're using the backend API
    print("🚀 Connecting to backend API...")
    
    run_conversation()