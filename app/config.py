"""
Configuration settings for the ADK platform.
"""
import os
import re
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from typing import Optional, Any


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # JWT Configuration
    jwt_service_url: str = Field(default="http://localhost:5000", description="URL of the JWT authentication service")
    jwt_secret_key: str = Field(default="dev-secret-key", description="JWT secret key for local validation")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8100, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Storage Configuration
    storage_path: str = Field(default="./data", description="Base storage path")
    agents_dir: str = Field(default="./data/agents", description="Agents configuration directory")
    tools_dir: str = Field(default="./data/tools", description="Tools configuration directory")
    graphs_dir: str = Field(default="./data/graphs", description="Graphs configuration directory")
    mcp_servers_dir: str = Field(default="./data/mcp_servers", description="MCP servers configuration directory")
    
    # OpenTelemetry Configuration
    otel_enabled: bool = Field(default=True, description="Enable OpenTelemetry telemetry")
    otel_endpoint: Optional[str] = Field(default=None, description="OTEL collector endpoint (e.g., http://localhost:4318)")
    otel_service_name: str = Field(default="adk", description="Service name for OTEL")
    otel_export_interval: int = Field(default=5000, description="Export interval in milliseconds")
    otel_max_traces: int = Field(default=10000, description="Maximum traces to keep in memory")
    otel_max_spans: int = Field(default=100000, description="Maximum spans to keep in memory")
    
    # Logging
    log_level: str = Field(default="DEBUG", description="Logging level")
    verbose_logging: bool = Field(default=False, description="Enable verbose payload logging (logs all request/response payloads)")

    # Langfuse (optional)
    langfuse_enabled: bool = Field(default=False, description="Enable Langfuse observability")
    langfuse_public_key: Optional[str] = Field(default=None, description="Langfuse public key")
    langfuse_secret_key: Optional[str] = Field(default=None, description="Langfuse secret key")
    langfuse_base_url: Optional[str] = Field(default=None, description="Langfuse base URL (cloud or self-hosted)")
    langfuse_host: Optional[str] = Field(default=None, description="Deprecated alias for langfuse_base_url")
    langfuse_tracing_enabled: Optional[bool] = Field(default=None, description="Override Langfuse tracing_enabled setting")
    
    @model_validator(mode='after')
    def resolve_env_variables(self) -> 'Settings':
        """Resolve ${VARIABLE} references in all string fields after loading."""
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, str):
                resolved = self._resolve_string(field_value)
                setattr(self, field_name, resolved)
        return self
    
    def _resolve_string(self, value: str) -> str:
        """Resolve ${VAR} and $VAR references in a string."""
        result = value
        
        # Match ${VAR_NAME}
        pattern_braces = r'\$\{([^}]+)\}'
        for var_name in re.findall(pattern_braces, result):
            env_value = os.getenv(var_name, '')
            if env_value:
                result = result.replace(f'${{{var_name}}}', env_value)
        
        # Match $VAR_NAME
        pattern_simple = r'\$([A-Za-z_][A-Za-z0-9_]*)'
        for var_name in re.findall(pattern_simple, result):
            env_value = os.getenv(var_name, '')
            if env_value:
                result = result.replace(f'${var_name}', env_value)
        
        return result
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


def ensure_directories(settings: Settings) -> None:
    """Ensure all required directories exist."""
    directories = [
        settings.storage_path,
        settings.agents_dir,
        settings.tools_dir,
        settings.graphs_dir,
        settings.mcp_servers_dir,
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
