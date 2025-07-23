"""
Configuration module for the Crowd Management Agentic AI System
"""

import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import google.auth
from google.oauth2 import service_account
import structlog

logger = structlog.get_logger()


class GoogleCloudConfig(BaseModel):
    """Google Cloud configuration"""
    project_id: str = Field(default="", description="Google Cloud Project ID")
    region: str = Field(default="us-central1", description="Google Cloud region")
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    service_account_path: Optional[str] = Field(default=None, description="Path to service account JSON file")
    
    @validator('gemini_api_key', pre=True)
    def validate_api_key(cls, v):
        if not v:
            logger.warning("GEMINI_API_KEY not provided - some features may be limited")
        return v


class RedisConfig(BaseModel):
    """Redis configuration for pub/sub and caching"""
    url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    max_connections: int = Field(default=10, description="Maximum Redis connections")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")


class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str = Field(default="sqlite:///./crowd_management.db", description="Database connection URL")
    echo: bool = Field(default=False, description="Enable SQL logging")
    pool_size: int = Field(default=5, description="Connection pool size")


class SimulationConfig(BaseModel):
    """Crowd simulation configuration"""
    update_interval: float = Field(default=1.0, description="Simulation update interval in seconds")
    max_capacity: int = Field(default=10000, description="Maximum total crowd capacity")
    enable_random_events: bool = Field(default=True, description="Enable random crowd events")
    event_probability: float = Field(default=0.05, description="Probability of random events per update")


class AgentConfig(BaseModel):
    """Agent configuration"""
    response_timeout: int = Field(default=30, description="Agent response timeout in seconds")
    max_concurrent: int = Field(default=10, description="Maximum concurrent agent operations")
    max_conversation_history: int = Field(default=50, description="Maximum conversation history length")
    enable_memory: bool = Field(default=True, description="Enable agent memory/context")
    temperature: float = Field(default=0.7, description="Model temperature for responses")


class APIConfig(BaseModel):
    """API server configuration"""
    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, description="API server port")
    reload: bool = Field(default=False, description="Enable auto-reload in development")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    rate_limit_per_minute: int = Field(default=100, description="Rate limit per IP per minute")


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="json", description="Log format: json or console")
    enable_access_logs: bool = Field(default=True, description="Enable API access logging")


class Settings(BaseSettings):
    """Main application settings"""
    
    # Environment
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=True, description="Enable debug mode")
    
    # Component configurations
    google_cloud: GoogleCloudConfig = Field(default_factory=GoogleCloudConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        extra = "ignore"  # Allow extra fields to be ignored
    
    @classmethod
    def from_env(cls):
        """Create settings from environment variables with proper nesting"""
        # Get environment variables for nested configs
        google_cloud_config = GoogleCloudConfig(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
            region=os.getenv("GOOGLE_CLOUD_REGION", "us-central1"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            service_account_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        )
        
        redis_config = RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379")
        )
        
        database_config = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///./crowd_management.db")
        )
        
        simulation_config = SimulationConfig(
            update_interval=float(os.getenv("SIMULATION_UPDATE_INTERVAL", "1.0")),
            max_capacity=int(os.getenv("MAX_CROWD_CAPACITY", "10000"))
        )
        
        agents_config = AgentConfig(
            response_timeout=int(os.getenv("AGENT_RESPONSE_TIMEOUT", "30")),
            max_concurrent=int(os.getenv("MAX_CONCURRENT_AGENTS", "10")),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7"))
        )
        
        api_config = APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            reload=os.getenv("API_RELOAD", "false").lower() == "true"
        )
        
        logging_config = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "json")
        )
        
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "true").lower() == "true",
            google_cloud=google_cloud_config,
            redis=redis_config,
            database=database_config,
            simulation=simulation_config,
            agents=agents_config,
            api=api_config,
            logging=logging_config
        )
    
    def __init__(self, **kwargs):
        """Initialize settings with environment variables"""
        # If no kwargs provided, use from_env method
        if not kwargs:
            settings_instance = self.from_env()
            super().__init__(**settings_instance.__dict__)
        else:
            super().__init__(**kwargs)
    
    def get_google_credentials(self):
        """Get Google Cloud credentials"""
        if self.google_cloud.service_account_path:
            return service_account.Credentials.from_service_account_file(
                self.google_cloud.service_account_path
            )
        else:
            credentials, project = google.auth.default()
            return credentials
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get Gemini model configuration"""
        return {
            "temperature": self.agents.temperature,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 2048,
        }


# Global settings instance
settings = Settings.from_env()

def get_settings() -> Settings:
    """Get application settings"""
    return settings


def configure_logging():
    """Configure structured logging"""
    import structlog
    import logging
    
    # Configure structlog
    if settings.logging.format == "json":
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.dev.ConsoleRenderer(colors=True)
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Set logging levels
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=getattr(logging, settings.logging.level.upper())
    )


# Configure logging on module import
configure_logging()
