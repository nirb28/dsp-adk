# Configuration Guide

## Overview

The ADK uses a **consistent `${VARIABLE_NAME}` syntax** for environment variable references across all configuration files:

- `.env` files
- YAML configuration files (agents, tools, skills)
- All string values are automatically resolved

## How It Works

### 1. Define Variables in `.env`

```bash
# .env
LLM_API_KEY=nvapi-your-actual-key-here
```

### 2. Reference Variables in YAML

```yaml
# research-agent.yaml
llm:
  provider: ${LLM_PROVIDER}
  model: ${LLM_MODEL}
  api_key: ${LLM_API_KEY}
```

### 3. Automatic Resolution

When the application loads:
1. `.env` file is loaded by Pydantic
2. All `${VARIABLE}` references in `.env` are resolved
3. YAML files are loaded
4. All `${VARIABLE}` references in YAML are resolved
5. Final configuration has all actual values

## Variable Reference Syntax

Both syntaxes are supported and work identically:

```bash
# With braces (recommended for clarity)
LLM_API_KEY=${NVIDIA_API_KEY}

# Without braces (shorter)
LLM_API_KEY=$NVIDIA_API_KEY
```

**Recommendation**: Use `${VARIABLE}` for consistency and clarity.

## Complete Example

### `.env` File

```bash
# LLM Provider Configuration
LLM_PROVIDER=nvidia
LLM_MODEL=meta/llama-3.1-70b-instruct
LLM_ENDPOINT=https://integrate.api.nvidia.com/v1
LLM_API_KEY=nvapi-your-actual-key-here

# Tool API Keys
BRAVE_API_KEY=BSAgNHWKHr9_VyP1q4Cx_6A52wGGbuB
SEARCH_API_KEY=${BRAVE_API_KEY}
SEARCH_API_ENDPOINT=https://api.search.brave.com/res/v1/web/search
```

### Agent YAML

```yaml
# data/agents/generic/research-agent.yaml
id: research-agent
name: Research Agent

llm:
  provider: ${LLM_PROVIDER}
  model: ${LLM_MODEL}
  endpoint: ${LLM_ENDPOINT}
  api_key: ${LLM_API_KEY}
  temperature: 0.3
  max_tokens: 2048

tools:
  - web-search
  - text-processor
```

### Tool YAML

```yaml
# data/tools/web-search.yaml
id: web-search
name: Web Search Tool
tool_type: api

implementation:
  endpoint: ${SEARCH_API_ENDPOINT}
  method: GET
  headers:
    X-Subscription-Token: ${SEARCH_API_KEY}
```

## Switching Between Providers

To switch LLM providers, just change which API key is referenced:

### For OpenAI

```bash
# .env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_ENDPOINT=https://api.openai.com/v1
LLM_API_KEY=sk-your-openai-key-here
```

### For Groq

```bash
# .env
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-70b-versatile
LLM_ENDPOINT=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_your-groq-key-here
```

### For NVIDIA

```bash
# .env
LLM_PROVIDER=nvidia
LLM_MODEL=meta/llama-3.1-70b-instruct
LLM_ENDPOINT=https://integrate.api.nvidia.com/v1
LLM_API_KEY=nvapi-your-nvidia-key-here
```

## Best Practices

### ✅ DO

1. **Use `${VARIABLE}` syntax for references**
   ```bash
   SEARCH_API_KEY=${BRAVE_API_KEY}
   DB_PATH=${DATA_DIR}/databases/sample.db
   ```

2. **Use clear variable names**
   ```bash
   LLM_API_KEY=your-api-key-here
   LLM_PROVIDER=nvidia
   LLM_MODEL=meta/llama-3.1-70b-instruct
   ```

3. **Group related configuration**
   ```bash
   # LLM Configuration
   LLM_PROVIDER=nvidia
   LLM_MODEL=meta/llama-3.1-70b-instruct
   LLM_ENDPOINT=https://integrate.api.nvidia.com/v1
   LLM_API_KEY=nvapi-xxx
   
   # Search Configuration
   BRAVE_API_KEY=brave-xxx
   SEARCH_API_KEY=${BRAVE_API_KEY}
   ```

### ❌ DON'T

1. **Don't hardcode API keys in YAML**
   ```yaml
   # Bad
   api_key: nvapi-hardcoded-key-here
   
   # Good
   api_key: ${LLM_API_KEY}
   ```

2. **Don't use inconsistent syntax**
   ```bash
   # Inconsistent
   SEARCH_API_KEY=${BRAVE_API_KEY}
   DB_PATH=DATA_DIR/db  # Missing $ for reference
   ```

3. **Don't create circular references**
   ```bash
   # Bad - circular
   VAR1=${VAR2}
   VAR2=${VAR1}
   ```

4. **Don't reference undefined variables**
   ```bash
   # Bad - UNDEFINED_VAR doesn't exist
   LLM_API_KEY=${UNDEFINED_VAR}
   ```

## Variable Resolution Order

Variables are resolved in this order:

1. **Environment variables** (from system)
2. **`.env` file** (loaded by Pydantic)
3. **Variable substitution** (in `.env` values)
4. **YAML loading** (with variable substitution)

This means:
- System environment variables override `.env` file
- Variables in `.env` can reference other variables in `.env`
- YAML files can reference any environment variable

## Debugging Variable Resolution

Enable debug logging to see variable resolution:

```bash
# .env
LOG_LEVEL=DEBUG
```

You'll see logs like:
```
[AGENT_EXEC] API key loaded for provider 'nvidia'
[TOOL_LOAD] Tool 'web-search' loaded: type=api, enabled=True
```

If a variable is not resolved, you'll see warnings:
```
Environment variable 'UNDEFINED_VAR' not set, leaving placeholder
```

## Common Patterns

### Pattern 1: Single Provider

```bash
# .env - Simple setup for one provider
LLM_PROVIDER=nvidia
LLM_MODEL=meta/llama-3.1-70b-instruct
LLM_ENDPOINT=https://integrate.api.nvidia.com/v1
LLM_API_KEY=nvapi-your-key-here  # Direct value
```

### Pattern 2: Provider Switching

```bash
# .env - Switch provider by changing these values
LLM_PROVIDER=nvidia
LLM_MODEL=meta/llama-3.1-70b-instruct
LLM_ENDPOINT=https://integrate.api.nvidia.com/v1
LLM_API_KEY=nvapi-xxx

# To switch to OpenAI, change to:
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4
# LLM_ENDPOINT=https://api.openai.com/v1
# LLM_API_KEY=sk-xxx
```

### Pattern 3: Shared API Keys

```bash
# .env - Reuse API keys across tools
BRAVE_API_KEY=BSAgxxx

# Multiple tools use the same key
SEARCH_API_KEY=${BRAVE_API_KEY}
WEB_SCRAPER_API_KEY=${BRAVE_API_KEY}
```

### Pattern 4: Environment-Specific

```bash
# .env.development
LLM_ENDPOINT=http://localhost:8000/v1
LLM_API_KEY=dev-key

# .env.production
LLM_ENDPOINT=https://api.production.com/v1
LLM_API_KEY=${PRODUCTION_API_KEY}
```

## Security Considerations

1. **Never commit `.env` files** with real API keys
   ```bash
   # .gitignore
   .env
   .env.local
   .env.*.local
   ```

2. **Use `.env.example` for documentation**
   ```bash
   # .env.example - Safe to commit
   LLM_API_KEY=your-api-key-here
   LLM_PROVIDER=nvidia
   ```

3. **Rotate keys if exposed**
   - Generate new API keys immediately
   - Update `.env` file
   - Restart application

4. **Use different keys per environment**
   - Development keys with limited permissions
   - Production keys with full access
   - Never share keys between environments

## Troubleshooting

### Issue: API key not working

**Check:**
1. Variable is defined in `.env`
2. No typos in variable names
3. Application restarted after `.env` changes
4. Debug logging enabled to see resolution

### Issue: Variable not being substituted

**Check:**
1. Syntax is correct: `${VARIABLE}` or `$VARIABLE`
2. Variable is defined before being referenced
3. No circular references
4. Check logs for warnings

### Issue: Wrong API key being used

**Check:**
1. Which variable `LLM_API_KEY` references
2. Order of variables in `.env`
3. System environment variables (override `.env`)
4. Debug logs show which key is loaded

## Related Documentation

- [Environment Variables](./ENVIRONMENT_VARIABLES.md) - Detailed variable substitution guide
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and solutions
- [Debug Logging](../DEBUG_LOGGING.md) - Logging configuration
