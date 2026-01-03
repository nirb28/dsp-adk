# Environment Variable Substitution

The ADK supports environment variable substitution in YAML configuration files using two syntaxes:

## Supported Syntaxes

### 1. `$VAR_NAME` Syntax (Simple)
```yaml
api_key: $BRAVE_API_KEY
endpoint: https://api.example.com
```

### 2. `${VAR_NAME}` Syntax (Braces)
```yaml
api_key: ${NVIDIA_API_KEY}
model: ${LLM_MODEL}
```

Both syntaxes work identically and can be mixed in the same configuration file.

## How It Works

When loading YAML configuration files (agents, tools, skills), the storage service automatically:

1. Scans all string values for environment variable references
2. Looks up the variable in the environment
3. Replaces the reference with the actual value
4. Warns if a variable is not set (leaves placeholder unchanged)

This happens **recursively** through all nested data structures (dicts, lists, strings).

## Use Cases

### 1. API Key References

Instead of duplicating API keys across multiple configurations:

```bash
# .env file
BRAVE_API_KEY=BSAgNHWKHr9_VyP1q4Cx_6A52wGGbuB
SEARCH_API_KEY=$BRAVE_API_KEY
```

In tool configuration:
```yaml
# data/tools/web-search.yaml
id: web-search
name: Web Search
api_key: $BRAVE_API_KEY  # Will be replaced with actual key
endpoint: https://api.search.brave.com/res/v1/web/search
```

### 2. LLM Configuration

```bash
# .env file
NVIDIA_API_KEY=nvapi-your-key-here
LLM_API_KEY_ENV=NVIDIA_API_KEY
```

In agent configuration:
```yaml
# data/agents/research-agent.yaml
llm:
  provider: nvidia
  model: meta/llama-3.1-70b-instruct
  endpoint: https://integrate.api.nvidia.com/v1
  api_key_env: $LLM_API_KEY_ENV  # References NVIDIA_API_KEY
```

### 3. Dynamic Configuration

```yaml
# Partial substitution in URLs
endpoint: https://api.example.com?key=$API_KEY&region=$REGION

# Mixed references
message: "Using API key from $PRIMARY_KEY with fallback to ${SECONDARY_KEY}"
```

## Best Practices

### ✅ DO

- Use `$VAR_NAME` for simple, clear references
- Use `${VAR_NAME}` when the variable name is followed by alphanumeric characters
- Set all required environment variables before starting the application
- Document required environment variables in `.env.example`

### ❌ DON'T

- Don't hardcode sensitive values (API keys, passwords) in YAML files
- Don't use variable substitution for non-string values (use actual values)
- Don't nest variable references (`$$VAR` or `${${VAR}}`)

## Examples

### Example 1: Tool Configuration with API Key Reference

```yaml
# data/tools/web-search.yaml
id: web-search
name: Web Search Tool
tool_type: api
api_key: $BRAVE_API_KEY
endpoint: https://api.search.brave.com/res/v1/web/search
```

```bash
# .env
BRAVE_API_KEY=BSAgNHWKHr9_VyP1q4Cx_6A52wGGbuB
```

### Example 2: Agent with Multiple Variable References

```yaml
# data/agents/my-agent.yaml
id: my-agent
name: My Agent
llm:
  provider: ${LLM_PROVIDER}
  model: ${LLM_MODEL}
  endpoint: ${LLM_ENDPOINT}
  api_key_env: $LLM_API_KEY_ENV
tools:
  - web-search
  - text-processor
```

```bash
# .env
LLM_PROVIDER=nvidia
LLM_MODEL=meta/llama-3.1-70b-instruct
LLM_ENDPOINT=https://integrate.api.nvidia.com/v1
LLM_API_KEY_ENV=NVIDIA_API_KEY
NVIDIA_API_KEY=nvapi-your-key-here
```

### Example 3: Nested Data Structures

```yaml
# Complex configuration with nested references
config:
  primary:
    api_key: $PRIMARY_API_KEY
    endpoint: $PRIMARY_ENDPOINT
  fallback:
    api_key: ${FALLBACK_API_KEY}
    endpoint: ${FALLBACK_ENDPOINT}
  settings:
    - name: timeout
      value: $TIMEOUT_SECONDS
    - name: retries
      value: $MAX_RETRIES
```

## Troubleshooting

### Variable Not Being Replaced

**Problem**: Variable reference like `$MY_VAR` appears in logs unchanged.

**Solutions**:
1. Check that the environment variable is set: `echo $MY_VAR` (Linux/Mac) or `echo %MY_VAR%` (Windows)
2. Restart the application after setting new environment variables
3. Check for typos in variable names (case-sensitive)
4. Look for warning logs: `Environment variable 'MY_VAR' not set, leaving placeholder`

### Variable Contains Special Characters

**Problem**: Variable value contains `$` or other special characters.

**Solution**: Environment variables are used as-is. No escaping needed. The substitution only happens in YAML files, not in environment variable values themselves.

### Circular References

**Problem**: `VAR1=$VAR2` and `VAR2=$VAR1`

**Solution**: The substitution happens only once when loading YAML files. Circular references in environment variables themselves are not resolved. Set actual values in your environment.

## Testing Variable Substitution

Run the test script to verify variable substitution works:

```bash
python test_env_variable_substitution.py
```

This tests:
- `$VAR_NAME` syntax
- `${VAR_NAME}` syntax
- Mixed syntax
- Nested data structures
- Non-existent variables
- Partial substitution

## Security Considerations

1. **Never commit `.env` files** with real API keys to version control
2. **Use `.env.example`** with placeholder values for documentation
3. **Rotate API keys** if accidentally exposed
4. **Use different keys** for development, staging, and production
5. **Limit API key permissions** to minimum required scope

## Related Documentation

- [Configuration Guide](./CONFIGURATION.md)
- [Debug Logging](../DEBUG_LOGGING.md)
- [Tool Development](./TOOL_DEVELOPMENT.md)
