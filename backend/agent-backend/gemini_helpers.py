import time
from google import genai
from google.genai import types
from google.genai.types import HttpOptions
import os
from dotenv import load_dotenv
import uuid
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

# Check if database logging is enabled
USE_DB_LOGGING = os.environ.get("USE_DB_LOGGING", "false").lower() == "true"

# Conditionally import and initialize database components
db_manager = None
llm_logger = None

if USE_DB_LOGGING:
    try:
        from db.llm_logger import LLMCallLogger
        from db.trigger_manager import DatabaseConnectionManager
        
        uuid_val = uuid.uuid4()
        db_manager = DatabaseConnectionManager(max_connections=4 * 2)
        llm_logger = LLMCallLogger(db_manager, f'memory_{uuid_val}')
        print("Database logging enabled")
    except Exception as e:
        print(f"Warning: Could not initialize database logging: {e}")
        USE_DB_LOGGING = False
else:
    print("Database logging disabled")

api_key = os.environ.get("GEMINI_API_KEY")


if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is required")

GEMINI_TIMEOUT = 20 * 1000  # 20 seconds
google_client = genai.Client(api_key=api_key, http_options=HttpOptions(timeout=GEMINI_TIMEOUT))
model = "gemini-2.5-flash"

def call_google_llm(model, messages, system_prompt, user_id=None, conversation_date=None, delay_seconds=0, response_format={"type": "text"}):
    try:
        """Call Google LLM using the specified API format."""
        # Apply rate limiting
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0,
            thinking_config=genai.types.ThinkingConfig(
                thinking_budget=4096
            ),
            response_mime_type="text/plain",
            system_instruction=[
                types.Part.from_text(text=system_prompt)])
        
        # Record start time for API call timing
        start_time = time.time()
        
        try:
            response = google_client.models.generate_content(
                model=model,
                contents=messages,
                config=generate_content_config)
        except Exception as api_error:
            # Handle 429 rate limit errors with 1-hour sleep
            if "429" in str(api_error) or "rate limit" in str(api_error).lower():
                print(f"🚨 Rate limit (429) encountered. Sleeping for 1 hour...")
                time.sleep(3600)  # Sleep for 1 hour (3600 seconds)
            raise api_error
        
        # Calculate processing time in milliseconds
        processing_time_ms = int((time.time() - start_time) * 1000)
        print(f"Processing time: {processing_time_ms} ms")
        
        # Log to database if enabled (will work even with disable_db=True if logger exists)
        user_prompt = messages[0].text if messages else ""
        parsed_operations = None
        
        # Extract token counts and finish reason
        input_tokens = 0
        output_tokens = 0
        finish_reason = None
        
        if hasattr(response, 'usage_metadata'):
            usage_dict = response.to_json_dict().get('usage_metadata', {})
            input_tokens = usage_dict.get('prompt_token_count', 0)
            output_tokens = usage_dict.get('candidates_token_count', 0) + usage_dict.get('thoughts_token_count', 0)

        if hasattr(response, 'candidates') and response.candidates:
            finish_reason = getattr(response.candidates[0], 'finish_reason', None)
        
        # Log to database if enabled
        if USE_DB_LOGGING and llm_logger:
            llm_logger.log_llm_call(
                user_id=user_id,
                conversation_date=conversation_date,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                llm_response=response.text,
                response_status='success',
                processing_time_ms=processing_time_ms,
                parsed_operations=parsed_operations,
                operation_counts=None,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                finish_reason=str(finish_reason)[:50] if finish_reason else None
            )
    
        return response.text
    except Exception as e:
        import traceback
        print(f"Error calling Google LLM: {e}", traceback.format_exc())
        return None

def extract_text_response(response: Any) -> Optional[str]:
    """Extract text response from LLM response."""
    try:
        if (response.candidates and 
            response.candidates[0].content and 
            response.candidates[0].content.parts):
            
            text_parts = []
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            
            if text_parts:
                return " ".join(text_parts)
        return None
    except Exception as e:
        # logger.error(f"Error extracting text response: {e}", send_on_slack=True)
        return None


def parse_function_call(response: Any) -> tuple[bool, Optional[Any]]:
    """Parse function call from LLM response."""
    try:
        if (response.candidates and 
            response.candidates[0].content and 
            response.candidates[0].content.parts):
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    return True, part.function_call
        return False, None
    except Exception as e:
        print(f"Error parsing function call: {e}")
        return False, None
    

def call_google_llm_with_tools(request_id, model, messages, sp, tools=None, user_id=None, max_retries=3):
    """Call Google LLM with optional tools and return full response object (for tool calling)"""
    config_params = {
        'temperature': 0.2,
        'thinking_config': genai.types.ThinkingConfig(thinking_budget=4096),
        'response_mime_type': "text/plain",
        'system_instruction': [types.Part.from_text(text=sp)]
    }
    
    if tools:
        config_params['tools'] = tools
    
    generate_content_config = types.GenerateContentConfig(**config_params)
    
    for attempt in range(max_retries):
        try:
            # logger.info(f"[DEBUG] GEMINI API CALL WITH TOOLS - Request ID: {request_id}, Attempt: {attempt + 1}")
            start_time = time.time()
            response = None
            response = google_client.models.generate_content(
                model=model,
                contents=messages,
                config=generate_content_config
            )
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"Processing time: {processing_time_ms} ms") 
            
            if response is None or response.candidates[0].content.parts is None:
                # logger.warning(f"Empty response from LLM (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    # logger.info(f"Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception("Failed to get response from LLM after all retries")

            if hasattr(response, 'usage_metadata'):
                usage_dict = response.to_json_dict().get('usage_metadata', {})
                input_tokens = usage_dict.get('prompt_token_count', 0)
                output_tokens = usage_dict.get('candidates_token_count', 0) + usage_dict.get('thoughts_token_count', 0)

            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = getattr(response.candidates[0], 'finish_reason', None)
            
            # Log successful response
            # logger.info(f"LLM call successful on attempt {attempt + 1}")
            
            # Add database logging for successful response if enabled
            if USE_DB_LOGGING and llm_logger:
                llm_logger.log_llm_call(
                    user_id=user_id,
                    conversation_date=None,
                    model=model,
                    system_prompt=sp,
                    user_prompt=str(messages),
                    llm_response=str(response),
                    response_status='success',
                    processing_time_ms=0,
                    parsed_operations=0,
                    operation_counts=None,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    finish_reason=str(finish_reason)[:50] if finish_reason else None
                )
            return response
            
        except Exception as e:
            print('somethin went wrong', e)
            if USE_DB_LOGGING and llm_logger:
                llm_logger.log_llm_call(
                    user_id=user_id,
                    conversation_date=None,
                    model=model,
                    system_prompt=sp,
                    user_prompt=str(messages),
                    llm_response=str(response),
                    response_status='error',
                    processing_time_ms=0,
                    parsed_operations=0,
                    operation_counts=None,
                    error_message=str(e)[:500],
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    finish_reason=str(finish_reason)[:50] if finish_reason else None
                )
            # logger.error(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # logger.info("Retrying...")
                time.sleep(1)
            else:
                # logger.error("All attempts failed. Giving up.", send_on_slack=True)
                raise
    
    # This should never be reached due to the raise in the loop
    raise Exception("Unexpected error in call_google_llm_with_tools")
    
if __name__ == "__main__":
    def _setup_tool_declarations():
        """Set up the function declarations for the tool calling API."""
        return [
            types.FunctionDeclaration(
                name="get_all_clinics",
                description="Get all available clinics in the system.",
                parameters={"type": "object", "properties": {}},
            ),
            types.FunctionDeclaration(
                name="get_clinics_by_user_location",
                description="Get clinics near a user's location.",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_location": {
                            "type": "string",
                            "description": "User's location (city, area, or location name)",
                        }
                    },
                    "required": ["user_location"],
                },
            ),
            types.FunctionDeclaration(
                name="get_clinics_by_user_pincode",
                description="Get clinics near a user's pincode.",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_pincode": {
                            "type": "string",
                            "description": "User's 6-digit pincode",
                            "pattern": "^[0-9]{6}$",
                        }
                    },
                    "required": ["user_pincode"],
                },
            ),
            types.FunctionDeclaration(
                name="recommend_appointment_slots",
                description="Get intelligent slot recommendations for a specific clinic and date with fallback options.",
                parameters={
                    "type": "object",
                    "properties": {
                        "clinic_name": {
                            "type": "string",
                            "description": "Name of the clinic",
                        },
                        "date": {
                            "type": "string",
                            "description": "Date in DD-MM-YYYY format",
                            "pattern": "^\\d{2}-\\d{2}-\\d{4}$",
                        },
                        "time": {
                            "type": "string",
                            "description": "Optional preferred time in HH:MM format (24-hour)",
                            "pattern": "^\\d{2}:\\d{2}$",
                        },
                    },
                    "required": ["clinic_name", "date"],
                },
            ),
            types.FunctionDeclaration(
                name="get_doctors_at_clinic",
                description="Get all doctors/practitioners at a specific clinic.",
                parameters={
                    "type": "object",
                    "properties": {
                        "clinic_name": {
                            "type": "string",
                            "description": "Name of the clinic",
                        }
                    },
                    "required": ["clinic_name"],
                },
            ),
            types.FunctionDeclaration(
                name="book_appointment",
                description="Book an appointment using clinic name, date, time, and practitioner name.",
                parameters={
                    "type": "object",
                    "properties": {
                        "clinic_name": {
                            "type": "string",
                            "description": "Name of the clinic",
                        },
                        "date": {
                            "type": "string",
                            "description": "Appointment date in DD-MM-YYYY format",
                            "pattern": "^\\d{2}-\\d{2}-\\d{4}$",
                        },
                        "time": {
                            "type": "string",
                            "description": "Appointment time in HH:MM format",
                            "pattern": "^\\d{2}:\\d{2}$",
                        },
                        "practitioner_name": {
                            "type": "string",
                            "description": "Name of the doctor/practitioner",
                        }
                    },
                    "required": ["clinic_name", "date", "time", "practitioner_name"],
                },
            ),
            types.FunctionDeclaration(
                name="search_doctor_by_name_and_city",
                description="Search for a specific doctor by name in a particular city.",
                parameters={
                    "type": "object",
                    "properties": {
                        "doctor_name": {
                            "type": "string",
                            "description": "Name of the doctor to search for",
                        },
                        "city": {
                            "type": "string",
                            "description": "City where to search for the doctor",
                        }
                    },
                    "required": ["doctor_name", "city"],
                },
            ),
        ]

    tools = types.Tool(function_declarations=_setup_tool_declarations())
    tools = [tools]
    # print(tools)
    # response = call_google_llm(
    #         model, 
    #         [types.Part.from_text(text='what clinics you ahve')], 
    #         system_prompt='you are bot', 
    #         conversation_date='2025-07-17',
    #     )
    # response = call_google_llm(
    #         model, 
    #         [types.Part.from_text(text='what clinics you ahve')], 
    #         system_prompt='you are bot', 
    #         conversation_date='2025-07-17',
    #     )
    response = call_google_llm_with_tools(
        request_id=None,
        model=model,
        messages=[types.Part.from_text(text='what clinics you ahve')],
        sp='you are bot',
        tools=tools,
        user_id=None
    )
    print(response)