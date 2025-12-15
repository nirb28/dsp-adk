"""
Telemetry and observability models for agent action logging.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ActionType(str, Enum):
    """Types of agent actions."""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    MCP_CALL = "mcp_call"
    MCP_RESULT = "mcp_result"
    GRAPH_NODE_ENTER = "graph_node_enter"
    GRAPH_NODE_EXIT = "graph_node_exit"
    GRAPH_EDGE_TRAVERSE = "graph_edge_traverse"
    STATE_UPDATE = "state_update"
    ERROR = "error"
    CUSTOM = "custom"


class SpanKind(str, Enum):
    """OpenTelemetry span kinds."""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    """Span status codes."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


class AgentAction(BaseModel):
    """Represents a single agent action/event."""
    trace_id: str = Field(..., description="Trace ID for correlation")
    span_id: str = Field(..., description="Unique span ID")
    parent_span_id: Optional[str] = Field(default=None, description="Parent span ID")
    
    # Action details
    action_type: ActionType = Field(..., description="Type of action")
    name: str = Field(..., description="Action name")
    
    # Context
    agent_id: Optional[str] = Field(default=None, description="Agent ID")
    graph_id: Optional[str] = Field(default=None, description="Graph ID")
    node_id: Optional[str] = Field(default=None, description="Node ID in graph")
    tool_id: Optional[str] = Field(default=None, description="Tool ID if tool call")
    
    # User context
    user_id: Optional[str] = Field(default=None, description="User ID from JWT")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    duration_ms: Optional[float] = Field(default=None, description="Duration in milliseconds")
    
    # Status
    status: SpanStatus = Field(default=SpanStatus.UNSET)
    error_message: Optional[str] = Field(default=None)
    error_type: Optional[str] = Field(default=None)
    
    # Span metadata
    kind: SpanKind = Field(default=SpanKind.INTERNAL)
    
    # Input/Output (can be redacted for security)
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Input data")
    output_data: Optional[Dict[str, Any]] = Field(default=None, description="Output data")
    
    # Metrics
    token_count: Optional[int] = Field(default=None, description="LLM tokens used")
    input_tokens: Optional[int] = Field(default=None)
    output_tokens: Optional[int] = Field(default=None)
    
    # Custom attributes (OTEL attributes)
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom OTEL attributes")
    
    # Events within the span
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Span events")
    
    class Config:
        extra = "allow"


class Trace(BaseModel):
    """A complete trace containing multiple spans."""
    trace_id: str = Field(..., description="Trace ID")
    name: str = Field(..., description="Trace name")
    
    # Root span info
    agent_id: Optional[str] = Field(default=None)
    graph_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    
    # Timing
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = Field(default=None)
    duration_ms: Optional[float] = Field(default=None)
    
    # Status
    status: SpanStatus = Field(default=SpanStatus.UNSET)
    
    # All spans in this trace
    spans: List[AgentAction] = Field(default_factory=list)
    
    # Aggregated metrics
    total_tokens: int = Field(default=0)
    total_tool_calls: int = Field(default=0)
    total_llm_calls: int = Field(default=0)
    error_count: int = Field(default=0)
    
    # Resource attributes
    service_name: str = Field(default="adk")
    service_version: str = Field(default="0.1.0")
    
    class Config:
        extra = "allow"


class OTELExportRequest(BaseModel):
    """Request to export spans to OTEL collector."""
    spans: List[AgentAction] = Field(..., description="Spans to export")
    resource_attributes: Dict[str, Any] = Field(default_factory=dict)


class TraceQueryRequest(BaseModel):
    """Request to query traces."""
    trace_id: Optional[str] = Field(default=None)
    agent_id: Optional[str] = Field(default=None)
    graph_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    action_type: Optional[ActionType] = Field(default=None)
    status: Optional[SpanStatus] = Field(default=None)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class TraceListResponse(BaseModel):
    """Response for trace listing."""
    success: bool = Field(default=True)
    traces: List[Trace] = Field(default_factory=list)
    total: int = Field(default=0)


class SpanListResponse(BaseModel):
    """Response for span listing."""
    success: bool = Field(default=True)
    spans: List[AgentAction] = Field(default_factory=list)
    total: int = Field(default=0)


class TelemetryStats(BaseModel):
    """Telemetry statistics."""
    total_traces: int = Field(default=0)
    total_spans: int = Field(default=0)
    total_errors: int = Field(default=0)
    total_tokens: int = Field(default=0)
    avg_duration_ms: float = Field(default=0.0)
    traces_by_agent: Dict[str, int] = Field(default_factory=dict)
    traces_by_status: Dict[str, int] = Field(default_factory=dict)
    actions_by_type: Dict[str, int] = Field(default_factory=dict)
