# API Tool Execution Guide

## Yes, Tools Can Be Executed with API Calls!

The ADK fully supports **real API tool execution**. When you set `mock_tools=false`, the system makes actual HTTP requests to external APIs.

## How API Tools Work

### 1. Tool Configuration

API tools are defined in YAML with `tool_type: api`:

```yaml
id: web-search
name: Web Search Tool
tool_type: api

parameters:
  - name: query
    type: string
    required: true
  - name: num_results
    type: integer
    required: false
    default: 5

implementation:
  endpoint: ${SEARCH_API_ENDPOINT}
  method: GET
  headers:
    Authorization: Bearer ${SEARCH_API_KEY}
  query_params:
    q: "{{query}}"
    count: "{{num_results}}"

timeout: 15
retry_count: 2
```

### 2. Environment Variables

Set up your API credentials:

```bash
# .env file
SEARCH_API_ENDPOINT=https://api.example.com/search
SEARCH_API_KEY=your_api_key_here
```

### 3. Template Substitution

The system supports two types of variable substitution:

**Environment Variables** (`${VAR}`) - Resolved at tool load time:
```yaml
endpoint: ${SEARCH_API_ENDPOINT}
headers:
  Authorization: Bearer ${SEARCH_API_KEY}
```

**Parameter Variables** (`{{param}}`) - Replaced at execution time:
```yaml
query_params:
  q: "{{query}}"
  count: "{{num_results}}"
```

### 4. HTTP Methods Supported

- **GET**: Query parameters in URL
- **POST**: JSON body + query parameters
- **PUT**: JSON body + query parameters  
- **DELETE**: Query parameters in URL

### 5. Request Flow

```
Agent decides to call tool
    ↓
Executor loads tool config
    ↓
Substitutes {{parameters}} with actual values
    ↓
Makes HTTP request to endpoint
    ↓
Parses JSON response
    ↓
Returns result to LLM
    ↓
LLM uses result to formulate answer
```

## Testing API Tools

### Option 1: Use HTTPBin (No API Key Required)

We've created a test tool that uses httpbin.org:

```yaml
# data/tools/generic/httpbin-test.yaml
id: httpbin-test
tool_type: api
implementation:
  endpoint: https://httpbin.org/post
  method: POST
```

**Test it:**
```bash
# Add to agent's tools list
tools:
  - httpbin-test

# Run with mock_tools=false
{
  "message": "Test the httpbin tool with data 'hello world'",
  "use_tools": true,
  "mock_tools": false
}
```

### Option 2: Use Your Own API

1. **Configure the endpoint:**
```yaml
implementation:
  endpoint: https://your-api.com/endpoint
  method: POST
  headers:
    Authorization: Bearer ${YOUR_API_KEY}
  body:
    query: "{{query}}"
```

2. **Set environment variables:**
```bash
export YOUR_API_KEY=your_key_here
```

3. **Test:**
```json
{
  "message": "Call the API with query 'test'",
  "use_tools": true,
  "mock_tools": false
}
```

## Common API Patterns

### REST API with Bearer Token
```yaml
implementation:
  endpoint: https://api.example.com/v1/search
  method: GET
  headers:
    Authorization: Bearer ${API_KEY}
    Content-Type: application/json
  query_params:
    q: "{{query}}"
```

### REST API with API Key in Query
```yaml
implementation:
  endpoint: https://api.example.com/search
  method: GET
  query_params:
    apikey: ${API_KEY}
    query: "{{query}}"
```

### POST with JSON Body
```yaml
implementation:
  endpoint: https://api.example.com/analyze
  method: POST
  headers:
    Authorization: Bearer ${API_KEY}
    Content-Type: application/json
  body:
    text: "{{text}}"
    options:
      language: "{{language}}"
      max_length: "{{max_length}}"
```

### GraphQL API
```yaml
implementation:
  endpoint: https://api.example.com/graphql
  method: POST
  headers:
    Authorization: Bearer ${API_KEY}
    Content-Type: application/json
  body:
    query: "{{graphql_query}}"
    variables: "{{variables}}"
```

## Troubleshooting

### Tools Not Being Called (Tool Calls: 0)

**Issue:** LLM isn't calling the tools even with `use_tools=true`

**Solutions:**
1. Check tool field name is `tool_type` not `type` in YAML
2. Verify tools are listed in agent's `tools:` array
3. Ensure tools are enabled (`enabled: true` or omitted)
4. Make tool descriptions clear so LLM knows when to use them
5. Check LLM supports function calling (Groq, OpenAI, etc.)

### API Request Fails

**Issue:** Tool execution returns error

**Solutions:**
1. Verify endpoint URL is correct
2. Check API key is set in environment
3. Test endpoint with curl first
4. Review API rate limits
5. Check timeout settings
6. Verify request format matches API docs

### Environment Variables Not Resolved

**Issue:** Seeing `${VAR_NAME}` in requests

**Solutions:**
1. Set variables in `.env` file
2. Restart ADK server after changing `.env`
3. Check variable names match exactly
4. Verify `.env` is in project root

### Template Variables Not Substituted

**Issue:** Seeing `{{param}}` in requests

**Solutions:**
1. Check parameter names match tool definition
2. Verify LLM is passing correct arguments
3. Review tool parameter schema
4. Check for typos in template names

## Example: Real Web Search Tool

Here's a complete example using a real search API:

### 1. Tool Configuration
```yaml
# data/tools/web-search.yaml
id: web-search
name: Web Search Tool
description: Search the web for current information
tool_type: api

parameters:
  - name: query
    type: string
    description: Search query
    required: true
  - name: num_results
    type: integer
    description: Number of results (1-10)
    required: false
    default: 5

implementation:
  endpoint: ${SEARCH_API_ENDPOINT}
  method: GET
  headers:
    Authorization: Bearer ${SEARCH_API_KEY}
  query_params:
    q: "{{query}}"
    count: "{{num_results}}"

timeout: 15
retry_count: 2
jwt_required: false
```

### 2. Environment Setup
```bash
# .env
SEARCH_API_ENDPOINT=https://api.search-provider.com/v1/search
SEARCH_API_KEY=your_search_api_key_here
```

### 3. Agent Configuration
```yaml
# data/agents/research-agent.yaml
tools:
  - web-search
```

### 4. Test Request
```json
{
  "message": "What are the latest developments in quantum computing?",
  "use_tools": true,
  "mock_tools": false,
  "max_tool_iterations": 3
}
```

### 5. Expected Flow
1. Agent receives query
2. Decides to call `web-search` tool
3. Executor makes GET request to search API
4. API returns search results
5. Agent analyzes results
6. Agent formulates response with sources

## Mock vs Real Execution

| Feature | Mock Mode | Real Mode |
|---------|-----------|-----------|
| API Key Required | ❌ No | ✅ Yes |
| Network Access | ❌ No | ✅ Yes |
| Real Data | ❌ No | ✅ Yes |
| Testing | ✅ Perfect | ⚠️ Use sparingly |
| Cost | 💰 Free | 💰 May incur costs |
| Speed | ⚡ Instant | 🐌 Network latency |

## Best Practices

1. **Start with Mock**: Always test with `mock_tools=true` first
2. **Use Environment Variables**: Never hardcode API keys
3. **Set Timeouts**: Prevent hanging on slow APIs
4. **Handle Errors**: APIs can fail, return errors gracefully
5. **Rate Limiting**: Respect API rate limits
6. **Retry Logic**: Use `retry_count` for transient failures
7. **Validate Responses**: Check API response format
8. **Monitor Usage**: Track API calls and costs
9. **Cache Results**: Consider caching for repeated queries
10. **Security**: Use HTTPS endpoints only

## Next Steps

1. ✅ Fix `tool_type` field in your tool YAML files
2. ✅ Set up environment variables for your APIs
3. ✅ Test with `httpbin-test` tool (no API key needed)
4. ✅ Configure your real API endpoints
5. ✅ Test with `mock_tools=false`
6. ✅ Monitor tool execution in logs
7. ✅ Implement error handling for production

## See Also

- [Tool Invocation Documentation](./TOOL_INVOCATION.md)
- [Agent Execution Guide](./AGENT_EXECUTION.md)
- [Example 03: Tool Execution](./examples/03-tool-execution/)
