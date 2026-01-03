# Debug Logging in ADK

This document explains the comprehensive debug logging system added to the ADK for tracking agent, tool, and skill execution flow.

## Overview

Debug logging has been added throughout the ADK codebase with clear execution flow markers to help developers understand and troubleshoot the execution of agents, tools, and skills.

## Log Markers

All debug logs use consistent markers to identify the component:

- **`[AGENT_EXEC]`** - Agent execution flow (AgentExecutor)
- **`[AGENT_EXEC:VERBOSE]`** - Verbose payload logging for LLM requests/responses
- **`[TOOL_EXEC]`** - Tool execution flow (all tool types)
- **`[TOOL_EXEC:VERBOSE]`** - Verbose payload logging for tool arguments/results
- **`[TOOL_EXEC:API]`** - API tool execution details
- **`[TOOL_EXEC:PYTHON]`** - Python tool execution details
- **`[TOOL_EXEC:SHELL]`** - Shell tool execution details
- **`[TOOL_LOAD]`** - Tool loading operations (ToolService)
- **`[TOOL_LOAD:VERBOSE]`** - Verbose payload logging for full tool configs
- **`[TOOL_LIST]`** - Tool listing operations
- **`[TOOL_ACCESS]`** - Tool access control checks
- **`[TOOL_CREATE]`** - Tool creation operations
- **`[AGENT_LOAD]`** - Agent loading operations (AgentService)
- **`[AGENT_LOAD:VERBOSE]`** - Verbose payload logging for full agent configs
- **`[AGENT_LIST]`** - Agent listing operations
- **`[AGENT_ACCESS]`** - Agent access control checks
- **`[AGENT_CREATE]`** - Agent creation operations
- **`[SKILL_LOAD]`** - Skill loading operations (RepositoryService)
- **`[SKILL_LOAD:VERBOSE]`** - Verbose payload logging for full skill configs
- **`[SKILL_LIST]`** - Skill listing operations
- **`[REPO_LOAD]`** - Repository asset loading

## Enabling Debug Logging

### Method 1: Environment Variable

```bash
# Basic debug logging
export LOG_LEVEL=DEBUG
python run.py

# Debug logging with verbose payload logging
export LOG_LEVEL=DEBUG
export VERBOSE_LOGGING=true
python run.py
```

### Method 2: In .env File

```bash
LOG_LEVEL=DEBUG
VERBOSE_LOGGING=true
```

### Method 3: In Python Code

```python
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
```

### Method 4: Configure Specific Loggers

```python
import logging

# Enable debug for specific components
logging.getLogger('app.services.agent_executor').setLevel(logging.DEBUG)
logging.getLogger('app.services.tool_service').setLevel(logging.DEBUG)
logging.getLogger('app.services.agent_service').setLevel(logging.DEBUG)
```

## Verbose Payload Logging

**IMPORTANT**: Verbose logging logs **ALL** request and response payloads in full. This includes:
- Complete LLM request messages (all messages, tools, parameters)
- Complete LLM response payloads (full content, tool calls, metadata)
- Full tool arguments (all parameters passed to tools)
- Full tool results (complete response data)
- Full configuration objects (agents, tools, skills)

**Use Cases**:
- Deep debugging of LLM interactions
- Troubleshooting tool parameter issues
- Analyzing exact data flow through the system
- Reproducing issues with exact payloads

**Warning**: Verbose logging generates **very large** log files. Only enable when needed for specific debugging tasks.

### Enabling Verbose Logging

```bash
# Via environment variable
export VERBOSE_LOGGING=true

# Or in .env file
VERBOSE_LOGGING=true
```

### Verbose Log Examples

```
[AGENT_EXEC:VERBOSE] Full LLM request payload: {
  "messages": [
    {"role": "system", "content": "You are a research assistant..."},
    {"role": "user", "content": "What is quantum computing?"}
  ],
  "tools": [{"type": "function", "function": {...}}],
  "kwargs": {"temperature": 0.3, "max_tokens": 2048}
}

[AGENT_EXEC:VERBOSE] Full LLM response payload: {
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "...",
      "tool_calls": [...]
    },
    "finish_reason": "tool_calls"
  }],
  "usage": {"prompt_tokens": 150, "completion_tokens": 50}
}

[TOOL_EXEC:VERBOSE] Tool 'web-search' full arguments payload: {
  "query": "quantum computing basics",
  "num_results": 5,
  "freshness": "pw"
}

[TOOL_EXEC:VERBOSE] Tool 'web-search' full result payload: {
  "results": [{"title": "...", "url": "...", "snippet": "..."}],
  "total_results": 5
}
```

## What Gets Logged

### Agent Execution (`[AGENT_EXEC]`)

- Agent initialization with ID and name
- Message content (first 100 chars)
- Context and configuration
- LLM provider initialization
- Message array building
- Tool loading and count
- Each iteration of the tool calling loop
- LLM response details
- Token usage per iteration
- Tool call processing
- Final response generation
- Execution duration and statistics

**Example:**
```
[AGENT_EXEC] Starting agent execution: agent_id='research-agent', agent_name='Research Agent'
[AGENT_EXEC] Message: What are the latest developments in quantum computing?...
[AGENT_EXEC] Getting LLM provider: groq
[AGENT_EXEC] Loaded 2 tools: ['web-search', 'text-processor']
[AGENT_EXEC] === Iteration 1/5 ===
[AGENT_EXEC] Processing 2 tool call(s)
[AGENT_EXEC] Tool call 1/2: web-search
[AGENT_EXEC] Execution completed successfully
[AGENT_EXEC] Duration: 3.45s, Tool calls: 2
```

### Tool Execution (`[TOOL_EXEC]`)

- Tool execution start with ID, type, and mock flag
- Tool arguments (full JSON)
- Routing to specific executor
- Execution completion with result length
- Result preview (first 200 chars)
- Error details with stack traces

**API Tools (`[TOOL_EXEC:API]`):**
- Endpoint template and resolved endpoint
- HTTP method
- Headers, query params, and body
- Response status code
- Response JSON keys or text length

**Python Tools (`[TOOL_EXEC:PYTHON]`):**
- Module and function template
- Resolved function name
- Template variables filtered out
- Function arguments after filtering
- Module import
- Function call

**Shell Tools (`[TOOL_EXEC:SHELL]`):**
- Command template
- Resolved command
- Command execution

**Example:**
```
[TOOL_EXEC] Starting execution: tool_id='web-search', type=api, mock=False
[TOOL_EXEC] Tool 'web-search' arguments: {"query": "quantum computing", "num_results": 5}
[TOOL_EXEC:API] Tool 'web-search': endpoint_template=https://api.example.com/search, method=GET
[TOOL_EXEC:API] Resolved endpoint: https://api.example.com/search
[TOOL_EXEC:API] Making request: GET https://api.example.com/search
[TOOL_EXEC:API] Response status: 200
[TOOL_EXEC] Completed: tool_id='web-search', result_length=1234
```

### Tool Loading (`[TOOL_LOAD]`)

- Tool loading by ID
- Tool type and enabled status
- Tool not found warnings

**Example:**
```
[TOOL_LOAD] Loading tool: web-search
[TOOL_LOAD] Tool 'web-search' loaded: type=api, enabled=True
```

### Agent Loading (`[AGENT_LOAD]`)

- Agent loading by ID
- Agent type, status, and tool count
- Agent not found warnings

**Example:**
```
[AGENT_LOAD] Loading agent: research-agent
[AGENT_LOAD] Agent 'research-agent' loaded: type=research, status=active, tools=2
```

### Skill Loading (`[SKILL_LOAD]`)

- Skill loading by ID
- Skill category
- Skill not found warnings

**Example:**
```
[SKILL_LOAD] Loading skill: sql-generation
[SKILL_LOAD] Skill 'sql-generation' loaded: category=data_processing
```

### Repository Loading (`[REPO_LOAD]`)

- Asset loading start
- Loading from each directory (agents, tools, skills, graphs, adapters)
- Individual asset loading
- Count of assets loaded per type
- Total assets and skills loaded

**Example:**
```
[REPO_LOAD] Starting repository asset loading
[REPO_LOAD] Loading agents from /path/to/data/agents
[REPO_LOAD] Loaded agent: research-agent
[REPO_LOAD] Loaded 5 agent(s) from /path/to/data/agents
[REPO_LOAD] Loaded 25 assets and 10 skills
```

## Example Script

See `examples/debug-mode-example.py` for a complete example of running the ADK with debug logging enabled.

```bash
cd examples
python debug-mode-example.py
```

## Filtering Debug Output

To see only specific components, use grep:

```bash
# See only agent execution flow
python your_script.py 2>&1 | grep "\[AGENT_EXEC\]"

# See only verbose payload logs
python your_script.py 2>&1 | grep "VERBOSE\]"

# See only tool execution
python your_script.py 2>&1 | grep "\[TOOL_EXEC"

# See all loading operations
python your_script.py 2>&1 | grep "LOAD\]"

# Exclude verbose logs (show only regular debug logs)
python your_script.py 2>&1 | grep -v "VERBOSE\]"
```

## Log Levels

- **DEBUG**: Detailed execution flow, arguments, intermediate steps
- **INFO**: High-level operations (tool loaded, agent started, execution completed)
- **WARNING**: Missing resources, fallback behavior
- **ERROR**: Execution failures, exceptions with stack traces

## Performance Considerations

Debug logging adds overhead. For production:

1. Set `LOG_LEVEL=INFO` or `LOG_LEVEL=WARNING`
2. **ALWAYS disable verbose logging** (`VERBOSE_LOGGING=false` or unset)
3. Use structured logging to a file instead of console
4. Consider async logging for high-throughput scenarios
5. Rotate log files to prevent disk space issues

### Verbose Logging Impact

**Verbose logging has significant performance impact**:
- Logs can be 10-100x larger than regular debug logs
- JSON serialization of large payloads adds CPU overhead
- I/O operations for writing large logs can slow execution
- Disk space fills up quickly (MB/s for active systems)

**Best Practices**:
- Only enable verbose logging for specific debugging sessions
- Use log rotation with size/time limits
- Filter logs to specific components when possible
- Disable immediately after debugging is complete

## Troubleshooting with Debug Logs

### Agent Not Calling Tools

Look for:
```
[AGENT_EXEC] Tool calling disabled or no tools configured
[AGENT_EXEC] No tools loaded for agent 'agent-id'
```

### Tool Execution Failures

Look for:
```
[TOOL_EXEC] Error executing tool 'tool-id': <error message>
[TOOL_EXEC:PYTHON] Failed to import <module>: <error>
[TOOL_EXEC:API] HTTP 404: <error>
```

### Missing Resources

Look for:
```
[TOOL_LOAD] Tool 'tool-id' not found
[AGENT_LOAD] Agent 'agent-id' not found
[SKILL_LOAD] Skill 'skill-id' not found
```

### Performance Issues

Look for:
```
[AGENT_EXEC] Duration: <time>s, Tool calls: <count>
[AGENT_EXEC] Total tokens: <count>
```

## Modified Files

The following files have been enhanced with debug logging:

- `app/services/agent_executor.py` - Agent and tool execution
- `app/services/tool_service.py` - Tool management
- `app/services/agent_service.py` - Agent management
- `app/services/repository_service.py` - Skills and repository

All logging follows the same pattern for consistency and easy filtering.
