"""
Adapter configuration models.
Adapters provide cross-cutting concerns like security, observability, caching, etc.
"""
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class AdapterType(str, Enum):
    """Types of adapters supported."""
    SECURITY = "security"
    OBSERVABILITY = "observability"
    CACHING = "caching"
    RATE_LIMITING = "rate_limiting"
    RETRY = "retry"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    LOGGING = "logging"
    CUSTOM = "custom"


class AdapterPosition(str, Enum):
    """Position of adapter in execution pipeline."""
    PRE = "pre"      # Execute before the node
    POST = "post"    # Execute after the node
    WRAP = "wrap"    # Wrap the node execution


# Security Adapter Configuration
class JWTValidationConfig(BaseModel):
    """JWT validation configuration."""
    enabled: bool = Field(default=True)
    jwt_service_url: Optional[str] = Field(default=None, description="JWT service URL for remote validation")
    secret_key_env: Optional[str] = Field(default=None, description="Environment variable for JWT secret")
    algorithm: str = Field(default="HS256")
    required_claims: List[str] = Field(default_factory=list, description="Claims that must be present")
    required_groups: List[str] = Field(default_factory=list)
    required_roles: List[str] = Field(default_factory=list)
    extract_metadata_filter: bool = Field(default=True, description="Extract metadata_filter claim")


class APIKeyValidationConfig(BaseModel):
    """API key validation configuration."""
    enabled: bool = Field(default=False)
    header_name: str = Field(default="X-API-Key")
    valid_keys_env: Optional[str] = Field(default=None, description="Environment variable with valid keys")


class SecurityAdapterConfig(BaseModel):
    """Security adapter configuration."""
    jwt: Optional[JWTValidationConfig] = Field(default=None)
    api_key: Optional[APIKeyValidationConfig] = Field(default=None)
    input_sanitization: bool = Field(default=True, description="Sanitize input for injection attacks")
    output_filtering: bool = Field(default=False, description="Filter sensitive data from output")
    sensitive_fields: List[str] = Field(default_factory=lambda: ["password", "secret", "token", "api_key"])
    audit_logging: bool = Field(default=True, description="Log security events")


# Observability Adapter Configuration
class MetricsConfig(BaseModel):
    """Metrics collection configuration."""
    enabled: bool = Field(default=True)
    provider: str = Field(default="prometheus", description="prometheus, datadog, custom")
    endpoint: Optional[str] = Field(default=None)
    prefix: str = Field(default="adk_")
    labels: Dict[str, str] = Field(default_factory=dict)
    collect_latency: bool = Field(default=True)
    collect_tokens: bool = Field(default=True)
    collect_errors: bool = Field(default=True)


class TracingConfig(BaseModel):
    """Distributed tracing configuration."""
    enabled: bool = Field(default=True)
    provider: str = Field(default="opentelemetry", description="opentelemetry, jaeger, zipkin")
    endpoint: Optional[str] = Field(default=None)
    service_name: str = Field(default="adk")
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    propagate_context: bool = Field(default=True)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    enabled: bool = Field(default=True)
    level: str = Field(default="INFO")
    format: str = Field(default="json", description="json, text")
    include_request: bool = Field(default=True)
    include_response: bool = Field(default=False, description="May contain sensitive data")
    include_metadata: bool = Field(default=True)
    redact_fields: List[str] = Field(default_factory=lambda: ["password", "secret", "token"])


class ObservabilityAdapterConfig(BaseModel):
    """Observability adapter configuration."""
    metrics: Optional[MetricsConfig] = Field(default=None)
    tracing: Optional[TracingConfig] = Field(default=None)
    logging: Optional[LoggingConfig] = Field(default=None)


# Caching Adapter Configuration
class CachingAdapterConfig(BaseModel):
    """Caching adapter configuration."""
    enabled: bool = Field(default=True)
    provider: str = Field(default="memory", description="memory, redis, memcached")
    ttl_seconds: int = Field(default=300, description="Time to live in seconds")
    max_size: int = Field(default=1000, description="Maximum cache entries")
    key_prefix: str = Field(default="adk_cache_")
    redis_url: Optional[str] = Field(default=None)
    cache_by: List[str] = Field(default_factory=lambda: ["query"], description="Fields to use for cache key")
    skip_on_error: bool = Field(default=True, description="Skip caching on errors")


# Rate Limiting Adapter Configuration
class RateLimitingAdapterConfig(BaseModel):
    """Rate limiting adapter configuration."""
    enabled: bool = Field(default=True)
    provider: str = Field(default="memory", description="memory, redis")
    requests_per_minute: int = Field(default=60)
    requests_per_hour: Optional[int] = Field(default=None)
    requests_per_day: Optional[int] = Field(default=None)
    key_by: str = Field(default="user", description="user, ip, api_key, custom")
    custom_key_field: Optional[str] = Field(default=None)
    redis_url: Optional[str] = Field(default=None)
    return_headers: bool = Field(default=True, description="Include rate limit headers in response")


# Retry Adapter Configuration
class RetryAdapterConfig(BaseModel):
    """Retry adapter configuration."""
    enabled: bool = Field(default=True)
    max_retries: int = Field(default=3)
    initial_delay_ms: int = Field(default=100)
    max_delay_ms: int = Field(default=10000)
    exponential_backoff: bool = Field(default=True)
    retry_on_status: List[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])
    retry_on_exceptions: List[str] = Field(default_factory=lambda: ["TimeoutError", "ConnectionError"])


# Transformation Adapter Configuration
class TransformationAdapterConfig(BaseModel):
    """Input/output transformation configuration."""
    enabled: bool = Field(default=True)
    input_transforms: List[Dict[str, Any]] = Field(default_factory=list, description="Input transformation rules")
    output_transforms: List[Dict[str, Any]] = Field(default_factory=list, description="Output transformation rules")
    template_engine: str = Field(default="jinja2", description="jinja2, handlebars")


# Validation Adapter Configuration
class ValidationAdapterConfig(BaseModel):
    """Input/output validation configuration."""
    enabled: bool = Field(default=True)
    input_schema: Optional[Dict[str, Any]] = Field(default=None, description="JSON Schema for input validation")
    output_schema: Optional[Dict[str, Any]] = Field(default=None, description="JSON Schema for output validation")
    strict_mode: bool = Field(default=False, description="Fail on validation errors")
    log_violations: bool = Field(default=True)


# Custom Adapter Configuration
class CustomAdapterConfig(BaseModel):
    """Custom adapter configuration."""
    handler_module: str = Field(..., description="Python module path")
    handler_function: str = Field(..., description="Handler function name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Custom configuration")


class AdapterConfig(BaseModel):
    """Complete adapter configuration."""
    id: str = Field(..., description="Unique adapter identifier")
    name: str = Field(..., description="Human-readable adapter name")
    description: Optional[str] = Field(default=None)
    type: AdapterType = Field(..., description="Adapter type")
    position: AdapterPosition = Field(default=AdapterPosition.WRAP, description="Execution position")
    enabled: bool = Field(default=True)
    priority: int = Field(default=100, description="Execution priority (lower = earlier)")
    
    # Type-specific configurations (only one should be set based on type)
    security: Optional[SecurityAdapterConfig] = Field(default=None)
    observability: Optional[ObservabilityAdapterConfig] = Field(default=None)
    caching: Optional[CachingAdapterConfig] = Field(default=None)
    rate_limiting: Optional[RateLimitingAdapterConfig] = Field(default=None)
    retry: Optional[RetryAdapterConfig] = Field(default=None)
    transformation: Optional[TransformationAdapterConfig] = Field(default=None)
    validation: Optional[ValidationAdapterConfig] = Field(default=None)
    custom: Optional[CustomAdapterConfig] = Field(default=None)
    
    # Conditions
    apply_to_types: List[str] = Field(default_factory=list, description="Node types to apply to (empty = all)")
    skip_types: List[str] = Field(default_factory=list, description="Node types to skip")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Additional conditions")
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    created_by: Optional[str] = Field(default=None)
    
    class Config:
        extra = "allow"


class AdapterReference(BaseModel):
    """Reference to an adapter for use in graphs/agents."""
    adapter_id: str = Field(..., description="ID of the adapter to apply")
    enabled: bool = Field(default=True, description="Override enabled status")
    position: Optional[AdapterPosition] = Field(default=None, description="Override position")
    priority: Optional[int] = Field(default=None, description="Override priority")
    config_overrides: Dict[str, Any] = Field(default_factory=dict, description="Override specific config values")


class AdapterResponse(BaseModel):
    """Response model for adapter operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    adapter: Optional[AdapterConfig] = Field(default=None)


class AdapterListResponse(BaseModel):
    """Response model for listing adapters."""
    success: bool = Field(default=True)
    adapters: List[AdapterConfig] = Field(default_factory=list)
    total: int = Field(default=0)
