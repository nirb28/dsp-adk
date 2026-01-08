# Troubleshooting Guide

## Common Issues and Solutions

### 401 Unauthorized Error - "Header of type `authorization` was missing"

**Symptoms:**
```
HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 401 Unauthorized"
ERROR - LLM API error: Header of type `authorization` was missing
```

**Cause:** The API key is not being loaded from the environment variable.

**Solution:**

1. **Check your `.env` file has the correct variables set:**

```bash
# For NVIDIA
LLM_PROVIDER=nvidia
LLM_MODEL=meta/llama-3.1-70b-instruct
LLM_ENDPOINT=https://integrate.api.nvidia.com/v1
LLM_API_KEY=nvapi-your-actual-key-here
```

2. **Verify the API key is set:**
   - `LLM_API_KEY` should contain your actual API key
   - The YAML config uses `${LLM_API_KEY}` which resolves to the actual key value

3. **Check for typos:**
   - Variable names are case-sensitive
   - Make sure `LLM_API_KEY` is spelled correctly

4. **Restart the server after changing `.env`:**
```bash
# Stop the server (Ctrl+C)
python run.py
```

5. **Enable debug logging to see what's happening:**
```bash
# In .env
LOG_LEVEL=DEBUG
```

Look for these log messages:
```
[AGENT_EXEC] API key loaded for provider 'nvidia'  # Good!
[AGENT_EXEC] No API key configured for provider 'nvidia'  # Bad - check your .env
```

### Environment Variable Not Being Substituted

**Symptoms:**
- Variable references like `$BRAVE_API_KEY` appear unchanged in logs
- Tools fail with "invalid API key" errors

**Solutions:**

1. **Check the variable is set in your environment:**
```bash
# Linux/Mac
echo $BRAVE_API_KEY

# Windows PowerShell
echo $env:BRAVE_API_KEY

# Windows CMD
echo %BRAVE_API_KEY%
```

2. **Verify `.env` file is being loaded:**
   - File must be named exactly `.env` (not `.env.txt` or `.env.example`)
   - File must be in the project root directory
   - Restart the application after changes

3. **Check for syntax errors in `.env`:**
```bash
# Correct
BRAVE_API_KEY=BSAgNHWKHr9_VyP1q4Cx_6A52wGGbuB

# Wrong - no quotes needed
BRAVE_API_KEY="BSAgNHWKHr9_VyP1q4Cx_6A52wGGbuB"

# Wrong - no spaces around =
BRAVE_API_KEY = BSAgNHWKHr9_VyP1q4Cx_6A52wGGbuB
```

4. **Look for warning logs:**
```
Environment variable 'BRAVE_API_KEY' not set, leaving placeholder
```

### Tool Execution Failures

**Symptoms:**
- Tools return errors or empty results
- "Tool not found" errors

**Solutions:**

1. **Verify tool configuration exists:**
```bash
ls data/tools/
# Should show web-search.yaml, text-processor.yaml, etc.
```

2. **Check tool is assigned to agent:**
```yaml
# In agent YAML
tools:
  - web-search
  - text-processor
```

3. **Verify tool API keys are set:**
```bash
# For web-search tool
BRAVE_API_KEY=your-key-here
```

4. **Enable verbose logging to see full payloads:**
```bash
# In .env
VERBOSE_LOGGING=true
```

### Agent Not Loading

**Symptoms:**
- "Agent not found" errors
- 404 responses from `/agents/{agent_id}`

**Solutions:**

1. **Check agent file exists:**
```bash
ls data/agents/generic/research-agent.yaml
```

2. **Verify YAML syntax is valid:**
```bash
# Use a YAML validator or Python
python -c "import yaml; yaml.safe_load(open('data/agents/generic/research-agent.yaml'))"
```

3. **Check for required fields:**
```yaml
id: research-agent  # Required
name: Research Agent  # Required
llm:  # Required
  provider: nvidia
  model: meta/llama-3.1-70b-instruct
```

4. **Look for loading errors in logs:**
```
[AGENT_LOAD] Agent 'research-agent' not found
[AGENT_LOAD] Failed to load agent: <error details>
```

### LLM Provider Errors

**Symptoms:**
- Connection timeouts
- "Unsupported LLM provider" errors
- Model not found errors

**Solutions:**

1. **Verify provider is supported:**
   - `openai` - OpenAI API
   - `groq` - Groq API
   - `nvidia` - NVIDIA NIM API
   - `anthropic` - Anthropic API

2. **Check endpoint URL is correct:**
```bash
# NVIDIA
LLM_ENDPOINT=https://integrate.api.nvidia.com/v1

# Groq
LLM_ENDPOINT=https://api.groq.com/openai/v1

# OpenAI
LLM_ENDPOINT=https://api.openai.com/v1
```

3. **Verify model name matches provider:**
```bash
# NVIDIA models
meta/llama-3.1-70b-instruct
meta/llama-3.1-8b-instruct

# Groq models
llama-3.1-70b-versatile
mixtral-8x7b-32768

# OpenAI models
gpt-4
gpt-3.5-turbo
```

4. **Test API key manually:**
```bash
# NVIDIA
curl -H "Authorization: Bearer $LLM_API_KEY" \
  https://integrate.api.nvidia.com/v1/models

# Should return list of available models
```

### Telemetry/Tracing Issues

**Symptoms:**
- "Failed to export traces" warnings
- Jaeger not showing traces

**Solutions:**

1. **Check if Jaeger is running:**
```bash
docker ps | grep jaeger
```

2. **Start Jaeger if not running:**
```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

3. **Verify OTEL configuration:**
```bash
# In .env
OTEL_ENABLED=true
OTEL_ENDPOINT=http://localhost:4318
```

4. **Disable telemetry if not needed:**
```bash
# In .env
OTEL_ENABLED=false
```

### Performance Issues

**Symptoms:**
- Slow response times
- High memory usage
- Large log files

**Solutions:**

1. **Disable verbose logging:**
```bash
# In .env
VERBOSE_LOGGING=false
LOG_LEVEL=INFO
```

2. **Reduce telemetry retention:**
```bash
# In .env
OTEL_MAX_TRACES=1000
OTEL_MAX_SPANS=10000
```

3. **Limit tool iterations:**
```yaml
# In agent config
max_tool_iterations: 5  # Default is 10
```

4. **Use faster models:**
```bash
# Switch from 70B to 8B model
LLM_MODEL=meta/llama-3.1-8b-instruct
```

## Debug Checklist

When troubleshooting issues, follow this checklist:

- [ ] Check `.env` file exists and has correct values
- [ ] Verify all required environment variables are set
- [ ] Restart the application after `.env` changes
- [ ] Enable debug logging (`LOG_LEVEL=DEBUG`)
- [ ] Check logs for error messages and warnings
- [ ] Verify YAML configuration files are valid
- [ ] Test API keys manually with curl
- [ ] Check file permissions on data directories
- [ ] Verify network connectivity to external APIs
- [ ] Review recent code changes if issue is new

## Getting Help

If you're still stuck:

1. **Collect debug information:**
```bash
# Run with debug logging
LOG_LEVEL=DEBUG python run.py > debug.log 2>&1

# Check versions
python --version
pip list | grep -E "(fastapi|pydantic|httpx)"
```

2. **Check documentation:**
   - [Environment Variables](./ENVIRONMENT_VARIABLES.md)
   - [Debug Logging](../DEBUG_LOGGING.md)
   - [Configuration Guide](./CONFIGURATION.md)

3. **Review example configurations:**
   - `data/agents/generic/research-agent.yaml`
   - `.env.example`
   - `examples/02-research-with-tools/`

4. **Search logs for specific error patterns:**
```bash
# Find all ERROR level logs
grep "ERROR" debug.log

# Find API key issues
grep "api_key" debug.log

# Find environment variable warnings
grep "Environment variable" debug.log
```
