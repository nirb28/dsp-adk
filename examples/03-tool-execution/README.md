# Example 03: Tool Execution Demo

This example demonstrates the different tool execution modes in the ADK:
- Mock tool execution (no external dependencies)
- Real tool execution (API, Python, Shell)
- Disabled tools (direct LLM response)

## Prerequisites

1. **ADK Server Running**
   ```bash
   python -m app.main
   ```

2. **Environment Variables** (for real execution)
   ```bash
   # LLM Configuration
   export LLM_PROVIDER=groq
   export LLM_MODEL=llama-3.3-70b-versatile
   export LLM_ENDPOINT=https://api.groq.com/openai/v1
   export GROQ_API_KEY=your_groq_api_key
   
   # Optional: API Tool Configuration
   export SEARCH_API_ENDPOINT=https://api.example.com/search
   export SEARCH_API_KEY=your_search_api_key
   ```

## Running the Example

```bash
cd examples/03-tool-execution
python run.py
```

## What This Example Shows

### Demo 1: Mock Tool Execution
- Uses `mock_tools=True`
- No API keys or external dependencies required
- Perfect for testing and demonstrations
- Returns predefined mock responses

### Demo 2: Real Tool Execution
- Uses `mock_tools=False`
- Calls actual API endpoints
- Requires proper configuration
- Production-ready execution

### Demo 3: Python Tool Execution
- Demonstrates Python function calls
- Shows how to create custom Python tools
- Real execution without external APIs

### Demo 4: Disabled Tools
- Uses `use_tools=False`
- Agent responds without calling any tools
- Fastest execution mode

## Tool Types Supported

### 1. API Tools (`tool_type: api`)
Make HTTP requests to external APIs.

**Configuration:**
```yaml
id: web-search
tool_type: api
implementation:
  endpoint: ${SEARCH_API_ENDPOINT}
  method: GET
  headers:
    Authorization: Bearer ${SEARCH_API_KEY}
  query_params:
    q: "{{query}}"
    count: "{{num_results}}"
```

### 2. Python Tools (`tool_type: python`)
Call Python functions directly.

**Configuration:**
```yaml
id: text-processor
tool_type: python
implementation:
  module: tools.text_utils
  function: summarize_text
```

**Python Function:**
```python
# tools/text_utils.py
def summarize_text(text: str, max_length: int = 100) -> dict:
    return {
        "summary": text[:max_length],
        "original_length": len(text)
    }
```

### 3. Shell Tools (`tool_type: shell`)
Execute shell commands.

**Configuration:**
```yaml
id: file-info
tool_type: shell
implementation:
  command: "ls -lh {{filepath}}"
```

**Security Warning:** Shell tools should be used with caution. Always validate inputs.

### 4. MCP Tools (`tool_type: mcp`)
Integrate with Model Context Protocol servers.

**Status:** Coming soon

## Request Parameters

```json
{
  "message": "Your query here",
  "use_tools": true,           // Enable/disable tool calling
  "mock_tools": false,          // Use mock or real execution
  "max_tool_iterations": 5      // Maximum tool calling loops
}
```

## Creating Custom Tools

### Step 1: Create Python Function
```python
# tools/my_tools.py
def my_function(param1: str, param2: int) -> dict:
    return {
        "result": f"Processed {param1} with {param2}"
    }
```

### Step 2: Create Tool Configuration
```yaml
# data/tools/my-tool.yaml
id: my-tool
name: My Custom Tool
tool_type: python

parameters:
  - name: param1
    type: string
    required: true
  - name: param2
    type: integer
    required: false
    default: 10

implementation:
  module: tools.my_tools
  function: my_function

jwt_required: false
```

### Step 3: Add to Agent
```yaml
# data/agents/my-agent.yaml
tools:
  - my-tool
```

## Testing Strategy

1. **Start with Mock Mode**
   ```json
   {"mock_tools": true}
   ```
   - Test agent behavior
   - Verify tool calling logic
   - No external dependencies

2. **Test Without Tools**
   ```json
   {"use_tools": false}
   ```
   - Verify basic agent functionality
   - Baseline performance

3. **Enable Real Execution**
   ```json
   {"mock_tools": false}
   ```
   - Test with real APIs
   - Verify error handling
   - Production testing

## Troubleshooting

### Tools Not Being Called
- Check `use_tools: true` in request
- Verify tools are listed in agent YAML
- Ensure tools are enabled (`enabled: true`)
- Check tool descriptions are clear

### API Tool Errors
- Verify environment variables are set
- Check API endpoint is accessible
- Review API key permissions
- Check rate limits

### Python Tool Errors
- Ensure module is importable
- Verify function signature matches parameters
- Check for missing dependencies
- Review function error handling

### Shell Tool Errors
- Validate command syntax
- Check file permissions
- Verify paths exist
- Review timeout settings

## Best Practices

1. **Always start with mock mode** for initial testing
2. **Use environment variables** for API keys and endpoints
3. **Set appropriate timeouts** for all tools
4. **Validate inputs** especially for shell tools
5. **Handle errors gracefully** in tool functions
6. **Keep Python functions pure** when possible
7. **Monitor tool_calls_made** to understand agent behavior
8. **Test error scenarios** with invalid inputs

## See Also

- [Tool Invocation Documentation](../../TOOL_INVOCATION.md)
- [Agent Execution Guide](../../AGENT_EXECUTION.md)
- [Example 01: Simple Q&A](../01-simple-qa/)
- [Example 02: Research with Tools](../02-research-with-tools/)
