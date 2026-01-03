# Telemetry Integration Fixes

## Issues Identified

Based on the Jaeger trace provided, the telemetry system had the following issues:

1. **Missing Input/Output Data**: The `input_data` and `output_data` fields were being set in spans but not exported to OTLP format
2. **Incorrect Event Timestamps**: Events were using `datetime.now()` instead of the actual event timestamp
3. **Incomplete Tool Call Tracking**: Tool calls weren't being captured with full details in span events
4. **Limited Payload Visibility**: LLM request/response payloads weren't showing complete information about tool calls

## Changes Made

### 1. Enhanced OTLP Conversion (`app/services/telemetry_service.py`)

**Added comprehensive attribute export:**
- Now exports `adk.input_data` as JSON string for full visibility
- Now exports `adk.output_data` as JSON string for full visibility
- Added `adk.input_tokens` and `adk.output_tokens` attributes
- Properly serializes complex data structures

**Fixed event timestamp parsing:**
- Added `_parse_event_timestamp()` method to parse ISO format timestamps
- Uses `python-dateutil` for robust timestamp parsing
- Falls back to current time if parsing fails

**Before:**
```python
"events": [
    {
        "name": e.get("name", "event"),
        "timeUnixNano": int(datetime.now(timezone.utc).timestamp() * 1e9),  # WRONG!
        "attributes": self._dict_to_otlp_attributes(e.get("attributes", {}))
    }
    for e in span.events
]
```

**After:**
```python
"events": [
    {
        "name": e.get("name", "event"),
        "timeUnixNano": self._parse_event_timestamp(e.get("timestamp")),  # CORRECT!
        "attributes": self._dict_to_otlp_attributes(e.get("attributes", {}))
    }
    for e in span.events
]
```

### 2. Enhanced Tool Call Telemetry (`app/services/agent_executor.py`)

**Added detailed LLM request logging:**
- Now includes `tools_available` list showing which tools are available
- Captures tool names from the tools array

**Enhanced LLM response logging:**
- Added `tool_calls_count` to show how many tool calls were made
- Added `tool_calls_summary` with detailed information:
  - Tool call ID
  - Function name
  - Arguments preview (first 200 chars)
- Changed `has_tool_calls` to check actual array length instead of key existence

**Added tool call detection event:**
- New span event `tool_calls_detected` when LLM requests tool execution
- Captures tool names and iteration number
- Provides clear visibility into when tools are being invoked

**Enhanced tool execution logging:**
- Added detailed argument logging
- Added result length tracking
- Better error messages

### 3. Added Missing Dependency

Added `python-dateutil>=2.8.2` to `requirements.txt` for timestamp parsing.

## Expected Improvements

After these fixes, Jaeger traces will show:

### 1. Full Input/Output Data
```json
{
  "adk.input_data": "{\"message\": \"What are the latest developments...\", \"use_tools\": true}",
  "adk.output_data": "{\"response_length\": 1234, \"tool_calls\": 2}"
}
```

### 2. Detailed Tool Call Information

**LLM Response Event:**
```json
{
  "event": "llm_response_payload",
  "attributes": {
    "has_tool_calls": true,
    "tool_calls_count": 2,
    "tool_calls_summary": "[{\"id\":\"call_abc\",\"function\":\"web-search\",\"args_preview\":\"{\\\"query\\\":\\\"quantum computing 2024\\\"}\"}]"
  }
}
```

**Tool Calls Detected Event:**
```json
{
  "event": "tool_calls_detected",
  "attributes": {
    "tool_calls_count": 2,
    "tool_names": "[\"web-search\", \"text-processor\"]",
    "iteration": 1
  }
}
```

### 3. Individual Tool Execution Spans

Each tool call now creates a separate span with:
- `ActionType.TOOL_CALL`
- Full input arguments in `adk.input_data`
- Tool result in span event `tool_result_payload`
- Result length and type in `adk.output_data`

## Testing the Fixes

### 1. Install Updated Dependencies

```bash
cd d:\ds\work\workspace\git\dsp-adk
pip install -r requirements.txt
```

### 2. Run Agent with Tools

```bash
# Make sure Jaeger is running
# Then execute an agent that uses tools
python examples/02-research-with-tools/run.py
```

### 3. Check Jaeger UI

Navigate to Jaeger UI and look for:

1. **Agent Start Span** - Should now show:
   - `adk.input_data` with full message and parameters
   - `adk.output_data` with response length and tool call count

2. **LLM Call Spans** - Should now show events:
   - `llm_request_payload` with tools_available list
   - `llm_response_payload` with tool_calls_summary
   - `tool_calls_detected` (if tools were called)

3. **Tool Call Spans** - Should now show:
   - `adk.input_data` with full tool arguments
   - `tool_result_payload` event with result preview
   - `adk.output_data` with result metadata

### 4. Verify Complete Trace

A complete trace with tool calls should look like:

```
agent_research-agent_start (SPAN)
├── adk.input_data: {"message": "...", "use_tools": true}
├── adk.output_data: {"response_length": 1234, "tool_calls": 2}
│
├── llm_call_iter_1 (SPAN)
│   ├── Event: llm_request_payload
│   │   └── tools_available: ["web-search", "text-processor"]
│   ├── Event: llm_response_payload
│   │   ├── has_tool_calls: true
│   │   ├── tool_calls_count: 2
│   │   └── tool_calls_summary: [...]
│   └── Event: tool_calls_detected
│       ├── tool_calls_count: 2
│       └── tool_names: ["web-search", "text-processor"]
│
├── tool_web-search (SPAN)
│   ├── adk.input_data: {"query": "quantum computing 2024", "num_results": 5}
│   ├── Event: tool_result_payload
│   │   └── result_preview: "{\"results\": [...]}"
│   └── adk.output_data: {"result_length": 523}
│
├── tool_text-processor (SPAN)
│   ├── adk.input_data: {"text": "...", "operation": "summarize"}
│   ├── Event: tool_result_payload
│   │   └── result_preview: "{\"result\": \"...\"}"
│   └── adk.output_data: {"result_length": 234}
│
└── llm_call_iter_2 (SPAN)
    └── Event: llm_response_payload
        └── has_tool_calls: false
```

## Troubleshooting

### Issue: Still not seeing tool calls

**Check:**
1. Are tools actually being called? Look for `finish_reason: "tool_calls"` in logs
2. Is the LLM hitting token limits? Check `finish_reason: "length"` - this means the response was truncated
3. Are tools enabled? Verify `use_tools=true` in the request

### Issue: Events showing wrong timestamps

**Check:**
1. Is `python-dateutil` installed? Run `pip list | grep dateutil`
2. Are events being created with timestamp field? Check the `add_span_event()` calls

### Issue: Input/output data not showing

**Check:**
1. Is the data being passed to `log_action()`? Check the `input_data` and `output_data` parameters
2. Is the OTLP export succeeding? Check logs for `[TELEMETRY] Successfully exported`

## Key Improvements Summary

✅ **Full payload visibility** - Input/output data now exported to Jaeger  
✅ **Accurate timestamps** - Events use correct timestamps instead of export time  
✅ **Tool call tracking** - Complete visibility into tool invocations  
✅ **Better debugging** - Rich span events with detailed information  
✅ **Proper span hierarchy** - Tool calls properly nested under agent execution  

## Note on Your Original Trace

The trace you provided showed `finish_reason: "length"`, which means the LLM hit the max_tokens limit and didn't actually make tool calls. The response was truncated before the LLM could request tools. To see tool calls:

1. Increase `max_tokens` in the LLM config
2. Use a simpler query that requires fewer tokens
3. Check that the system prompt isn't too long

The fixes ensure that **when tool calls do occur**, they will be properly captured and visible in Jaeger.
