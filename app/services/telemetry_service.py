"""
OpenTelemetry service for agent action logging.
"""
import logging
import uuid
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from collections import defaultdict

import httpx

from ..config import get_settings
from ..models.telemetry import (
    AgentAction, Trace, ActionType, SpanStatus, SpanKind,
    TraceQueryRequest, TraceListResponse, SpanListResponse, TelemetryStats
)
from .langfuse_service import get_langfuse_service

logger = logging.getLogger(__name__)


class TelemetryService:
    """Service for collecting and exporting agent telemetry to OTEL."""
    
    def __init__(self):
        self.settings = get_settings()
        self.langfuse_service = get_langfuse_service()
        self._traces: Dict[str, Trace] = {}  # In-memory trace storage
        self._spans: List[AgentAction] = []  # All spans for querying
        self._http_client: Optional[httpx.AsyncClient] = None
        self._export_queue: List[AgentAction] = []
        self._export_lock = asyncio.Lock()
        
        # OTEL endpoint configuration
        self.otel_endpoint = getattr(self.settings, 'otel_endpoint', None)
        self.otel_enabled = getattr(self.settings, 'otel_enabled', True)
        self.service_name = getattr(self.settings, 'otel_service_name', 'adk')
        self.service_version = "0.1.0"
        
        # Retention settings
        self.max_traces = getattr(self.settings, 'otel_max_traces', 10000)
        self.max_spans = getattr(self.settings, 'otel_max_spans', 100000)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for OTEL export."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def close(self):
        """Close HTTP client and flush pending exports."""
        await self._flush_export_queue()
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        try:
            self.langfuse_service.flush()
            self.langfuse_service.shutdown()
        except Exception:
            pass
    
    def generate_trace_id(self) -> str:
        """Generate a new trace ID."""
        return uuid.uuid4().hex
    
    def generate_span_id(self) -> str:
        """Generate a new span ID."""
        return uuid.uuid4().hex[:16]
    
    def start_trace(
        self,
        name: str,
        agent_id: Optional[str] = None,
        graph_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Trace:
        """Start a new trace."""
        trace_id = trace_id or self.generate_trace_id()
        
        trace = Trace(
            trace_id=trace_id,
            name=name,
            agent_id=agent_id,
            graph_id=graph_id,
            user_id=user_id,
            session_id=session_id,
            start_time=datetime.now(timezone.utc),
            service_name=self.service_name,
            service_version=self.service_version
        )
        
        self._traces[trace_id] = trace
        self._cleanup_old_traces()

        try:
            self.langfuse_service.on_trace_started(trace)
        except Exception:
            pass
        
        logger.debug(f"Started trace {trace_id}: {name}")
        return trace
    
    def end_trace(self, trace_id: str, status: SpanStatus = SpanStatus.OK):
        """End a trace and queue spans for export."""
        if trace_id not in self._traces:
            logger.warning(f"Trace {trace_id} not found")
            return
        
        trace = self._traces[trace_id]
        trace.end_time = datetime.now(timezone.utc)
        trace.status = status
        
        if trace.start_time and trace.end_time:
            trace.duration_ms = (trace.end_time - trace.start_time).total_seconds() * 1000
        
        # Calculate aggregates
        trace.total_tokens = sum(s.token_count or 0 for s in trace.spans)
        trace.total_tool_calls = sum(1 for s in trace.spans if s.action_type == ActionType.TOOL_CALL)
        trace.total_llm_calls = sum(1 for s in trace.spans if s.action_type == ActionType.LLM_REQUEST)
        trace.error_count = sum(1 for s in trace.spans if s.status == SpanStatus.ERROR)
        
        logger.debug(f"Ended trace {trace_id} with status {status}")

        try:
            self.langfuse_service.on_trace_ended(trace_id=trace_id, status=status)
        except Exception:
            pass
        
        # Trigger immediate export in background
        if self.otel_enabled and trace.spans:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.export_to_otel(trace.spans))
                else:
                    # If no event loop is running, export synchronously
                    loop.run_until_complete(self.export_to_otel(trace.spans))
            except RuntimeError:
                # No event loop available, log warning
                logger.warning(f"Cannot export trace {trace_id}: no event loop available")
    
    def log_action(
        self,
        trace_id: str,
        action_type: ActionType,
        name: str,
        parent_span_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        graph_id: Optional[str] = None,
        node_id: Optional[str] = None,
        tool_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        status: SpanStatus = SpanStatus.UNSET,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        token_count: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        duration_ms: Optional[float] = None,
        attributes: Optional[Dict[str, Any]] = None,
        kind: SpanKind = SpanKind.INTERNAL
    ) -> AgentAction:
        """Log an agent action as a span."""
        if trace_id in self._traces:
            trace = self._traces[trace_id]
            if session_id is None:
                session_id = trace.session_id
            if user_id is None:
                user_id = trace.user_id

        span_id = self.generate_span_id()
        now = datetime.now(timezone.utc)
        
        action = AgentAction(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            action_type=action_type,
            name=name,
            agent_id=agent_id,
            graph_id=graph_id,
            node_id=node_id,
            tool_id=tool_id,
            user_id=user_id,
            session_id=session_id,
            timestamp=now,
            start_time=now,
            status=status,
            error_message=error_message,
            error_type=error_type,
            input_data=input_data,
            output_data=output_data,
            token_count=token_count,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            attributes=attributes or {},
            kind=kind
        )
        
        # Add to trace if exists
        if trace_id in self._traces:
            self._traces[trace_id].spans.append(action)
        
        # Store span for querying
        self._spans.append(action)
        self._cleanup_old_spans()
        
        # Queue for export
        self._export_queue.append(action)

        try:
            self.langfuse_service.on_action_started(action)
        except Exception:
            pass
        
        logger.debug(f"Logged action {action_type}: {name} (trace={trace_id}, span={span_id})")
        return action
    
    def add_span_event(
        self,
        span_id: str,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Add an event to a span for detailed payload tracking."""
        for span in reversed(self._spans):
            if span.span_id == span_id:
                event = {
                    "name": name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "attributes": attributes or {}
                }
                span.events.append(event)
                logger.debug(f"Added event '{name}' to span {span_id}")

                try:
                    self.langfuse_service.on_span_event(
                        trace_id=span.trace_id,
                        span_id=span_id,
                        name=name,
                        attributes=attributes or {}
                    )
                except Exception:
                    pass
                break
    
    def complete_action(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.OK,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        token_count: Optional[int] = None
    ):
        """Complete an action span with results."""
        for span in reversed(self._spans):
            if span.span_id == span_id:
                span.end_time = datetime.now(timezone.utc)
                span.status = status
                if output_data:
                    span.output_data = output_data
                if error_message:
                    span.error_message = error_message
                if token_count:
                    span.token_count = token_count
                if span.start_time and span.end_time:
                    span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000

                try:
                    self.langfuse_service.on_action_completed(span)
                except Exception:
                    pass
                break
    
    async def export_to_otel(self, spans: List[AgentAction]) -> bool:
        """Export spans to OTEL collector."""
        if not self.otel_endpoint or not self.otel_enabled:
            logger.debug("OTEL export disabled or no endpoint configured")
            return True
        
        try:
            logger.info(f"[TELEMETRY] Exporting {len(spans)} spans to {self.otel_endpoint}/v1/traces")
            client = await self._get_client()
            
            # Convert spans to OTLP JSON format
            otlp_data = self._convert_to_otlp(spans)
            
            response = await client.post(
                f"{self.otel_endpoint}/v1/traces",
                json=otlp_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 202]:
                logger.info(f"[TELEMETRY] Successfully exported {len(spans)} spans to OTEL (status: {response.status_code})")
                return True
            else:
                logger.error(f"[TELEMETRY] OTEL export failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"[TELEMETRY] Error exporting to OTEL: {e}", exc_info=True)
            return False
    
    def _convert_to_otlp(self, spans: List[AgentAction]) -> Dict[str, Any]:
        """Convert spans to OTLP JSON format."""
        otlp_spans = []
        
        for span in spans:
            # Build base attributes
            base_attrs = {
                "adk.action_type": span.action_type.value,
                "adk.agent_id": span.agent_id,
                "adk.graph_id": span.graph_id,
                "adk.node_id": span.node_id,
                "adk.tool_id": span.tool_id,
                "adk.user_id": span.user_id,
                "adk.session_id": span.session_id,
                "adk.token_count": span.token_count,
                "adk.input_tokens": span.input_tokens,
                "adk.output_tokens": span.output_tokens,
            }
            
            # Add input/output data as JSON strings for better visibility
            if span.input_data:
                try:
                    import json
                    base_attrs["adk.input_data"] = json.dumps(span.input_data)
                except:
                    base_attrs["adk.input_data"] = str(span.input_data)
            
            if span.output_data:
                try:
                    import json
                    base_attrs["adk.output_data"] = json.dumps(span.output_data)
                except:
                    base_attrs["adk.output_data"] = str(span.output_data)
            
            # Merge with custom attributes
            all_attrs = {**base_attrs, **span.attributes}
            
            otlp_span = {
                "traceId": span.trace_id,
                "spanId": span.span_id,
                "parentSpanId": span.parent_span_id or "",
                "name": span.name,
                "kind": self._span_kind_to_otlp(span.kind),
                "startTimeUnixNano": int(span.start_time.timestamp() * 1e9) if span.start_time else 0,
                "endTimeUnixNano": int(span.end_time.timestamp() * 1e9) if span.end_time else 0,
                "status": {
                    "code": self._status_to_otlp(span.status),
                    "message": span.error_message or ""
                },
                "attributes": self._dict_to_otlp_attributes(all_attrs),
                "events": [
                    {
                        "name": e.get("name", "event"),
                        "timeUnixNano": self._parse_event_timestamp(e.get("timestamp")),
                        "attributes": self._dict_to_otlp_attributes(e.get("attributes", {}))
                    }
                    for e in span.events
                ]
            }
            otlp_spans.append(otlp_span)
        
        return {
            "resourceSpans": [{
                "resource": {
                    "attributes": self._dict_to_otlp_attributes({
                        "service.name": self.service_name,
                        "service.version": self.service_version
                    })
                },
                "scopeSpans": [{
                    "scope": {"name": "adk.telemetry"},
                    "spans": otlp_spans
                }]
            }]
        }
    
    def _dict_to_otlp_attributes(self, d: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert dict to OTLP attributes format."""
        attrs = []
        for k, v in d.items():
            if v is None:
                continue
            attr = {"key": k}
            if isinstance(v, bool):
                attr["value"] = {"boolValue": v}
            elif isinstance(v, int):
                attr["value"] = {"intValue": str(v)}
            elif isinstance(v, float):
                attr["value"] = {"doubleValue": v}
            else:
                attr["value"] = {"stringValue": str(v)}
            attrs.append(attr)
        return attrs
    
    def _span_kind_to_otlp(self, kind: SpanKind) -> int:
        """Convert span kind to OTLP integer."""
        mapping = {
            SpanKind.INTERNAL: 1,
            SpanKind.SERVER: 2,
            SpanKind.CLIENT: 3,
            SpanKind.PRODUCER: 4,
            SpanKind.CONSUMER: 5
        }
        return mapping.get(kind, 1)
    
    def _status_to_otlp(self, status: SpanStatus) -> int:
        """Convert status to OTLP integer."""
        mapping = {
            SpanStatus.UNSET: 0,
            SpanStatus.OK: 1,
            SpanStatus.ERROR: 2
        }
        return mapping.get(status, 0)
    
    def _parse_event_timestamp(self, timestamp_str: Optional[str]) -> int:
        """Parse event timestamp string to Unix nanoseconds."""
        if not timestamp_str:
            return int(datetime.now(timezone.utc).timestamp() * 1e9)
        
        try:
            # Try parsing ISO format timestamp
            from dateutil import parser
            dt = parser.isoparse(timestamp_str)
            return int(dt.timestamp() * 1e9)
        except:
            # Fallback to current time
            return int(datetime.now(timezone.utc).timestamp() * 1e9)
    
    async def _flush_export_queue(self):
        """Flush pending exports."""
        async with self._export_lock:
            if self._export_queue:
                await self.export_to_otel(self._export_queue)
                self._export_queue.clear()
    
    def _cleanup_old_traces(self):
        """Remove old traces to prevent memory growth."""
        if len(self._traces) > self.max_traces:
            # Remove oldest traces
            sorted_traces = sorted(
                self._traces.items(),
                key=lambda x: x[1].start_time
            )
            to_remove = len(self._traces) - self.max_traces
            for trace_id, _ in sorted_traces[:to_remove]:
                del self._traces[trace_id]
    
    def _cleanup_old_spans(self):
        """Remove old spans to prevent memory growth."""
        if len(self._spans) > self.max_spans:
            self._spans = self._spans[-self.max_spans:]
    
    # Query methods
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        return self._traces.get(trace_id)
    
    def query_traces(self, request: TraceQueryRequest) -> TraceListResponse:
        """Query traces with filters."""
        traces = list(self._traces.values())
        
        # Apply filters
        if request.trace_id:
            traces = [t for t in traces if t.trace_id == request.trace_id]
        if request.agent_id:
            traces = [t for t in traces if t.agent_id == request.agent_id]
        if request.graph_id:
            traces = [t for t in traces if t.graph_id == request.graph_id]
        if request.user_id:
            traces = [t for t in traces if t.user_id == request.user_id]
        if request.session_id:
            traces = [t for t in traces if t.session_id == request.session_id]
        if request.status:
            traces = [t for t in traces if t.status == request.status]
        if request.start_time:
            traces = [t for t in traces if t.start_time >= request.start_time]
        if request.end_time:
            traces = [t for t in traces if t.start_time <= request.end_time]
        
        # Sort by start time descending
        traces = sorted(traces, key=lambda t: t.start_time, reverse=True)
        
        total = len(traces)
        traces = traces[request.offset:request.offset + request.limit]
        
        return TraceListResponse(success=True, traces=traces, total=total)
    
    def query_spans(self, request: TraceQueryRequest) -> SpanListResponse:
        """Query spans with filters."""
        spans = list(self._spans)
        
        # Apply filters
        if request.trace_id:
            spans = [s for s in spans if s.trace_id == request.trace_id]
        if request.agent_id:
            spans = [s for s in spans if s.agent_id == request.agent_id]
        if request.graph_id:
            spans = [s for s in spans if s.graph_id == request.graph_id]
        if request.user_id:
            spans = [s for s in spans if s.user_id == request.user_id]
        if request.action_type:
            spans = [s for s in spans if s.action_type == request.action_type]
        if request.status:
            spans = [s for s in spans if s.status == request.status]
        if request.start_time:
            spans = [s for s in spans if s.timestamp >= request.start_time]
        if request.end_time:
            spans = [s for s in spans if s.timestamp <= request.end_time]
        
        # Sort by timestamp descending
        spans = sorted(spans, key=lambda s: s.timestamp, reverse=True)
        
        total = len(spans)
        spans = spans[request.offset:request.offset + request.limit]
        
        return SpanListResponse(success=True, spans=spans, total=total)
    
    def get_stats(self) -> TelemetryStats:
        """Get telemetry statistics."""
        traces_by_agent = defaultdict(int)
        traces_by_status = defaultdict(int)
        actions_by_type = defaultdict(int)
        total_tokens = 0
        total_duration = 0.0
        duration_count = 0
        
        for trace in self._traces.values():
            if trace.agent_id:
                traces_by_agent[trace.agent_id] += 1
            traces_by_status[trace.status.value] += 1
            total_tokens += trace.total_tokens
            if trace.duration_ms:
                total_duration += trace.duration_ms
                duration_count += 1
        
        for span in self._spans:
            actions_by_type[span.action_type.value] += 1
        
        return TelemetryStats(
            total_traces=len(self._traces),
            total_spans=len(self._spans),
            total_errors=sum(1 for s in self._spans if s.status == SpanStatus.ERROR),
            total_tokens=total_tokens,
            avg_duration_ms=total_duration / duration_count if duration_count > 0 else 0.0,
            traces_by_agent=dict(traces_by_agent),
            traces_by_status=dict(traces_by_status),
            actions_by_type=dict(actions_by_type)
        )


# Singleton
_telemetry_service: Optional[TelemetryService] = None


def get_telemetry_service() -> TelemetryService:
    """Get the telemetry service singleton."""
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService()
    return _telemetry_service
