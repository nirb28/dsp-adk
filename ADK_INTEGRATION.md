# ADK Integration with Control Tower and Front Door

This document describes how the Agent Development Kit (ADK) integrates with the DSP AI platform components:
- **Control Tower (CT)**: Centralized configuration management via manifests
- **Front Door (FD)**: API gateway for routing and traffic management

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Control Tower (CT)                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Project Manifests                                  │   │
│  │  - ADKAgentModule     - ADKToolModule                                │   │
│  │  - ADKGraphModule     - ADKCapabilityModule                          │   │
│  │  - JWTConfigModule    - RAGServiceModule                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ GET /manifests/{project_id}
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Front Door (FD)                                    │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────┐   │
│  │  Manifest Sync   │────▶│  APISIX Gateway │────▶│  ADK Route Gen      │   │
│  │  from CT         │     │  (Routes/Auth)  │     │  (Auto-routing)     │   │
│  └─────────────────┘     └─────────────────┘     └─────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │     ADK      │    │  RAG Service │    │  JWT Service │
    │  (Agents)    │    │  (Retrieval) │    │   (Auth)     │
    └──────────────┘    └──────────────┘    └──────────────┘
```

## ADK Module Types

The Control Tower supports four ADK-specific module types:

### 1. ADK Agent Module (`adk_agent`)

Configures an ADK agent for deployment.

```json
{
  "module_type": "adk_agent",
  "name": "support-agent",
  "config": {
    "service_url": "http://adk-service:8100",
    "agent_id": "customer-support-agent",
    "tools": ["knowledge-search", "ticket-create"],
    "capabilities": ["memory", "streaming", "guardrails"],
    "memory_enabled": true,
    "memory_type": "session",
    "streaming_enabled": true,
    "stream_format": "sse",
    "guardrails_enabled": true,
    "pii_detection": true,
    "jwt_module_reference": "auth-service",
    "rag_module_reference": "knowledge-base",
    "request_timeout": 120,
    "rate_limit_enabled": true,
    "requests_per_minute": 60
  }
}
```

**Generated Routes:**
- `POST /{project_id}/agents/{name}/run` - Execute agent
- `POST /{project_id}/agents/{name}/stream` - Stream execution
- `GET /{project_id}/agents/{name}/info` - Get agent info

### 2. ADK Tool Module (`adk_tool`)

Configures an ADK tool for deployment.

```json
{
  "module_type": "adk_tool",
  "name": "knowledge-search",
  "config": {
    "service_url": "http://adk-service:8100",
    "tool_id": "knowledge-search",
    "tool_type": "api",
    "timeout": 30,
    "jwt_module_reference": "auth-service",
    "allowed_agents": ["customer-support-agent"]
  }
}
```

**Generated Routes:**
- `POST /{project_id}/tools/{name}/execute` - Execute tool
- `GET /{project_id}/tools/{name}/schema` - Get tool schema

### 3. ADK Graph Module (`adk_graph`)

Configures an ADK graph/workflow for deployment.

```json
{
  "module_type": "adk_graph",
  "name": "support-workflow",
  "config": {
    "service_url": "http://adk-service:8100",
    "graph_id": "customer-support-workflow",
    "graph_type": "langgraph",
    "max_iterations": 10,
    "timeout_seconds": 300,
    "enable_checkpointing": true,
    "human_approval_enabled": true,
    "jwt_module_reference": "auth-service",
    "agent_modules": ["support-agent", "escalation-agent"]
  }
}
```

**Generated Routes:**
- `POST /{project_id}/graphs/{name}/run` - Execute graph
- `POST /{project_id}/graphs/{name}/stream` - Stream execution
- `GET /{project_id}/graphs/{name}/info` - Get graph info
- `GET /{project_id}/graphs/{name}/state` - Get graph state

### 4. ADK Capability Module (`adk_capability`)

Configures ADK capabilities (sessions, memory, guardrails, etc.).

```json
{
  "module_type": "adk_capability",
  "name": "session-management",
  "config": {
    "service_url": "http://adk-service:8100",
    "capability_name": "sessions",
    "enabled": true,
    "session_ttl_minutes": 60,
    "max_messages": 100
  }
}
```

## Cross-References

Modules can reference each other for integrated functionality:

```json
{
  "module_type": "adk_agent",
  "name": "support-agent",
  "cross_references": {
    "authentication": {
      "module_name": "auth-service",
      "module_type": "jwt_config",
      "purpose": "JWT token validation",
      "required": true
    },
    "knowledge": {
      "module_name": "knowledge-base",
      "module_type": "rag_service",
      "purpose": "Knowledge retrieval",
      "required": true
    }
  },
  "config": { ... }
}
```

## Integration Flow

### 1. Manifest Creation

Create a manifest in Control Tower with ADK modules:

```bash
curl -X POST http://localhost:8000/manifests \
  -H "Content-Type: application/json" \
  -H "X-DSPAI-Client-Secret: your-secret" \
  -d @manifest.json
```

### 2. Front Door Sync

Front Door automatically syncs manifests and generates APISIX routes:

```python
from src.apisix.adk_routes import generate_adk_routes_for_project

# Fetch manifest modules
manifest = await fetch_manifest("my-project")

# Generate routes
result = generate_adk_routes_for_project(
    project_id="my-project",
    manifest_modules=manifest["modules"]
)

print(result["summary"])
# {
#   "project_id": "my-project",
#   "total_routes": 9,
#   "agent_routes": 3,
#   "tool_routes": 2,
#   "graph_routes": 4,
#   "endpoints": [...]
# }
```

### 3. ADK Configuration Loading

ADK can load configurations from manifests:

```python
from app.services.manifest_integration import get_manifest_service

service = get_manifest_service()

# Fetch and cache manifest
manifest = await service.fetch_manifest("my-project")

# Extract ADK modules
adk_modules = service.extract_all_adk_modules(manifest)

# Build agent config from manifest
agent_module = adk_modules["agents"][0]
agent_config = service.build_agent_config_from_manifest(agent_module)
```

### 4. Client Requests

Clients make requests through Front Door:

```bash
# Execute agent
curl -X POST http://frontend:9080/my-project/agents/support-agent/run \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'

# Stream response
curl -X POST http://frontend:9080/my-project/agents/support-agent/stream \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Help me with my order"}'

# Execute tool
curl -X POST http://frontend:9080/my-project/tools/knowledge-search/execute \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "password reset instructions"}'
```

## Configuration

### ADK Service Configuration

Configure ADK to connect to Control Tower:

```python
from app.services.manifest_integration import configure_manifest_service

configure_manifest_service(
    control_tower_url="http://control-tower:8000",
    client_id="adk-service",
    client_secret="your-secret"
)
```

### Environment Variables

```bash
# Control Tower connection
CONTROL_TOWER_URL=http://control-tower:8000
CONTROL_TOWER_CLIENT_ID=adk-service
CONTROL_TOWER_CLIENT_SECRET=your-secret

# ADK service
ADK_SERVICE_URL=http://localhost:8100
ADK_DEFAULT_TIMEOUT=120
```

## Example Manifest

See `manifests/adk-customer-service.json` in Control Tower for a complete example.

## API Endpoints

### Control Tower Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/manifests` | GET | List all manifests |
| `/manifests/{id}` | GET | Get manifest by ID |
| `/manifests/{id}/modules` | GET | Get manifest modules |
| `/module-types` | GET | List available module types |

### Generated APISIX Routes

| Pattern | Method | Description |
|---------|--------|-------------|
| `/{project}/agents/{name}/run` | POST | Execute agent |
| `/{project}/agents/{name}/stream` | POST | Stream agent |
| `/{project}/agents/{name}/info` | GET | Agent info |
| `/{project}/tools/{name}/execute` | POST | Execute tool |
| `/{project}/tools/{name}/schema` | GET | Tool schema |
| `/{project}/graphs/{name}/run` | POST | Execute graph |
| `/{project}/graphs/{name}/stream` | POST | Stream graph |

## Security

### JWT Authentication

ADK modules can reference JWT config modules for authentication:

```json
{
  "jwt_module_reference": "auth-service"
}
```

This automatically configures:
- APISIX jwt-auth plugin on routes
- Token validation before forwarding to ADK
- User context injection into requests

### Rate Limiting

Enable rate limiting per agent:

```json
{
  "rate_limit_enabled": true,
  "requests_per_minute": 60,
  "tokens_per_minute": 100000
}
```

## Monitoring

### Prometheus Metrics

All generated routes include Prometheus plugin for metrics:
- Request count by route
- Latency histograms
- Error rates

### Logging

HTTP logger plugin captures:
- Request/response details
- Timing information
- Error messages

## Troubleshooting

### Common Issues

1. **Manifest not found**: Ensure project_id is correct and manifest exists in CT
2. **Route not generated**: Check module status is "enabled"
3. **Auth failures**: Verify JWT module reference is correct
4. **Timeout errors**: Increase request_timeout in module config

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("app.services.manifest_integration").setLevel(logging.DEBUG)
```
