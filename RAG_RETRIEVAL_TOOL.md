# RAG Retrieval Tool

Document retrieval tool that connects to dsp-rag service for semantic search and knowledge base access.

## Overview

The RAG Retrieval Tool enables AI agents to search through document collections using semantic similarity. It connects to a RAG (Retrieval Augmented Generation) service like dsp-rag to retrieve relevant document chunks based on queries.

## Features

- **Semantic Search**: Vector similarity-based document retrieval
- **Multiple Knowledge Bases**: Search different document collections
- **Metadata Filtering**: Filter documents by attributes
- **Reranking**: Optional reranking for improved relevance
- **Configurable Parameters**: Adjust top_k, filters, thresholds
- **OpenAI-Compatible API**: Works with dsp-rag /retrieve endpoint

## Architecture

```
Agent Query
    ↓
RAG Retrieval Tool
    ↓
HTTP POST to dsp-rag
    ↓
/retrieve endpoint
    ↓
Vector Search + Reranking
    ↓
Relevant Document Chunks
```

## Configuration

### Tool Configuration (`data/tools/rag-retrieval.yaml`)

```yaml
implementation:
  endpoint: ${RAG_ENDPOINT:http://localhost:8000}/retrieve
  method: POST
  
  rag_configs:
    default:
      endpoint: ${RAG_ENDPOINT:http://localhost:8000}
      description: Default knowledge base
      
    technical_docs:
      endpoint: ${RAG_ENDPOINT:http://localhost:8000}
      configuration_name: technical-docs
      description: Technical documentation
```

### Environment Variables

```bash
# RAG service endpoint
export RAG_ENDPOINT=http://localhost:8000

# Optional: Authentication
export RAG_API_KEY=your_api_key
```

## Parameters

### Required
- **query** (string): Search query or question

### Optional
- **configuration_name** (string): Knowledge base to search (default: "default")
- **top_k** (integer): Number of chunks to retrieve (default: 5)
- **use_reranking** (boolean): Enable reranking (default: true)
- **metadata_filter** (object): Filter by metadata (e.g., `{"category": "api"}`)
- **min_score** (float): Minimum similarity score (0.0-1.0)

## Usage

### With Tool Service

```python
from app.services.tool_service import ToolService

tool_service = ToolService(config)

result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "What is machine learning?",
        "configuration_name": "default",
        "top_k": 5,
        "use_reranking": True
    }
)

print(f"Found {result['total_chunks']} chunks")
for chunk in result['chunks']:
    print(f"Score: {chunk['score']:.4f}")
    print(f"Content: {chunk['content']}")
    print(f"Metadata: {chunk['metadata']}")
```

### With Agent

```python
from app.services.agent_executor import AgentExecutor

executor = AgentExecutor(config)

response = await executor.execute_agent(
    agent_id="knowledge-assistant",
    user_message="What is machine learning?",
    conversation_id="session-123"
)
```

### Direct Tool Call

```python
from tools.rag_retrieval import retrieve_documents

result = await retrieve_documents(
    query="machine learning",
    configuration_name="default",
    top_k=5,
    use_reranking=True,
    metadata_filter={"category": "ml"},
    tool_config=config
)
```

## Response Format

```json
{
  "success": true,
  "query": "What is machine learning?",
  "configuration_name": "default",
  "chunks": [
    {
      "content": "Machine learning is a subset of AI...",
      "metadata": {
        "source": "ml_guide.pdf",
        "page": 1,
        "category": "introduction"
      },
      "score": 0.89
    }
  ],
  "total_chunks": 5
}
```

## Integration with dsp-rag

### Request Format

The tool sends POST requests to the dsp-rag `/retrieve` endpoint:

```json
{
  "query": "search query",
  "configuration_name": "default",
  "top_k": 5,
  "use_reranking": true,
  "metadata_filter": {"category": "technical"},
  "min_score": 0.0
}
```

### Expected Response

```json
{
  "success": true,
  "documents": [
    {
      "content": "document text",
      "metadata": {...},
      "score": 0.85
    }
  ],
  "total": 5,
  "configuration_name": "default"
}
```

## Examples

### Basic Retrieval

```python
result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "How to configure authentication?",
        "configuration_name": "default",
        "top_k": 5
    }
)
```

### With Metadata Filter

```python
result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "API endpoints",
        "configuration_name": "technical_docs",
        "top_k": 10,
        "metadata_filter": {
            "category": "api",
            "version": "2.0"
        }
    }
)
```

### With Score Threshold

```python
result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "database setup",
        "top_k": 20,
        "min_score": 0.7,  # Only high-confidence results
        "use_reranking": True
    }
)
```

### Multiple Configurations

```python
# Search technical docs
tech_result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "API configuration",
        "configuration_name": "technical_docs"
    }
)

# Search customer support
support_result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "reset password",
        "configuration_name": "customer_support"
    }
)
```

## Use Cases

### 1. Question Answering
Retrieve relevant context for answering user questions.

### 2. Documentation Search
Find specific information in technical documentation.

### 3. Customer Support
Search support articles and FAQs.

### 4. Product Information
Retrieve product specifications and details.

### 5. Troubleshooting
Find solutions to common problems.

## Error Handling

The tool includes comprehensive error handling:

```python
result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={"query": "test"}
)

if result['success']:
    # Process chunks
    for chunk in result['chunks']:
        print(chunk['content'])
else:
    # Handle error
    print(f"Error: {result['error']}")
```

Common errors:
- **Connection refused**: RAG service not running
- **Configuration not found**: Invalid configuration_name
- **Timeout**: RAG service not responding
- **Invalid parameters**: Missing required fields

## Configuration Options

### Multiple RAG Services

Configure different RAG service endpoints:

```yaml
rag_configs:
  production:
    endpoint: https://rag.production.com
    description: Production RAG service
    
  staging:
    endpoint: https://rag.staging.com
    description: Staging RAG service
    
  local:
    endpoint: http://localhost:8000
    description: Local development
```

### Retry Configuration

```yaml
implementation:
  timeout: 30
  retry_count: 2
  retry_delay: 1
```

### Authentication

```yaml
headers:
  Authorization: Bearer ${RAG_API_KEY}
```

## Best Practices

### Query Formulation
- Use clear, specific queries
- Include relevant context
- Avoid overly broad queries

### Parameter Tuning
- **top_k**: Start with 5-10, adjust based on results
- **use_reranking**: Enable for better relevance
- **min_score**: Use 0.7+ for high-confidence results
- **metadata_filter**: Use to narrow search scope

### Performance
- Cache common queries
- Use appropriate top_k values
- Enable reranking selectively
- Filter by metadata when possible

### Error Handling
- Always check `success` field
- Implement retry logic for transient errors
- Provide fallback behavior
- Log errors for debugging

## Testing

Run comprehensive tests:

```bash
python test_rag_retrieval.py
```

Tests include:
- Tool loading
- Basic retrieval
- Metadata filtering
- Different configurations
- Score thresholding
- Error handling
- Agent integration

## Troubleshooting

### RAG Service Not Running

```
Error: Connection refused

Solution:
cd dsp_ai_rag2
python app/main.py
```

### No Results Found

```
total_chunks: 0

Possible causes:
- Query doesn't match documents
- Metadata filter too restrictive
- min_score too high
- Configuration has no documents

Solutions:
- Broaden query
- Remove/adjust filters
- Lower min_score
- Verify documents indexed
```

### Timeout Errors

```
Error: Request timeout

Solutions:
- Check RAG service health
- Increase timeout value
- Verify network connectivity
- Check RAG service logs
```

## Files

- `data/tools/rag-retrieval.yaml` - Tool configuration
- `tools/rag_retrieval.py` - Implementation
- `data/agents/knowledge-assistant-agent.yaml` - Example agent
- `examples/06-rag-knowledge-retrieval/` - Complete example
- `test_rag_retrieval.py` - Test suite

## Dependencies

No additional dependencies required beyond base ADK requirements:
- `httpx` - HTTP client (already in requirements.txt)
- `asyncio` - Async support (Python standard library)

## See Also

- dsp-rag documentation for RAG service setup
- `DATABASE_TOOL.md` for database integration
- `VISUALIZATION_TOOL.md` for result visualization
- OpenAI API documentation for compatible formats
