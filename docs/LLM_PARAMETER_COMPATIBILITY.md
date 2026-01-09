# LLM Parameter Compatibility

## Overview

Different LLM models and providers may use different parameter names for controlling output length. The ADK supports both legacy and modern parameter conventions to ensure compatibility across all models.

## Supported Parameters

**IMPORTANT**: You should only specify ONE of these parameters in your configuration. Setting both will cause API errors.

### `max_tokens` (Legacy)
Used by most OpenAI-compatible models including:
- OpenAI GPT-3.5, GPT-4 (older versions)
- Groq models (Llama, Mixtral)
- NVIDIA NIM models
- Most third-party OpenAI-compatible endpoints

### `max_completion_tokens` (Modern)
Required by newer OpenAI models:
- GPT-4o and newer models
- GPT-4-turbo (latest versions)
- Other models that follow the updated OpenAI API specification

### Parameter Priority

If both parameters are specified in your configuration:
- `max_completion_tokens` takes priority and is sent to the API
- `max_tokens` is ignored
- However, **this is not recommended** - only specify the parameter your model requires

## Configuration

The `LLMConfig` model supports both parameters:

```yaml
llm:
  provider: openai
  model: gpt-4o
  endpoint: https://api.openai.com/v1
  api_key: ${LLM_API_KEY}
  temperature: 0.7
  max_completion_tokens: 2048  # Use for newer models
```

Or for legacy models:

```yaml
llm:
  provider: groq
  model: llama-3.1-70b-versatile
  endpoint: https://api.groq.com/openai/v1
  api_key: ${LLM_API_KEY}
  temperature: 0.7
  max_tokens: 2048  # Use for older/legacy models
```

## Automatic Parameter Selection

The agent executor automatically selects the appropriate parameter:

1. **If `max_completion_tokens` is specified**: Uses `max_completion_tokens` in the API request
2. **If only `max_tokens` is specified**: Uses `max_tokens` in the API request (default behavior)
3. **If both are specified**: Prioritizes `max_completion_tokens`

This ensures backward compatibility while supporting newer models.

## Examples

### Example 1: OpenAI GPT-4o (Requires max_completion_tokens)

```yaml
# data/agents/gpt4o-agent.yaml
id: gpt4o-agent
name: GPT-4o Agent
llm:
  provider: openai
  model: gpt-4o
  endpoint: https://api.openai.com/v1
  api_key: ${LLM_API_KEY}
  temperature: 0.7
  max_completion_tokens: 4096  # Required for GPT-4o
```

### Example 2: Groq Llama (Uses max_tokens)

```yaml
# data/agents/groq-agent.yaml
id: groq-agent
name: Groq Llama Agent
llm:
  provider: groq
  model: llama-3.1-70b-versatile
  endpoint: https://api.groq.com/openai/v1
  api_key: ${LLM_API_KEY}
  temperature: 0.7
  max_tokens: 2048  # Standard for Groq
```

### Example 3: NVIDIA NIM (Uses max_tokens)

```yaml
# data/agents/nvidia-agent.yaml
id: nvidia-agent
name: NVIDIA Agent
llm:
  provider: nvidia
  model: meta/llama-3.1-70b-instruct
  endpoint: https://integrate.api.nvidia.com/v1
  api_key: ${LLM_API_KEY}
  temperature: 0.7
  max_tokens: 4096  # Standard for NVIDIA
```

## Python API

When creating agents programmatically:

```python
from app.models.agents import AgentConfig, LLMConfig

# For newer models
agent = AgentConfig(
    id="my-agent",
    name="My Agent",
    llm=LLMConfig(
        provider="openai",
        model="gpt-4o",
        endpoint="https://api.openai.com/v1",
        api_key=os.getenv("LLM_API_KEY"),
        temperature=0.7,
        max_completion_tokens=4096  # Use this for GPT-4o
    )
)

# For legacy models
agent = AgentConfig(
    id="my-agent",
    name="My Agent",
    llm=LLMConfig(
        provider="groq",
        model="llama-3.1-70b-versatile",
        endpoint="https://api.groq.com/openai/v1",
        api_key=os.getenv("LLM_API_KEY"),
        temperature=0.7,
        max_tokens=2048  # Use this for Groq
    )
)
```

## Troubleshooting

### Error: "Unsupported parameter: 'max_tokens'"

**Cause**: The model requires `max_completion_tokens` instead of `max_tokens`.

**Solution**: Update your agent configuration to use `max_completion_tokens`:

```yaml
llm:
  # Remove or comment out max_tokens
  # max_tokens: 2048
  
  # Add max_completion_tokens
  max_completion_tokens: 2048
```

### Error: "Unsupported parameter: 'max_completion_tokens'"

**Cause**: The model/provider doesn't support the newer parameter.

**Solution**: Use `max_tokens` instead:

```yaml
llm:
  # Remove max_completion_tokens
  # max_completion_tokens: 2048
  
  # Use max_tokens
  max_tokens: 2048
```

### Error: Both parameters set simultaneously

**Cause**: Your configuration has both `max_tokens` and `max_completion_tokens` specified.

**Solution**: Remove one of them - keep only the parameter your model requires:

```yaml
llm:
  # For newer models - keep only this
  max_completion_tokens: 2048
  
  # For older models - keep only this instead
  # max_tokens: 2048
```

## Model-Specific Recommendations

| Provider | Model | Recommended Parameter |
|----------|-------|----------------------|
| OpenAI | gpt-4o, gpt-4o-mini | `max_completion_tokens` |
| OpenAI | gpt-4-turbo (latest) | `max_completion_tokens` |
| OpenAI | gpt-4, gpt-3.5-turbo (older) | `max_tokens` |
| Groq | All models | `max_tokens` |
| NVIDIA | All NIM models | `max_tokens` |
| Anthropic | Claude (via OpenAI API) | `max_tokens` |

## Best Practices

1. **Use only one parameter**: Never set both `max_tokens` and `max_completion_tokens` in the same configuration
2. **Check model documentation**: Always verify which parameter your specific model requires
3. **Test with small requests**: When switching models, test with a simple request first
4. **Use environment-specific configs**: Keep separate configurations for different model versions
5. **Monitor API errors**: Watch for parameter-related errors in logs and adjust accordingly

## Related Documentation

- [Configuration Guide](./CONFIGURATION.md)
- [Agent Execution](../AGENT_EXECUTION.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
