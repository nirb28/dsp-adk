# OpenTelemetry Integration in ADK

## Overview

The Agent Development Kit (ADK) includes comprehensive OpenTelemetry (OTEL) integration for distributed tracing and observability. Every agent execution, LLM call, tool execution, and skill application is automatically tracked and can be exported to OTEL-compatible collectors like Jaeger, Zipkin, or Grafana Tempo.

## Features

- **Distributed Tracing**: Complete trace of agent execution flow
- **Span Hierarchy**: Parent-child relationships showing execution dependencies
- **Token Tracking**: Automatic LLM token usage tracking per request
- **Tool Execution**: Detailed tool call timing and results
- **Skill Application**: Track which skills are applied and when
- **Error Tracking**: Automatic error capture with stack traces
- **Performance Metrics**: Duration, token counts, and iteration counts

## Quick Start

### 1. Start Jaeger

The easiest way to get started is with Jaeger all-in-one:

```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

Or use the provided script:
```bash
.\start_otel_docker.cmd
```

### 2. Configure ADK

Update your `.env` file:

```bash
OTEL_ENABLED=true
OTEL_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=adk
LOG_LEVEL=DEBUG
```

### 3. Run Your Agent

```bash
python run.py
```

### 4. View Traces

Open Jaeger UI: http://localhost:16686

- Select service: `adk`
- Click "Find Traces"
- Explore your agent executions!

## Architecture

### Trace Structure

Each agent execution creates a trace with the following span hierarchy:

```
Trace: agent_execution_{agent_id}
├─ Span: agent_{agent_id}_start (SERVER)
   ├─ Span: apply_skills (INTERNAL)
   ├─ Span: llm_call_iter_1 (CLIENT)
   │  └─ Token usage tracked
   ├─ Span: tool_{tool_id} (INTERNAL)
   │  └─ Tool execution details
   ├─ Span: llm_call_iter_2 (CLIENT)
   │  └─ Token usage tracked
   └─ Final response
```

### Span Types

- **AGENT_START**: Agent execution begins
- **AGENT_END**: Agent execution completes
- **LLM_REQUEST**: LLM API call
- **LLM_RESPONSE**: LLM response received
- **TOOL_CALL**: Tool execution
- **TOOL_RESULT**: Tool result returned
- **CUSTOM**: Skill application and other operations

### Span Kinds

- **SERVER**: Entry point (agent execution)
- **CLIENT**: External calls (LLM APIs)
- **INTERNAL**: Internal operations (tools, skills)

## What Gets Tracked

### Agent Execution

**Attributes:**
- `agent_name`: Name of the agent
- `agent_id`: Unique agent identifier
- `llm_provider`: LLM provider (groq, openai, nvidia)
- `llm_model`: Model name
- `user_id`: User making the request (if authenticated)

**Metrics:**
- `duration_ms`: Total execution time
- `total_tokens`: Total tokens used
- `tool_calls`: Number of tool calls made
- `response_length`: Length of final response

### LLM Calls

**Attributes:**
- `provider`: LLM provider
- `model`: Model name
- `iteration`: Which iteration in tool calling loop

**Metrics:**
- `token_count`: Total tokens for this call
- `input_tokens`: Prompt tokens
- `output_tokens`: Completion tokens
- `duration_ms`: API call duration

**Output Data:**
- `finish_reason`: stop, tool_calls, length, etc.
- `message_count`: Number of messages in context

**Span Events (Payloads):**
- `llm_request_payload`: Last message content (first 500 chars), message count, tools count
- `llm_response_payload`: Response content preview (first 500 chars), finish reason, has tool calls

### Tool Execution

**Attributes:**
- `tool_type`: api, python, shell, mcp
- `tool_name`: Human-readable tool name
- `tool_id`: Unique tool identifier

**Input Data:**
- `arguments`: Tool arguments (sanitized)
- `mock`: Whether using mock execution

**Output Data:**
- `result_length`: Size of tool result

**Span Events (Payloads):**
- `tool_result_payload`: Tool result preview (first 1000 chars), result length, tool type

**Errors:**
- `error_message`: Error details if tool fails
- `status`: OK or ERROR

### Skill Application

**Attributes:**
- `skill_count`: Number of skills applied

**Output Data:**
- `skills_applied`: Number of skills successfully applied

## Configuration

### Environment Variables

```bash
# Enable/disable telemetry
OTEL_ENABLED=true

# OTEL collector endpoint (HTTP)
OTEL_ENDPOINT=http://localhost:4318

# Service name in traces
OTEL_SERVICE_NAME=adk

# Export interval (milliseconds)
OTEL_EXPORT_INTERVAL=5000

# Memory limits
OTEL_MAX_TRACES=10000
OTEL_MAX_SPANS=100000
```

### Programmatic Configuration

```python
from app.config import get_settings

settings = get_settings()
settings.otel_enabled = True
settings.otel_endpoint = "http://localhost:4318"
```

## REST API

The telemetry service provides REST endpoints for querying traces:

### List Traces

```bash
GET /telemetry/traces?agent_id=research-agent&limit=10
```

**Query Parameters:**
- `trace_id`: Filter by trace ID
- `agent_id`: Filter by agent ID
- `user_id`: Filter by user ID
- `session_id`: Filter by session ID
- `status`: Filter by status (ok, error, unset)
- `limit`: Number of results (default: 100)
- `offset`: Pagination offset

### Get Specific Trace

```bash
GET /telemetry/traces/{trace_id}
```

Returns complete trace with all spans.

### List Spans

```bash
GET /telemetry/spans?action_type=llm_request&limit=10
```

**Query Parameters:**
- `trace_id`: Filter by trace ID
- `agent_id`: Filter by agent ID
- `action_type`: Filter by action type
- `status`: Filter by status
- `limit`: Number of results
- `offset`: Pagination offset

### Get Statistics

```bash
GET /telemetry/stats
```

Returns aggregated statistics:
- Total traces and spans
- Total errors
- Total tokens used
- Average duration
- Traces by agent
- Traces by status
- Actions by type

### Get Trace Timeline

```bash
GET /telemetry/traces/{trace_id}/timeline
```

Returns chronological timeline of all spans in a trace.

### Force Export

```bash
POST /telemetry/export
```

Forces immediate export of pending spans to OTEL collector.

## Integration Examples

### Custom Telemetry in Your Code

```python
from app.services.telemetry_service import get_telemetry_service
from app.models.telemetry import ActionType, SpanStatus, SpanKind

telemetry = get_telemetry_service()

# Start a trace
trace = telemetry.start_trace(
    name="custom_operation",
    agent_id="my-agent",
    user_id="user123"
)

# Log an action
span = telemetry.log_action(
    trace_id=trace.trace_id,
    action_type=ActionType.CUSTOM,
    name="custom_step",
    input_data={"param": "value"},
    attributes={"custom_attr": "value"},
    kind=SpanKind.INTERNAL
)

# Complete the action
telemetry.complete_action(
    span_id=span.span_id,
    status=SpanStatus.OK,
    output_data={"result": "success"}
)

# End the trace
telemetry.end_trace(trace.trace_id, SpanStatus.OK)
```

### Querying Traces Programmatically

```python
from app.services.telemetry_service import get_telemetry_service
from app.models.telemetry import TraceQueryRequest, SpanStatus

telemetry = get_telemetry_service()

# Query traces
request = TraceQueryRequest(
    agent_id="research-agent",
    status=SpanStatus.OK,
    limit=10
)
response = telemetry.query_traces(request)

for trace in response.traces:
    print(f"Trace: {trace.trace_id}")
    print(f"Duration: {trace.duration_ms}ms")
    print(f"Tokens: {trace.total_tokens}")
    print(f"Spans: {len(trace.spans)}")
```

## Visualization

### Jaeger UI

**Service View:**
- Shows all services reporting traces
- Select "adk" to see ADK traces

**Trace View:**
- Timeline visualization of spans
- Span hierarchy with parent-child relationships
- Detailed span information
- Tag and log viewing

**Search:**
- Filter by service, operation, tags
- Time range selection
- Duration filters
- Tag-based queries

### Grafana Tempo

For production environments, consider Grafana Tempo:

```yaml
# docker-compose.yml
services:
  tempo:
    image: grafana/tempo:latest
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
      - ./tempo-data:/tmp/tempo
    ports:
      - "4318:4318"   # OTLP HTTP
      - "3200:3200"   # Tempo API

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
```

## Best Practices

### 1. Use Meaningful Trace Names

```python
# Good
trace = telemetry.start_trace(name=f"agent_execution_{agent.id}")

# Bad
trace = telemetry.start_trace(name="trace")
```

### 2. Add Context with Attributes

```python
span = telemetry.log_action(
    trace_id=trace_id,
    action_type=ActionType.LLM_REQUEST,
    name="llm_call",
    attributes={
        "provider": "groq",
        "model": "llama3-70b",
        "temperature": 0.7,
        "max_tokens": 2048
    }
)
```

### 3. Track Token Usage

```python
telemetry.complete_action(
    span_id=span.span_id,
    status=SpanStatus.OK,
    token_count=response["usage"]["total_tokens"],
    output_data={"finish_reason": "stop"}
)
```

### 4. Handle Errors Properly

```python
try:
    result = await some_operation()
    telemetry.complete_action(span_id, SpanStatus.OK)
except Exception as e:
    telemetry.complete_action(
        span_id=span_id,
        status=SpanStatus.ERROR,
        error_message=str(e)
    )
    raise
```

### 5. Use Span Hierarchy

```python
# Parent span
agent_span = telemetry.log_action(
    trace_id=trace_id,
    action_type=ActionType.AGENT_START,
    name="agent_execution"
)

# Child span
tool_span = telemetry.log_action(
    trace_id=trace_id,
    parent_span_id=agent_span.span_id,  # Link to parent
    action_type=ActionType.TOOL_CALL,
    name="web_search"
)
```

## Troubleshooting

### No Traces Appearing in Jaeger

1. **Check OTEL is enabled:**
   ```bash
   grep OTEL_ENABLED .env
   # Should show: OTEL_ENABLED=true
   ```

2. **Verify Jaeger is running:**
   ```bash
   docker ps | grep jaeger
   curl http://localhost:16686
   ```

3. **Check endpoint configuration:**
   ```bash
   grep OTEL_ENDPOINT .env
   # Should show: OTEL_ENDPOINT=http://localhost:4318
   ```

4. **Check logs for export errors:**
   ```bash
   # Look for telemetry service logs
   grep "telemetry" logs/adk.log
   ```

### Traces Not Exporting

1. **Force export:**
   ```bash
   curl -X POST http://localhost:8100/telemetry/export
   ```

2. **Check export interval:**
   - Default is 5000ms (5 seconds)
   - Traces export automatically on interval

3. **Check memory limits:**
   - If limits exceeded, old traces are dropped
   - Increase `OTEL_MAX_TRACES` and `OTEL_MAX_SPANS`

### High Memory Usage

1. **Reduce retention:**
   ```bash
   OTEL_MAX_TRACES=1000
   OTEL_MAX_SPANS=10000
   ```

2. **Increase export frequency:**
   ```bash
   OTEL_EXPORT_INTERVAL=1000  # Export every second
   ```

3. **Disable telemetry if not needed:**
   ```bash
   OTEL_ENABLED=false
   ```

## Performance Impact

- **Overhead**: ~1-2% CPU overhead for telemetry collection
- **Memory**: ~10-50MB depending on trace volume
- **Network**: Minimal - batched exports every 5 seconds
- **Storage**: Jaeger handles trace storage and retention

## Security Considerations

1. **Sensitive Data**: Input/output data is captured in spans
   - Sanitize sensitive information before logging
   - Use attributes for metadata, not full payloads

2. **Authentication**: Telemetry endpoints support JWT authentication
   - Protect production telemetry data
   - Use read-only access for viewers

3. **Network**: OTEL endpoint should be secured
   - Use HTTPS in production
   - Restrict access to telemetry collector

## Advanced Topics

### Custom Exporters

Implement custom exporters for other backends:

```python
from app.services.telemetry_service import TelemetryService

class CustomExporter:
    async def export(self, spans):
        # Send to custom backend
        pass

telemetry = TelemetryService()
telemetry.add_exporter(CustomExporter())
```

### Sampling

Reduce trace volume with sampling:

```python
# Sample 10% of traces
if random.random() < 0.1:
    trace = telemetry.start_trace(...)
```

### Context Propagation

Propagate trace context across services:

```python
# Extract context
trace_id = trace.trace_id

# Propagate in HTTP headers
headers = {
    "traceparent": f"00-{trace_id}-{span_id}-01"
}

# Inject in downstream service
response = await client.post(url, headers=headers)
```

## Resources

- **Jaeger Documentation**: https://www.jaegertracing.io/docs/
- **OpenTelemetry Specification**: https://opentelemetry.io/docs/
- **Grafana Tempo**: https://grafana.com/oss/tempo/
- **OTLP Protocol**: https://opentelemetry.io/docs/specs/otlp/

## Support

For issues or questions:
1. Check logs: `logs/adk.log`
2. Verify configuration: `.env` file
3. Test connectivity: `curl http://localhost:4318/v1/traces`
4. Review documentation: This file and Jaeger docs
