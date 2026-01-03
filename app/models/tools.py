"""
Tool configuration models.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.base import ADKComponentConfig, ComponentType


class ToolType(str, Enum):
    """Types of tools supported."""
    FUNCTION = "function"
    API = "api"
    MCP = "mcp"
    PYTHON = "python"
    SHELL = "shell"
    CUSTOM = "custom"


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type: string, integer, boolean, array, object")
    description: Optional[str] = Field(default=None, description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value")
    enum: Optional[List[Any]] = Field(default=None, description="Allowed values")
    
    class Config:
        extra = "allow"


class ToolConfig(ADKComponentConfig):
    """
    Complete tool configuration.
    
    Inherits standard fields from ADKComponentConfig:
    - id, name, description, version
    - component_type, status, enabled
    - tags, category, metadata
    - jwt_required, allowed_groups, allowed_roles
    - dependencies, created_at, updated_at, created_by
    """
    # Override component type
    component_type: ComponentType = Field(default=ComponentType.TOOL)
    
    # Tool-specific type
    tool_type: ToolType = Field(default=ToolType.FUNCTION, description="Tool type")
    
    # Function Schema (OpenAI-compatible)
    parameters: List[ToolParameter] = Field(default_factory=list, description="Tool parameters")
    returns: Optional[Dict[str, Any]] = Field(default=None, description="Return type schema")
    
    # Implementation Details
    implementation: Dict[str, Any] = Field(default_factory=dict, description="Implementation config")
    # For API tools: endpoint, method, headers
    # For Python tools: module, function
    # For Shell tools: command, args
    # For MCP tools: mcp_server_id, tool_name

    usage_instructions: Optional[str] = Field(default=None, description="Optional tool usage instructions")
    fallback_to_user_message_params: List[str] = Field(default_factory=list, description="If missing, fill these params from the user message")
    
    # Tool-specific settings
    rate_limit: Optional[int] = Field(default=None, description="Rate limit per minute")
    timeout: int = Field(default=30, description="Timeout in seconds")
    retry_count: int = Field(default=0, description="Number of retries on failure")


class ToolResponse(BaseModel):
    """Response model for tool operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    tool: Optional[ToolConfig] = Field(default=None, description="Tool configuration")


class ToolListResponse(BaseModel):
    """Response model for listing tools."""
    success: bool = Field(default=True)
    tools: List[ToolConfig] = Field(default_factory=list)
    total: int = Field(default=0)
