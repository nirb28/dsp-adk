"""
Graph/Pipeline configuration models.
Supports LangGraph and other pipeline technologies.
"""
from enum import Enum
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
from pydantic import BaseModel, Field
from datetime import datetime

if TYPE_CHECKING:
    from .adapters import AdapterReference


class GraphType(str, Enum):
    """Types of graph/pipeline frameworks supported."""
    LANGGRAPH = "langgraph"
    LANGCHAIN = "langchain"
    CUSTOM = "custom"
    DAG = "dag"


class NodeType(str, Enum):
    """Types of nodes in a graph."""
    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    TRANSFORM = "transform"
    ROUTER = "router"
    START = "start"
    END = "end"
    CUSTOM = "custom"


class EdgeType(str, Enum):
    """Types of edges in a graph."""
    NORMAL = "normal"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"


class NodeAdapterReference(BaseModel):
    """Reference to an adapter for use in nodes."""
    adapter_id: str = Field(..., description="ID of the adapter to apply")
    enabled: bool = Field(default=True, description="Override enabled status")
    position: Optional[str] = Field(default=None, description="Override position: pre, post, wrap")
    priority: Optional[int] = Field(default=None, description="Override priority")
    config_overrides: Dict[str, Any] = Field(default_factory=dict, description="Override specific config values")


class GraphNode(BaseModel):
    """Node definition in a graph."""
    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Human-readable node name")
    type: NodeType = Field(default=NodeType.AGENT, description="Node type")
    
    # Node Configuration
    agent_id: Optional[str] = Field(default=None, description="Agent ID if type is agent")
    tool_id: Optional[str] = Field(default=None, description="Tool ID if type is tool")
    
    # For condition/router nodes
    condition: Optional[str] = Field(default=None, description="Condition expression or function name")
    routes: Dict[str, str] = Field(default_factory=dict, description="Condition routes: value -> target_node_id")
    
    # Custom node configuration
    handler: Optional[str] = Field(default=None, description="Custom handler function path")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node-specific configuration")
    
    # Adapters for this node
    adapters: List[NodeAdapterReference] = Field(default_factory=list, description="Adapters applied to this node")
    
    # Metadata
    position: Optional[Dict[str, float]] = Field(default=None, description="Visual position for UI")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"


class GraphEdge(BaseModel):
    """Edge definition connecting nodes in a graph."""
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: EdgeType = Field(default=EdgeType.NORMAL, description="Edge type")
    
    # For conditional edges
    condition: Optional[str] = Field(default=None, description="Condition for this edge")
    condition_value: Optional[Any] = Field(default=None, description="Value that triggers this edge")
    
    # Metadata
    label: Optional[str] = Field(default=None, description="Edge label")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"


class StateSchema(BaseModel):
    """State schema for the graph."""
    fields: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Field definitions: name -> {type, default, description}"
    )
    reducer: Optional[str] = Field(default=None, description="State reducer function")
    
    class Config:
        extra = "allow"


class GraphConfig(BaseModel):
    """Complete graph/pipeline configuration."""
    id: str = Field(..., description="Unique graph identifier")
    name: str = Field(..., description="Human-readable graph name")
    description: Optional[str] = Field(default=None, description="Graph description")
    type: GraphType = Field(default=GraphType.LANGGRAPH, description="Graph framework type")
    
    # Graph Structure
    nodes: List[GraphNode] = Field(default_factory=list, description="Graph nodes")
    edges: List[GraphEdge] = Field(default_factory=list, description="Graph edges")
    entry_point: Optional[str] = Field(default=None, description="Entry point node ID")
    
    # State Management (for LangGraph)
    state_schema: Optional[StateSchema] = Field(default=None, description="State schema definition")
    checkpointer: Optional[str] = Field(default=None, description="Checkpointer type: memory, sqlite, postgres")
    checkpointer_config: Dict[str, Any] = Field(default_factory=dict, description="Checkpointer configuration")
    
    # Execution Configuration
    max_iterations: int = Field(default=25, description="Maximum iterations to prevent infinite loops")
    timeout: int = Field(default=300, description="Execution timeout in seconds")
    streaming: bool = Field(default=True, description="Enable streaming output")
    
    # Agent and Tool References
    agents: List[str] = Field(default_factory=list, description="Agent IDs used in this graph")
    tools: List[str] = Field(default_factory=list, description="Tool IDs used in this graph")
    mcp_servers: List[str] = Field(default_factory=list, description="MCP server IDs used")
    
    # Graph-level Adapters (applied to all nodes unless overridden)
    adapters: List[NodeAdapterReference] = Field(default_factory=list, description="Adapters applied to all nodes")
    
    # Security
    jwt_required: bool = Field(default=True, description="Whether JWT is required")
    allowed_groups: List[str] = Field(default_factory=list, description="JWT groups allowed")
    allowed_roles: List[str] = Field(default_factory=list, description="JWT roles allowed")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    created_by: Optional[str] = Field(default=None)
    
    class Config:
        extra = "allow"


class GraphResponse(BaseModel):
    """Response model for graph operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    graph: Optional[GraphConfig] = Field(default=None, description="Graph configuration")


class GraphListResponse(BaseModel):
    """Response model for listing graphs."""
    success: bool = Field(default=True)
    graphs: List[GraphConfig] = Field(default_factory=list)
    total: int = Field(default=0)


class GraphExecutionRequest(BaseModel):
    """Request to execute a graph."""
    graph_id: str = Field(..., description="Graph ID to execute")
    input: Dict[str, Any] = Field(default_factory=dict, description="Input data")
    config: Dict[str, Any] = Field(default_factory=dict, description="Execution configuration overrides")
    thread_id: Optional[str] = Field(default=None, description="Thread ID for state persistence")


class GraphExecutionResponse(BaseModel):
    """Response from graph execution."""
    success: bool = Field(..., description="Whether execution was successful")
    output: Dict[str, Any] = Field(default_factory=dict, description="Execution output")
    thread_id: Optional[str] = Field(default=None, description="Thread ID used")
    iterations: int = Field(default=0, description="Number of iterations")
    execution_time: float = Field(default=0.0, description="Execution time in seconds")
    error: Optional[str] = Field(default=None, description="Error message if failed")
