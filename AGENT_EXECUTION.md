# Agent Execution

The ADK now supports full agent execution with LLM integration. Agents can be run through REST API endpoints with support for both synchronous and streaming responses.

## Features

- **Multiple LLM Providers**: OpenAI, Groq, NVIDIA, Anthropic (OpenAI-compatible)
- **Synchronous Execution**: Get complete responses in one request
- **Streaming Responses**: Server-Sent Events (SSE) for real-time streaming
- **Context & History**: Pass conversation context and history
- **Parameter Overrides**: Override temperature, max_tokens per request
- **Authentication**: JWT-based access control per agent

## API Endpoints

### Run Agent (Synchronous)

```http
POST /agents/{agent_id}/run
```

**Request Body:**
```json
{
  "message": "What is the capital of France?",
  "context": {
    "user_location": "Paris",
    "language": "en"
  },
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help you?"}
  ],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Response:**
```json
{
  "success": true,
  "response": "The capital of France is Paris...",
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 12,
    "total_tokens": 57
  },
  "model": "gpt-4",
  "provider": "openai",
  "duration_seconds": 1.23,
  "timestamp": "2025-12-26T18:45:00Z",
  "agent_id": "conversational-assistant",
  "agent_name": "Conversational Assistant Agent"
}
```

### Stream Agent (SSE)

```http
POST /agents/{agent_id}/stream
```

**Request Body:** Same as `/run` endpoint

**Response:** Server-Sent Events stream
```
data: The
data:  capital
data:  of
data:  France
data:  is
data:  Paris
data: [DONE]
```

## Configuration

### Agent LLM Configuration

Agents must have LLM configuration in their YAML:

```yaml
id: my-agent
name: My Agent
llm:
  provider: openai  # or groq, nvidia, anthropic
  model: gpt-4
  endpoint: https://api.openai.com/v1  # optional, uses default
  api_key: ${LLM_API_KEY}  # resolved from environment
  temperature: 0.7
  max_tokens: 2048  # or max_completion_tokens for newer models
  system_prompt: |
    You are a helpful assistant...
```

### Environment Variables

Set API keys in environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export GROQ_API_KEY="gsk_..."
export NVIDIA_API_KEY="nvapi-..."
```

## Supported Providers

### OpenAI
```yaml
llm:
  provider: openai
  model: gpt-4
  api_key: ${LLM_API_KEY}
```

### Groq
```yaml
llm:
  provider: groq
  model: llama-3.1-70b-versatile
  endpoint: https://api.groq.com/openai/v1
  api_key: ${LLM_API_KEY}
```

### NVIDIA
```yaml
llm:
  provider: nvidia
  model: meta/llama-3.1-70b-instruct
  endpoint: https://integrate.api.nvidia.com/v1
  api_key: ${LLM_API_KEY}
```

### Anthropic (OpenAI-compatible)
```yaml
llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  endpoint: https://api.anthropic.com/v1
  api_key: ${LLM_API_KEY}
```

## Parameter Compatibility

Different models may require different parameter names for controlling output length:

- **`max_tokens`**: Used by most models (GPT-4, Groq, NVIDIA, older OpenAI models)
- **`max_completion_tokens`**: Required by newer OpenAI models (GPT-4o, GPT-4-turbo latest)

The ADK automatically uses the appropriate parameter based on your configuration:

```yaml
# For newer OpenAI models
llm:
  model: gpt-4o
  max_completion_tokens: 4096  # Use this for GPT-4o

# For most other models
llm:
  model: llama-3.1-70b-versatile
  max_tokens: 2048  # Standard parameter
```

See [LLM Parameter Compatibility](./docs/LLM_PARAMETER_COMPATIBILITY.md) for detailed information.

## Python Client Example

```python
import httpx
import asyncio

async def run_agent():
    async with httpx.AsyncClient(base_url="http://localhost:8100") as client:
        response = await client.post(
            "/agents/conversational-assistant/run",
            json={
                "message": "Explain quantum computing in simple terms",
                "temperature": 0.8
            }
        )
        result = response.json()
        print(result["response"])

asyncio.run(run_agent())
```

## Streaming Example

```python
import httpx
import asyncio

async def stream_agent():
    async with httpx.AsyncClient(base_url="http://localhost:8100") as client:
        async with client.stream(
            "POST",
            "/agents/conversational-assistant/stream",
            json={"message": "Tell me a story"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    print(chunk, end="", flush=True)

asyncio.run(stream_agent())
```

## Authentication

Agents with `jwt_required: true` require authentication:

```python
headers = {"Authorization": f"Bearer {jwt_token}"}
response = await client.post(
    "/agents/secure-agent/run",
    json={"message": "Hello"},
    headers=headers
)
```

## Error Handling

The executor handles various error scenarios:

- **404**: Agent not found
- **401**: Authentication required
- **403**: Access denied (insufficient permissions)
- **500**: Execution error (LLM API error, timeout, etc.)

Error responses include detailed messages:

```json
{
  "detail": "LLM API error: Rate limit exceeded"
}
```

## Architecture

```
Client Request
    ↓
FastAPI Endpoint (/agents/{id}/run)
    ↓
AgentExecutor Service
    ↓
LLMProvider (OpenAI/Groq/NVIDIA/etc.)
    ↓
LLM API
    ↓
Response/Stream
```

## Future Enhancements

- [ ] Tool calling support
- [ ] Memory persistence
- [ ] Multi-agent orchestration
- [ ] Cost tracking per execution
- [ ] Rate limiting per agent
- [ ] Execution history/logging
- [ ] Retry logic with exponential backoff
- [ ] Response caching

## See Also

- [Examples](./examples/01-simple-qa/) - Working examples
- [Agent Configuration](./data/agents/) - Agent YAML definitions
- [API Documentation](http://localhost:8100/docs) - Interactive API docs
