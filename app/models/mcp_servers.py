"""
MCP Server configuration models.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MCPProtocol(str, Enum):
    """MCP transport protocols."""
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"
    WEBSOCKET = "websocket"


class MCPToolDefinition(BaseModel):
    """MCP tool definition exposed by a server."""
    name: str = Field(..., description="Tool name")
    description: Optional[str] = Field(default=None, description="Tool description")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for input")
    
    class Config:
        extra = "allow"


class MCPResourceDefinition(BaseModel):
    """MCP resource definition exposed by a server."""
    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(default=None, description="Resource description")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    
    class Config:
        extra = "allow"


class MCPServerConfig(BaseModel):
    """Complete MCP server configuration."""
    id: str = Field(..., description="Unique server identifier")
    name: str = Field(..., description="Human-readable server name")
    description: Optional[str] = Field(default=None, description="Server description")
    
    # Connection Configuration
    protocol: MCPProtocol = Field(default=MCPProtocol.STDIO, description="Transport protocol")
    
    # STDIO Configuration
    command: Optional[str] = Field(default=None, description="Command to run (for stdio)")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    cwd: Optional[str] = Field(default=None, description="Working directory")
    
    # HTTP/SSE/WebSocket Configuration
    endpoint: Optional[str] = Field(default=None, description="Server endpoint URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    
    # Tools and Resources
    tools: List[MCPToolDefinition] = Field(default_factory=list, description="Available tools")
    resources: List[MCPResourceDefinition] = Field(default_factory=list, description="Available resources")
    
    # Security
    jwt_required: bool = Field(default=True, description="Whether JWT is required")
    allowed_groups: List[str] = Field(default_factory=list, description="JWT groups allowed")
    allowed_roles: List[str] = Field(default_factory=list, description="JWT roles allowed")
    api_key_env: Optional[str] = Field(default=None, description="Environment variable for API key")
    
    # Configuration
    timeout: int = Field(default=60, description="Connection timeout in seconds")
    auto_start: bool = Field(default=False, description="Auto-start server on platform startup")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    created_by: Optional[str] = Field(default=None)
    
    class Config:
        extra = "allow"


class MCPServerResponse(BaseModel):
    """Response model for MCP server operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    server: Optional[MCPServerConfig] = Field(default=None, description="Server configuration")


class MCPServerListResponse(BaseModel):
    """Response model for listing MCP servers."""
    success: bool = Field(default=True)
    servers: List[MCPServerConfig] = Field(default_factory=list)
    total: int = Field(default=0)


class MCPServerStatus(BaseModel):
    """MCP server runtime status."""
    server_id: str = Field(..., description="Server ID")
    running: bool = Field(default=False, description="Whether server is running")
    connected: bool = Field(default=False, description="Whether connected to server")
    last_health_check: Optional[datetime] = Field(default=None)
    error: Optional[str] = Field(default=None, description="Last error message")
    tools_available: int = Field(default=0)
    resources_available: int = Field(default=0)
