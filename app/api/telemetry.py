"""
Telemetry and observability API endpoints.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
import json

from ..models.telemetry import (
    AgentAction, Trace, ActionType, SpanStatus,
    TraceQueryRequest, TraceListResponse, SpanListResponse, TelemetryStats
)
from ..models.auth import AuthenticatedUser
from ..services.telemetry_service import get_telemetry_service, TelemetryService
from .dependencies import get_current_user, get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


def get_service() -> TelemetryService:
    """Get the telemetry service."""
    return get_telemetry_service()


@router.get("/traces", response_model=TraceListResponse, summary="List traces")
async def list_traces(
    trace_id: Optional[str] = Query(default=None, description="Filter by trace ID"),
    agent_id: Optional[str] = Query(default=None, description="Filter by agent ID"),
    graph_id: Optional[str] = Query(default=None, description="Filter by graph ID"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    session_id: Optional[str] = Query(default=None, description="Filter by session ID"),
    status: Optional[SpanStatus] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: TelemetryService = Depends(get_service)
):
    """List traces with optional filtering."""
    request = TraceQueryRequest(
        trace_id=trace_id,
        agent_id=agent_id,
        graph_id=graph_id,
        user_id=user_id,
        session_id=session_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return service.query_traces(request)


@router.get("/traces/{trace_id}", response_model=Trace, summary="Get trace by ID")
async def get_trace(
    trace_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: TelemetryService = Depends(get_service)
):
    """Get a specific trace by ID with all its spans."""
    trace = service.get_trace(trace_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace '{trace_id}' not found"
        )
    return trace


@router.get("/spans", response_model=SpanListResponse, summary="List spans")
async def list_spans(
    trace_id: Optional[str] = Query(default=None, description="Filter by trace ID"),
    agent_id: Optional[str] = Query(default=None, description="Filter by agent ID"),
    graph_id: Optional[str] = Query(default=None, description="Filter by graph ID"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    action_type: Optional[ActionType] = Query(default=None, description="Filter by action type"),
    status: Optional[SpanStatus] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: TelemetryService = Depends(get_service)
):
    """List spans/actions with optional filtering."""
    request = TraceQueryRequest(
        trace_id=trace_id,
        agent_id=agent_id,
        graph_id=graph_id,
        user_id=user_id,
        action_type=action_type,
        status=status,
        limit=limit,
        offset=offset
    )
    return service.query_spans(request)


@router.get("/stats", response_model=TelemetryStats, summary="Get telemetry statistics")
async def get_stats(
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: TelemetryService = Depends(get_service)
):
    """Get aggregated telemetry statistics."""
    return service.get_stats()


@router.get("/action-types", response_model=List[str], summary="Get action types")
async def get_action_types():
    """Get list of available action types."""
    return [t.value for t in ActionType]


@router.post("/traces", response_model=Trace, status_code=status.HTTP_201_CREATED, summary="Create trace")
async def create_trace(
    name: str = Query(..., description="Trace name"),
    agent_id: Optional[str] = Query(default=None),
    graph_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    user: AuthenticatedUser = Depends(get_current_user),
    service: TelemetryService = Depends(get_service)
):
    """Start a new trace for agent execution."""
    trace = service.start_trace(
        name=name,
        agent_id=agent_id,
        graph_id=graph_id,
        user_id=user.user_id,
        session_id=session_id
    )
    return trace


@router.post("/traces/{trace_id}/end", summary="End trace")
async def end_trace(
    trace_id: str,
    status: SpanStatus = Query(default=SpanStatus.OK),
    user: AuthenticatedUser = Depends(get_current_user),
    service: TelemetryService = Depends(get_service)
):
    """End a trace."""
    service.end_trace(trace_id, status)
    return {"success": True, "message": f"Trace {trace_id} ended"}


@router.post("/spans", response_model=AgentAction, status_code=status.HTTP_201_CREATED, summary="Log action")
async def log_action(
    trace_id: str = Query(..., description="Trace ID"),
    action_type: ActionType = Query(..., description="Action type"),
    name: str = Query(..., description="Action name"),
    parent_span_id: Optional[str] = Query(default=None),
    agent_id: Optional[str] = Query(default=None),
    graph_id: Optional[str] = Query(default=None),
    node_id: Optional[str] = Query(default=None),
    tool_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    user: AuthenticatedUser = Depends(get_current_user),
    service: TelemetryService = Depends(get_service)
):
    """Log an agent action/span."""
    action = service.log_action(
        trace_id=trace_id,
        action_type=action_type,
        name=name,
        parent_span_id=parent_span_id,
        agent_id=agent_id,
        graph_id=graph_id,
        node_id=node_id,
        tool_id=tool_id,
        user_id=user.user_id,
        session_id=session_id
    )
    return action


@router.post("/spans/{span_id}/complete", summary="Complete action")
async def complete_action(
    span_id: str,
    status: SpanStatus = Query(default=SpanStatus.OK),
    error_message: Optional[str] = Query(default=None),
    token_count: Optional[int] = Query(default=None),
    user: AuthenticatedUser = Depends(get_current_user),
    service: TelemetryService = Depends(get_service)
):
    """Complete an action span with results."""
    service.complete_action(
        span_id=span_id,
        status=status,
        error_message=error_message,
        token_count=token_count
    )
    return {"success": True, "message": f"Span {span_id} completed"}


@router.post("/export", summary="Export spans to OTEL")
async def export_to_otel(
    user: AuthenticatedUser = Depends(get_current_user),
    service: TelemetryService = Depends(get_service)
):
    """Force export pending spans to OTEL collector."""
    await service._flush_export_queue()
    return {"success": True, "message": "Export triggered"}


@router.get("/traces/{trace_id}/timeline", summary="Get trace timeline")
async def get_trace_timeline(
    trace_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: TelemetryService = Depends(get_service)
):
    """Get a timeline view of a trace with all spans ordered by time."""
    trace = service.get_trace(trace_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace '{trace_id}' not found"
        )
    
    # Sort spans by start time
    sorted_spans = sorted(trace.spans, key=lambda s: s.start_time or s.timestamp)
    
    timeline = []
    for span in sorted_spans:
        timeline.append({
            "span_id": span.span_id,
            "parent_span_id": span.parent_span_id,
            "action_type": span.action_type.value,
            "name": span.name,
            "start_time": span.start_time.isoformat() if span.start_time else None,
            "end_time": span.end_time.isoformat() if span.end_time else None,
            "duration_ms": span.duration_ms,
            "status": span.status.value,
            "agent_id": span.agent_id,
            "node_id": span.node_id,
            "tool_id": span.tool_id,
            "token_count": span.token_count,
            "error_message": span.error_message
        })
    
    return {
        "trace_id": trace_id,
        "name": trace.name,
        "start_time": trace.start_time.isoformat() if trace.start_time else None,
        "end_time": trace.end_time.isoformat() if trace.end_time else None,
        "duration_ms": trace.duration_ms,
        "status": trace.status.value,
        "total_spans": len(timeline),
        "timeline": timeline
    }
