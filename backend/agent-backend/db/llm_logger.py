import psycopg2
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class LLMCallLogger:
    """Logger for LLM API calls to PostgreSQL database."""
    
    def __init__(self, db_manager=None, session_id: Optional[str] = None):
        self.db_manager = db_manager
        self.db_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password'),
            'database': os.getenv('POSTGRES_DB', 'llm_logs')
        }
        self.session_id = str(uuid.uuid4()) if not session_id else session_id
        # print(f"LLM Logger initialized with session ID: {self.session_id}")
    
    def log_llm_call(self,
                     user_id: str,
                     conversation_date: str,
                     model: str,
                     system_prompt: str,
                     user_prompt: str,
                     llm_response: str,
                     response_status: str = 'success',
                     processing_time_ms: Optional[int] = None,
                     parsed_operations: Optional[List[Dict]] = None,
                     operation_counts: Optional[Dict] = None,
                     error_message: Optional[str] = None,
                     input_tokens: Optional[int] = None,
                     output_tokens: Optional[int] = None,
                     finish_reason: Optional[str] = None) -> bool:
        """Log an LLM API call to the database."""
        
        try:
            # Use database connection manager if available, otherwise fall back to direct connection
            if self.db_manager:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    insert_sql = """
                    INSERT INTO llm_call_logs (
                        user_id, conversation_date, model, system_prompt, user_prompt,
                        llm_response, response_status, processing_time_ms, parsed_operations,
                        operation_counts, error_message, session_id, input_tokens, output_tokens, finish_reason
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """
                    
                    # Convert date string to date object
                    conv_date = None
                    if conversation_date:
                        conv_date = datetime.strptime(conversation_date, '%Y-%m-%d').date()
                    
                    
                    # Convert lists/dicts to JSON
                    parsed_ops_json = json.dumps(parsed_operations) if parsed_operations else None
                    op_counts_json = json.dumps(operation_counts) if operation_counts else None
                    
                    cursor.execute(insert_sql, (
                        user_id,
                        conv_date,
                        model,
                        system_prompt,
                        user_prompt,
                        llm_response,
                        response_status,
                        processing_time_ms,
                        parsed_ops_json,
                        op_counts_json,
                        error_message,
                        self.session_id,
                        input_tokens,
                        output_tokens,
                        finish_reason
                    ))
                    
                    log_id = cursor.fetchone()[0]
                    conn.commit()
                    cursor.close()
                    
                    # print(f"LLM call logged with ID: {log_id}")
                    return True
            else:
                # Fall back to direct connection
                conn = psycopg2.connect(**self.db_params)
                cursor = conn.cursor()
                
                insert_sql = """
                INSERT INTO llm_call_logs (
                    user_id, conversation_date, model, system_prompt, user_prompt,
                    llm_response, response_status, processing_time_ms, parsed_operations,
                    operation_counts, error_message, session_id, input_tokens, output_tokens, finish_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """
                
                # Convert date string to date object
                conv_date = datetime.strptime(conversation_date, '%Y-%m-%d').date()
                
                # Convert lists/dicts to JSON
                parsed_ops_json = json.dumps(parsed_operations) if parsed_operations else None
                op_counts_json = json.dumps(operation_counts) if operation_counts else None
                
                cursor.execute(insert_sql, (
                    user_id,
                    conv_date,
                    model,
                    system_prompt,
                    str(user_prompt),
                    llm_response,
                    response_status,
                    processing_time_ms,
                    parsed_ops_json,
                    op_counts_json,
                    str(error_message),
                    self.session_id,
                    input_tokens,
                    output_tokens,
                    finish_reason
                ))
                
                log_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                conn.close()
                
                # print(f"LLM call logged with ID: {log_id}")
                return True
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            # print(f"Error logging LLM call: {e}")
            return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session."""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            stats_sql = """
            SELECT 
                COUNT(*) as total_calls,
                COUNT(CASE WHEN response_status = 'success' THEN 1 END) as successful_calls,
                COUNT(CASE WHEN response_status = 'error' THEN 1 END) as failed_calls,
                AVG(processing_time_ms) as avg_processing_time_ms,
                MIN(timestamp) as session_start,
                MAX(timestamp) as session_end
            FROM llm_call_logs 
            WHERE session_id = %s;
            """
            
            cursor.execute(stats_sql, (self.session_id,))
            result = cursor.fetchone()
            
            if result:
                stats = {
                    'session_id': self.session_id,
                    'total_calls': result[0],
                    'successful_calls': result[1],
                    'failed_calls': result[2],
                    'avg_processing_time_ms': float(result[3]) if result[3] else 0,
                    'session_start': result[4].isoformat() if result[4] else None,
                    'session_end': result[5].isoformat() if result[5] else None
                }
            else:
                stats = {
                    'session_id': self.session_id,
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'avg_processing_time_ms': 0,
                    'session_start': None,
                    'session_end': None
                }
            
            cursor.close()
            conn.close()
            return stats
            
        except Exception as e:
            print(f"Error getting session stats: {e}")
            return {'error': str(e)}

    def check_if_processed(self, user_id: str, conversation_date: str) -> bool:
        """Check if a user_id and conversation_date combination has already been processed."""
        try:
            # Use database connection manager if available
            if self.db_manager:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Convert date string to date object
                    conv_date = datetime.strptime(conversation_date, '%Y-%m-%d').date()
                    
                    check_sql = """
                    SELECT EXISTS(
                        SELECT 1 FROM llm_call_logs 
                        WHERE user_id = %s 
                        AND conversation_date = %s
                        AND response_status = 'success'
                    );
                    """
                    
                    cursor.execute(check_sql, (user_id, conv_date))
                    result = cursor.fetchone()[0]
                    cursor.close()
                    
                    return result
            else:
                # Fall back to direct connection
                conn = psycopg2.connect(**self.db_params)
                cursor = conn.cursor()
                
                # Convert date string to date object
                conv_date = datetime.strptime(conversation_date, '%Y-%m-%d').date()
                
                check_sql = """
                SELECT EXISTS(
                    SELECT 1 FROM llm_call_logs 
                    WHERE user_id = %s 
                    AND conversation_date = %s
                    AND response_status = 'success'
                );
                """
                
                cursor.execute(check_sql, (user_id, conv_date))
                result = cursor.fetchone()[0]
                
                cursor.close()
                conn.close()
                
                return result
                
        except Exception as e:
            print(f"Error checking if processed: {e}")
            # In case of error, return False to allow processing
            return False
    
    
    def query_logs(self, 
                   user_id: Optional[str] = None,
                   date_from: Optional[str] = None,
                   date_to: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Query LLM call logs with optional filters."""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            where_conditions = []
            params = []
            
            if user_id:
                where_conditions.append("user_id = %s")
                params.append(user_id)
            
            if date_from:
                where_conditions.append("conversation_date >= %s")
                params.append(datetime.strptime(date_from, '%Y-%m-%d').date())
            
            if date_to:
                where_conditions.append("conversation_date <= %s")
                params.append(datetime.strptime(date_to, '%Y-%m-%d').date())
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            query_sql = f"""
            SELECT
                id, timestamp, user_id, conversation_date, model,
                system_prompt, user_prompt, llm_response, response_status,
                processing_time_ms, parsed_operations, operation_counts,
                error_message, session_id, input_tokens, output_tokens, finish_reason
            FROM llm_call_logs
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT %s;
            """
            
            params.append(limit)
            cursor.execute(query_sql, params)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                log_entry = dict(zip(columns, row))
                # Convert timestamp to ISO string
                if log_entry['timestamp']:
                    log_entry['timestamp'] = log_entry['timestamp'].isoformat()
                # Convert date to string
                if log_entry['conversation_date']:
                    log_entry['conversation_date'] = log_entry['conversation_date'].isoformat()
                # Parse JSON fields
                if log_entry['parsed_operations'] and isinstance(log_entry['parsed_operations'], str):
                    log_entry['parsed_operations'] = json.loads(log_entry['parsed_operations'])
                if log_entry['operation_counts'] and isinstance(log_entry['operation_counts'], str):
                    log_entry['operation_counts'] = json.loads(log_entry['operation_counts'])
                
                results.append(log_entry)
            
            cursor.close()
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error querying logs: {e}")
            return []

# Example usage and testing
if __name__ == "__main__":
    logger = LLMCallLogger()
    
    # Test logging
    test_success = logger.log_llm_call(
        user_id="test_user_123",
        conversation_date="2025-06-04",
        model="gemini-2.5-flash",
        system_prompt="You are a helpful assistant.",
        user_prompt="Hello, how are you?",
        llm_response="I'm doing well, thank you!",
        response_status="success",
        processing_time_ms=1500,
        parsed_operations=[{"operation": "CREATE", "topic": "test"}],
        operation_counts={"CREATE": 1, "UPDATE": 0, "DELETE": 0}
    )
    
    if test_success:
        print("Test log entry created successfully!")
        
        # Get session stats
        stats = logger.get_session_stats()
        print(f"Session stats: {stats}")
        
        # Query logs
        logs = logger.query_logs(limit=5)
        print(f"Found {len(logs)} log entries")
    else:
        print("Test log entry failed!")
