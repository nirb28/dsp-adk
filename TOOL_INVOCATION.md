# Tool Invocation

The ADK now supports real tool invocation during agent execution. Agents can call configured tools through OpenAI-compatible function calling, with the ability to enable/disable tool usage per request.

## Features

- **OpenAI Function Calling**: Automatic conversion of ADK tools to OpenAI function format
- **Multi-Turn Execution**: Agents can make multiple tool calls in a single conversation
- **Enable/Disable Control**: Turn tool calling on/off per request
- **Iteration Limits**: Configurable maximum tool calling iterations
- **Real Tool Execution**: Support for API, Python, Shell, and MCP tool types
- **Mock Mode**: Optional mock responses for testing without real execution
- **Usage Tracking**: Token usage accumulation across all tool calling iterations
- **Template Substitution**: Dynamic variable substitution in tool configurations

## How It Works

1. **Agent Configuration**: Agents specify which tools they can use in their YAML
2. **Tool Loading**: Executor loads tool configurations when `use_tools=True`
3. **Function Conversion**: Tools are converted to OpenAI function calling format
4. **LLM Decision**: LLM decides whether to call tools based on user query
5. **Tool Execution**: Executor runs the tool and returns results
6. **Multi-Turn Loop**: LLM receives tool results and can make more calls or respond
7. **Final Response**: After all tool calls, LLM provides final answer to user

## API Usage

### Enable Tool Calling with Real Execution (Default)

```bash
curl -X POST http://localhost:8100/agents/research-agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the latest developments in quantum computing?",
    "use_tools": true,
    "max_tool_iterations": 5,
    "mock_tools": false
  }'
```

### Enable Tool Calling with Mock Responses

```bash
curl -X POST http://localhost:8100/agents/research-agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the latest developments in quantum computing?",
    "use_tools": true,
    "max_tool_iterations": 5,
    "mock_tools": true
  }'
```

### Disable Tool Calling

```bash
curl -X POST http://localhost:8100/agents/research-agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the latest developments in quantum computing?",
    "use_tools": false
  }'
```

## Request Parameters

- **`use_tools`** (bool, default: `true`): Enable/disable tool calling
- **`max_tool_iterations`** (int, default: `5`): Maximum number of tool calling loops
- **`mock_tools`** (bool, default: `false`): Use mock responses instead of real execution

## Response Metadata

Responses now include:

```json
{
  "success": true,
  "response": "Based on my research...",
  "usage": {
    "prompt_tokens": 450,
    "completion_tokens": 200,
    "total_tokens": 650
  },
  "model": "llama-3.3-70b-versatile",
  "provider": "groq",
  "duration_seconds": 3.45,
  "tool_calls_made": 2,
  "agent_id": "research-agent",
  "agent_name": "Research Agent"
}
```

The `tool_calls_made` field shows how many tool calling iterations occurred.

## Agent Configuration

Agents specify tools in their YAML:

```yaml
id: research-agent
name: Research Agent
description: A research agent with tool access

llm:
  provider: groq
  model: llama-3.3-70b-versatile
  temperature: 0.3

tools:
  - web-search
  - text-processor
  - vector-search

capabilities:
  - tool_calling
  - multi_turn
```

## Tool Configuration

Tools must be properly configured with parameters:

```yaml
id: web-search
name: Web Search Tool
description: Search the web for information

parameters:
  - name: query
    type: string
    description: The search query
    required: true
  - name: num_results
    type: integer
    description: Number of results (1-10)
    required: false
    default: 5

jwt_required: false
```

## OpenAI Function Format

Tools are automatically converted to OpenAI function calling format:

```json
{
  "type": "function",
  "function": {
    "name": "web-search",
    "description": "Search the web for information",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The search query"
        },
        "num_results": {
          "type": "integer",
          "description": "Number of results (1-10)"
        }
      },
      "required": ["query"]
    }
  }
}
```

## Python Client Example

```python
import httpx
import asyncio

async def run_agent_with_tools():
    async with httpx.AsyncClient(base_url="http://localhost:8100") as client:
        response = await client.post(
            "/agents/research-agent/run",
            json={
                "message": "Research quantum computing breakthroughs in 2024",
                "use_tools": True,
                "max_tool_iterations": 5
            }
        )
        result = response.json()
        print(f"Response: {result['response']}")
        print(f"Tool calls made: {result['tool_calls_made']}")
        print(f"Total tokens: {result['usage']['total_tokens']}")

asyncio.run(run_agent_with_tools())
```

## Execution Flow

```
User Query
    ↓
Agent Executor
    ↓
Load Tools (if use_tools=True)
    ↓
Convert to OpenAI Functions
    ↓
┌─────────────────────────────┐
│  LLM Call with Functions    │
│  (Iteration 1)              │
└─────────────────────────────┘
    ↓
Tool Call Needed?
    ├─ No → Return Response
    └─ Yes
        ↓
    Execute Tool(s)
        ↓
    Add Results to Conversation
        ↓
┌─────────────────────────────┐
│  LLM Call with Tool Results │
│  (Iteration 2)              │
└─────────────────────────────┘
    ↓
Tool Call Needed?
    ├─ No → Return Response
    └─ Yes → Repeat (up to max_tool_iterations)
```

## Tool Execution Types

The ADK supports multiple tool execution types:

### 1. API Tools (`tool_type: api`)

Make HTTP requests to external APIs:

```yaml
id: web-search
tool_type: api
implementation:
  endpoint: https://api.example.com/search
  method: GET
  headers:
    Authorization: Bearer ${SEARCH_API_KEY}
  query_params:
    q: "{{query}}"
    count: "{{num_results}}"
```

**Features:**
- Template variable substitution: `{{parameter_name}}`
- Environment variable resolution: `${ENV_VAR}`
- Support for GET, POST, PUT, DELETE methods
- Custom headers and query parameters
- Request body support for POST/PUT
- Automatic JSON response parsing

### 2. Python Tools (`tool_type: python`)

Call Python functions directly:

```yaml
id: text-processor
tool_type: python
implementation:
  module: tools.text_utils
  function: summarize_text
```

**Features:**
- Dynamic module imports
- Function arguments passed as kwargs
- Return values automatically serialized to JSON
- Support for template substitution in function names

**Example Python Function:**
```python
# tools/text_utils.py
def summarize_text(text: str, max_length: int = 100) -> dict:
    return {
        "summary": text[:max_length],
        "original_length": len(text)
    }
```

### 3. Shell Tools (`tool_type: shell`)

Execute shell commands:

```yaml
id: file-info
tool_type: shell
implementation:
  command: "ls -lh {{filepath}}"
```

**Features:**
- Template variable substitution in commands
- Captures stdout, stderr, and return code
- Configurable timeout
- Security: Use with caution, validate inputs

### 4. MCP Tools (`tool_type: mcp`)

Integrate with Model Context Protocol servers:

```yaml
id: mcp-tool
tool_type: mcp
implementation:
  mcp_server_id: my-mcp-server
  tool_name: search_documents
```

**Status:** Placeholder implementation (coming soon)

### 5. Mock Mode

When `mock_tools: true`, all tools return predefined mock responses:

```json
{
  "results": [
    {
      "title": "Result 1 for: quantum computing",
      "url": "https://example.com/result1",
      "snippet": "This is a snippet about quantum computing..."
    }
  ]
}
```

**Use Cases:**
- Testing without API keys
- Development without external dependencies
- Demos and presentations
- CI/CD pipelines

## Template Variable Substitution

Tools support dynamic variable substitution using `{{variable}}` syntax:

**In API endpoints:**
```yaml
endpoint: https://api.example.com/search?q={{query}}&limit={{num_results}}
```

**In headers:**
```yaml
headers:
  X-User-ID: "{{user_id}}"
```

**In function names:**
```yaml
function: "{{operation}}_text"  # Becomes summarize_text, count_words, etc.
```

**In shell commands:**
```yaml
command: "cat {{filepath}} | grep {{pattern}}"
```

## Environment Variable Resolution

Use `${ENV_VAR}` syntax for environment variables:

```yaml
endpoint: ${SEARCH_API_ENDPOINT}
headers:
  Authorization: Bearer ${SEARCH_API_KEY}
```

Variables are resolved when the tool configuration is loaded.

## Future Enhancements

- [x] Real tool execution for API, Python, Shell types
- [x] Mock mode for testing
- [x] Template variable substitution
- [ ] Tool execution caching
- [ ] Parallel tool execution
- [ ] Tool execution permissions and sandboxing
- [ ] Enhanced tool execution logging and auditing
- [ ] MCP tool integration
- [ ] Tool result validation and schema enforcement
- [ ] Retry logic with exponential backoff

## Controlling Tool Execution

You can control tool execution in several ways:

### 1. Disable All Tools (Per Request)
```json
{
  "message": "Hello",
  "use_tools": false
}
```

### 2. Use Mock Responses (Per Request)
```json
{
  "message": "Research quantum computing",
  "use_tools": true,
  "mock_tools": true
}
```

### 3. Disable Tools for Agent (in YAML)
```yaml
tools: []  # Empty tools list
```

### 4. Disable Individual Tool (in YAML)
```yaml
id: web-search
enabled: false  # Disable the tool
```

## Error Handling

Tool execution errors are returned to the LLM:

```json
{
  "error": "Tool 'web-search' not found"
}
```

The LLM can then decide how to handle the error (retry, use different tool, or inform user).

## Token Usage

Token usage is accumulated across all iterations:

- **Iteration 1**: 100 prompt + 50 completion = 150 total
- **Iteration 2**: 200 prompt + 30 completion = 230 total
- **Final Usage**: 300 prompt + 80 completion = 380 total

## Best Practices

1. **Set Reasonable Limits**: Use `max_tool_iterations` to prevent infinite loops
2. **Tool Selection**: Only include tools the agent actually needs
3. **Tool Descriptions**: Write clear descriptions so LLM knows when to use each tool
4. **Error Handling**: Tools should return meaningful error messages in JSON format
5. **Testing**: 
   - Start with `mock_tools=true` to test flow without dependencies
   - Then test with `use_tools=false` to verify basic agent functionality
   - Finally enable real execution with `mock_tools=false`
6. **Security**:
   - Validate all inputs for shell tools
   - Use environment variables for API keys, never hardcode
   - Set appropriate timeouts for all tools
   - Review shell commands for injection vulnerabilities
7. **Monitoring**: Track `tool_calls_made` to understand agent behavior
8. **API Tools**: Always handle rate limits and implement retry logic
9. **Python Tools**: Keep functions pure and stateless when possible

## Troubleshooting

### Agent Not Calling Tools

- Verify tools are listed in agent YAML
- Check tools are enabled (`enabled: true`)
- Ensure `use_tools: true` in request
- Verify tool descriptions are clear
- Check LLM supports function calling (most do)

### Too Many Tool Calls

- Reduce `max_tool_iterations`
- Improve tool descriptions
- Add more context to user message
- Check for tool execution errors

### Tool Execution Fails

- Verify tool configuration is valid
- Check tool parameters match schema
- Review server logs for errors
- Test tool independently

## See Also

- [Agent Execution](./AGENT_EXECUTION.md) - Basic agent execution
- [Tool Configuration](./data/tools/) - Tool YAML examples
- [API Documentation](http://localhost:8100/docs) - Interactive API docs
