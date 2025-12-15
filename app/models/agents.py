"""
Agent configuration models.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AgentType(str, Enum):
    """Types of agents supported by the platform."""
    CONVERSATIONAL = "conversational"
    TASK_EXECUTOR = "task_executor"
    TOOL_USER = "tool_user"
    MULTI_AGENT = "multi_agent"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Agent lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class AgentCapability(str, Enum):
    """Agent capabilities."""
    TOOL_CALLING = "tool_calling"
    MEMORY = "memory"
    STREAMING = "streaming"
    MULTI_TURN = "multi_turn"
    CODE_EXECUTION = "code_execution"
    FILE_HANDLING = "file_handling"
    WEB_BROWSING = "web_browsing"


class AgentMemoryConfig(BaseModel):
    """Configuration for agent memory."""
    enabled: bool = Field(default=False, description="Whether memory is enabled")
    type: str = Field(default="buffer", description="Memory type: buffer, summary, vector")
    max_tokens: int = Field(default=4000, description="Maximum tokens to retain")
    persistence: bool = Field(default=False, description="Whether to persist memory")
    
    class Config:
        extra = "allow"


class LLMConfig(BaseModel):
    """LLM configuration for the agent."""
    provider: str = Field(..., description="LLM provider: openai, groq, anthropic, nvidia, local")
    model: str = Field(..., description="Model name/identifier")
    endpoint: Optional[str] = Field(default=None, description="Custom endpoint URL")
    api_key_env: Optional[str] = Field(default=None, description="Environment variable for API key")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: int = Field(default=2048, description="Maximum tokens to generate")
    system_prompt: Optional[str] = Field(default=None, description="System prompt for the agent")
    
    class Config:
        extra = "allow"


class AgentConfig(BaseModel):
    """Complete agent configuration."""
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    description: Optional[str] = Field(default=None, description="Agent description")
    type: AgentType = Field(default=AgentType.CONVERSATIONAL, description="Agent type")
    status: AgentStatus = Field(default=AgentStatus.DRAFT, description="Agent status")
    
    # LLM Configuration
    llm: LLMConfig = Field(..., description="LLM configuration")
    
    # Capabilities and Features
    capabilities: List[AgentCapability] = Field(default_factory=list, description="Agent capabilities")
    
    # Tool Integration
    tools: List[str] = Field(default_factory=list, description="List of tool IDs assigned to this agent")
    mcp_servers: List[str] = Field(default_factory=list, description="List of MCP server IDs to use")
    
    # Graph/Pipeline Integration
    graph_id: Optional[str] = Field(default=None, description="Associated graph/pipeline ID")
    
    # Memory Configuration
    memory: AgentMemoryConfig = Field(default_factory=AgentMemoryConfig, description="Memory configuration")
    
    # Security
    jwt_required: bool = Field(default=True, description="Whether JWT authentication is required")
    allowed_groups: List[str] = Field(default_factory=list, description="JWT groups allowed to use this agent")
    allowed_roles: List[str] = Field(default_factory=list, description="JWT roles allowed to use this agent")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator user ID")
    
    class Config:
        extra = "allow"


class AgentResponse(BaseModel):
    """Response model for agent operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    agent: Optional[AgentConfig] = Field(default=None, description="Agent configuration")


class AgentListResponse(BaseModel):
    """Response model for listing agents."""
    success: bool = Field(default=True)
    agents: List[AgentConfig] = Field(default_factory=list)
    total: int = Field(default=0)
