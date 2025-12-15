"""
Tool configuration models.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


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


class ToolConfig(BaseModel):
    """Complete tool configuration."""
    id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Human-readable tool name")
    description: str = Field(..., description="Tool description for LLM")
    type: ToolType = Field(default=ToolType.FUNCTION, description="Tool type")
    
    # Function Schema (OpenAI-compatible)
    parameters: List[ToolParameter] = Field(default_factory=list, description="Tool parameters")
    returns: Optional[Dict[str, Any]] = Field(default=None, description="Return type schema")
    
    # Implementation Details
    implementation: Dict[str, Any] = Field(default_factory=dict, description="Implementation config")
    # For API tools: endpoint, method, headers
    # For Python tools: module, function
    # For Shell tools: command, args
    # For MCP tools: mcp_server_id, tool_name
    
    # Security
    jwt_required: bool = Field(default=True, description="Whether JWT is required")
    allowed_groups: List[str] = Field(default_factory=list, description="JWT groups allowed")
    allowed_roles: List[str] = Field(default_factory=list, description="JWT roles allowed")
    rate_limit: Optional[int] = Field(default=None, description="Rate limit per minute")
    
    # Configuration
    timeout: int = Field(default=30, description="Timeout in seconds")
    retry_count: int = Field(default=0, description="Number of retries on failure")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    created_by: Optional[str] = Field(default=None)
    
    class Config:
        extra = "allow"


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
