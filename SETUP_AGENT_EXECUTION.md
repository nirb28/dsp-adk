# Setup Guide: Agent Execution

This guide will help you set up and test the agent execution feature.

## Prerequisites

1. ADK server installed and configured
2. An LLM API key (OpenAI, Groq, or NVIDIA)

## Step 1: Configure Environment Variables

Create or update your `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and configure your LLM provider:

### Option A: OpenAI

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_ENDPOINT=https://api.openai.com/v1
LLM_API_KEY_ENV=OPENAI_API_KEY

OPENAI_API_KEY=sk-your-actual-openai-key-here
```

### Option B: Groq (Fast and Free)

```bash
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-70b-versatile
LLM_ENDPOINT=https://api.groq.com/openai/v1
LLM_API_KEY_ENV=GROQ_API_KEY

GROQ_API_KEY=gsk_your-actual-groq-key-here
```

### Option C: NVIDIA

```bash
LLM_PROVIDER=nvidia
LLM_MODEL=meta/llama-3.1-70b-instruct
LLM_ENDPOINT=https://integrate.api.nvidia.com/v1
LLM_API_KEY_ENV=NVIDIA_API_KEY

NVIDIA_API_KEY=nvapi-your-actual-nvidia-key-here
```

## Step 2: Verify Agent Configuration

The `conversational-assistant` agent uses environment variable placeholders that will be automatically resolved:

```yaml
# data/agents/generic/conversational-assistant.yaml
llm:
  provider: ${LLM_PROVIDER}      # Resolved from .env
  model: ${LLM_MODEL}            # Resolved from .env
  endpoint: ${LLM_ENDPOINT}      # Resolved from .env
  api_key_env: ${LLM_API_KEY_ENV}  # Resolved from .env
```

## Step 3: Start the ADK Server

```bash
python run.py
```

The server should start on `http://localhost:8100`

## Step 4: Test with Example 01

```bash
cd examples/01-simple-qa
python run.py
```

Expected output:

```
============================================================
Example 01: Simple Q&A Agent
============================================================

1. Checking for conversational-assistant agent...
   Found agent: Conversational Assistant Agent
   Description: A friendly, helpful conversational agent...

2. Agent Configuration:
   Provider: openai
   Model: gpt-4
   Temperature: 0.7

3. Configurable Parameters:
   - personality: No description
     Default: friendly
   ...

4. Running the Agent:
   Question: What is the capital of France?

   Agent Response:
   The capital of France is Paris. It's one of the most iconic...

   Metadata:
   - Model: gpt-4
   - Provider: openai
   - Duration: 1.23s
   - Tokens: 57

============================================================
Example complete!
============================================================
```

## Step 5: Test with API Directly

### Non-Streaming Request

```bash
curl -X POST http://localhost:8100/agents/conversational-assistant/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is quantum computing?"
  }'
```

### Streaming Request

```bash
curl -X POST http://localhost:8100/agents/conversational-assistant/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about artificial intelligence"
  }'
```

## Troubleshooting

### Error: "Unsupported LLM provider: ${LLM_PROVIDER}"

**Cause:** Environment variables are not being resolved.

**Solution:**
1. Ensure your `.env` file exists in the project root
2. Verify the environment variables are set correctly
3. Restart the ADK server to reload the `.env` file

### Error: "HTTP 401 Unauthorized" or API key errors

**Cause:** Invalid or missing API key.

**Solution:**
1. Check that your API key is correct in the `.env` file
2. Ensure the `LLM_API_KEY_ENV` variable points to the correct environment variable name
3. For OpenAI: Get a key from https://platform.openai.com/api-keys
4. For Groq: Get a key from https://console.groq.com/keys
5. For NVIDIA: Get a key from https://build.nvidia.com/

### Error: "HTTP 500" with LLM API errors

**Cause:** Various LLM API issues (rate limits, invalid model, etc.)

**Solution:**
1. Check the server logs for detailed error messages
2. Verify the model name is correct for your provider
3. Check your API key has sufficient credits/quota
4. Try a different model or provider

### Environment variables not loading

**Cause:** `.env` file not in the correct location or format issues.

**Solution:**
1. Ensure `.env` is in the project root (same directory as `run.py`)
2. Check file encoding is UTF-8
3. No spaces around `=` in variable assignments
4. Restart the server after making changes

## Getting API Keys

### OpenAI
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new secret key

### Groq (Recommended for testing - fast and free tier)
1. Go to https://console.groq.com/
2. Sign up with your email
3. Navigate to API Keys
4. Create a new API key

### NVIDIA
1. Go to https://build.nvidia.com/
2. Sign up or log in
3. Navigate to API Catalog
4. Get your API key

## Next Steps

Once you have agent execution working:

1. Try different questions and prompts
2. Experiment with context and history parameters
3. Test streaming responses
4. Create your own custom agents
5. Add tools to agents for enhanced capabilities

## See Also

- [Agent Execution Documentation](./AGENT_EXECUTION.md)
- [API Documentation](http://localhost:8100/docs)
- [Example Scripts](./examples/)
