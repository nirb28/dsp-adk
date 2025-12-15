# Agent Development Kit (ADK)

A comprehensive platform for developing, configuring, and managing AI agents with tools, MCP servers, and graph pipelines.

## Features

- **Agent Management**: Configure AI agents with LLM providers, tools, and capabilities
- **Tool System**: Define custom tools with OpenAI-compatible schemas
- **MCP Server Integration**: Connect to Model Context Protocol servers
- **Graph Pipelines**: Create LangGraph workflows and other pipeline technologies
- **Adapters**: Add cross-cutting concerns like security, observability, caching, rate limiting
- **JWT Authentication**: Full integration with DSP JWT service for secure access

## Quick Start

### 1. Install Dependencies

```bash
cd dsp-adk
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run the Server

```bash
python run.py
```

The API will be available at `http://localhost:8100`
- Swagger UI: `http://localhost:8100/docs`
- ReDoc: `http://localhost:8100/redoc`

## Architecture

```
dsp-adk/
├── app/
│   ├── api/               # REST API endpoints
│   │   ├── agents.py      # Agent CRUD operations
│   │   ├── tools.py       # Tool CRUD operations
│   │   ├── mcp_servers.py # MCP server management
│   │   ├── graphs.py      # Graph/pipeline management
│   │   └── adapters.py    # Adapter management
│   ├── models/            # Pydantic data models
│   │   ├── agents.py      # Agent configuration models
│   │   ├── tools.py       # Tool configuration models
│   │   ├── mcp_servers.py # MCP server models
│   │   ├── graphs.py      # Graph/pipeline models
│   │   ├── adapters.py    # Adapter models
│   │   └── auth.py        # Authentication models
│   ├── services/          # Business logic
│   │   ├── agent_service.py
│   │   ├── tool_service.py
│   │   ├── mcp_service.py
│   │   ├── graph_service.py
│   │   ├── adapter_service.py
│   │   └── auth_service.py
│   ├── config.py          # Configuration settings
│   └── main.py            # FastAPI application
├── data/                  # Configuration storage
│   ├── agents/            # Agent configurations (YAML)
│   ├── tools/             # Tool configurations (YAML)
│   ├── mcp_servers/       # MCP server configurations (YAML)
│   ├── graphs/            # Graph configurations (YAML)
│   └── adapters/          # Adapter configurations (YAML)
└── tests/                 # Test suite
```

## API Endpoints

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/agents` | List all agents |
| GET | `/agents/{id}` | Get agent by ID |
| POST | `/agents` | Create agent (auth required) |
| PUT | `/agents/{id}` | Update agent (auth required) |
| DELETE | `/agents/{id}` | Delete agent (admin required) |
| POST | `/agents/{id}/tools/{tool_id}` | Add tool to agent |
| DELETE | `/agents/{id}/tools/{tool_id}` | Remove tool from agent |
| POST | `/agents/{id}/mcp-servers/{server_id}` | Add MCP server to agent |

### Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tools` | List all tools |
| GET | `/tools/{id}` | Get tool by ID |
| GET | `/tools/{id}/schema` | Get OpenAI-compatible schema |
| GET | `/tools/schemas?tool_ids=...` | Get multiple tool schemas |
| POST | `/tools` | Create tool (auth required) |
| PUT | `/tools/{id}` | Update tool (auth required) |
| DELETE | `/tools/{id}` | Delete tool (admin required) |

### MCP Servers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mcp-servers` | List all MCP servers |
| GET | `/mcp-servers/{id}` | Get MCP server by ID |
| GET | `/mcp-servers/{id}/tools` | Get server tool schemas |
| GET | `/mcp-servers/{id}/status` | Get server runtime status |
| GET | `/mcp-servers/status` | Get all servers status |
| POST | `/mcp-servers` | Create MCP server (auth required) |
| PUT | `/mcp-servers/{id}` | Update MCP server (auth required) |
| DELETE | `/mcp-servers/{id}` | Delete MCP server (admin required) |

### Graphs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/graphs` | List all graphs |
| GET | `/graphs/{id}` | Get graph by ID |
| GET | `/graphs/{id}/nodes` | Get graph nodes |
| GET | `/graphs/{id}/edges` | Get graph edges |
| POST | `/graphs` | Create graph (auth required) |
| PUT | `/graphs/{id}` | Update graph (auth required) |
| DELETE | `/graphs/{id}` | Delete graph (admin required) |
| POST | `/graphs/{id}/nodes` | Add node to graph |
| POST | `/graphs/{id}/edges` | Add edge to graph |

### Adapters

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/adapters` | List all adapters |
| GET | `/adapters/types` | Get available adapter types |
| GET | `/adapters/{id}` | Get adapter by ID |
| GET | `/adapters/type/{type}` | Get adapters by type |
| POST | `/adapters` | Create adapter (auth required) |
| PUT | `/adapters/{id}` | Update adapter (auth required) |
| DELETE | `/adapters/{id}` | Delete adapter (admin required) |

## Authentication

The ADK integrates with the DSP JWT service for authentication. Include the JWT token in requests:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8100/agents
```

### Getting a Token

```bash
curl -X POST http://localhost:5000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

### Security Configuration

Each resource (agent, tool, MCP server, graph) can be configured with:
- `jwt_required`: Whether authentication is required
- `allowed_groups`: JWT groups that can access the resource
- `allowed_roles`: JWT roles that can access the resource

## Agent Configuration

Example agent configuration:

```yaml
id: my-agent
name: My Agent
description: A helpful AI assistant
type: conversational
status: active

llm:
  provider: groq  # groq, openai, nvidia, anthropic
  model: llama-3.3-70b-versatile
  endpoint: https://api.groq.com/openai/v1
  api_key_env: GROQ_API_KEY
  temperature: 0.7
  max_tokens: 2048
  system_prompt: |
    You are a helpful assistant.

capabilities:
  - tool_calling
  - multi_turn
  - streaming

tools:
  - web-search
  - calculator

mcp_servers:
  - memory-mcp

graph_id: null

memory:
  enabled: true
  type: buffer
  max_tokens: 4000

jwt_required: true
allowed_groups:
  - ai-team
```

## Tool Configuration

Example tool configuration:

```yaml
id: web-search
name: Web Search
description: Search the web for information
type: api

parameters:
  - name: query
    type: string
    description: Search query
    required: true
  - name: num_results
    type: integer
    default: 5

implementation:
  endpoint: ${SEARCH_API_ENDPOINT}
  method: GET
  headers:
    Authorization: Bearer ${SEARCH_API_KEY}

jwt_required: true
rate_limit: 30
timeout: 15
```

## MCP Server Configuration

Example MCP server configuration:

```yaml
id: filesystem-mcp
name: Filesystem MCP Server
description: File system operations

protocol: stdio  # stdio, http, sse, websocket

command: npx
args:
  - -y
  - "@modelcontextprotocol/server-filesystem"
  - "/workspace"

tools:
  - name: read_file
    description: Read file contents
    input_schema:
      type: object
      properties:
        path:
          type: string

jwt_required: true
auto_start: false
```

## Graph Configuration (LangGraph)

Example LangGraph workflow:

```yaml
id: qa-graph
name: Q&A Graph
type: langgraph

nodes:
  - id: start
    type: start
  - id: classifier
    type: agent
    agent_id: classifier-agent
  - id: router
    type: router
    routes:
      factual: search-node
      calculation: calc-node
  - id: search-node
    type: tool
    tool_id: web-search
  - id: calc-node
    type: tool
    tool_id: calculator
  - id: end
    type: end

edges:
  - source: start
    target: classifier
  - source: classifier
    target: router
  # ... more edges

entry_point: start

state_schema:
  fields:
    query:
      type: string
    result:
      type: object

max_iterations: 25
streaming: true

# Graph-level adapters
adapters:
  - adapter_id: jwt-security-adapter
    enabled: true
  - adapter_id: observability-adapter
    enabled: true
```

## Adapter Configuration

Adapters provide cross-cutting concerns that can be applied to graph nodes. Available adapter types:

| Type | Description |
|------|-------------|
| `security` | JWT validation, API key auth, input sanitization |
| `observability` | Metrics, tracing, logging |
| `caching` | Response caching to reduce latency and costs |
| `rate_limiting` | Request throttling per user/IP/API key |
| `retry` | Automatic retries with exponential backoff |
| `transformation` | Input/output transformation |
| `validation` | Schema validation for input/output |

Example security adapter:

```yaml
id: jwt-security-adapter
name: JWT Security Adapter
type: security
position: pre  # pre, post, wrap
enabled: true
priority: 10

security:
  jwt:
    enabled: true
    jwt_service_url: ${JWT_SERVICE_URL}
    secret_key_env: JWT_SECRET_KEY
    required_claims: [sub, exp]
    extract_metadata_filter: true
  input_sanitization: true
  audit_logging: true

apply_to_types: [agent, tool]
skip_types: [start, end]
```

### Using Adapters in Graphs

Adapters can be applied at two levels:

1. **Graph-level**: Applied to all nodes
```yaml
adapters:
  - adapter_id: jwt-security-adapter
    enabled: true
  - adapter_id: observability-adapter
    enabled: true
```

2. **Node-level**: Applied to specific nodes (can override graph-level)
```yaml
nodes:
  - id: planner
    type: agent
    agent_id: task-executor-agent
    adapters:
      - adapter_id: caching-adapter
        enabled: true
        config_overrides:
          ttl_seconds: 600
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

The project follows PEP 8 style guidelines.

## Integration with DSP Projects

The ADK is designed to work with other DSP AI projects:

- **dsp_ai_jwt**: Authentication and authorization
- **dsp-ai-control-tower**: Manifest-based configuration management
- **dsp-fd2**: Front door API gateway integration
- **dsp_ai_rag2**: RAG system integration

## License

MIT License
