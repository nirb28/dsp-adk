# RAG Knowledge Retrieval Example

This example demonstrates an AI agent that retrieves information from knowledge bases using the RAG (Retrieval Augmented Generation) retrieval tool connected to dsp-rag service.

## Features

- **Semantic Search**: Find relevant document chunks using vector similarity
- **Multiple Knowledge Bases**: Search different document collections
- **Metadata Filtering**: Filter documents by source, category, etc.
- **Reranking**: Improve relevance with optional reranking
- **Source Citations**: Agent provides answers with source references
- **Configurable Parameters**: Adjust top_k, filters, and more

## Architecture

```
User Question
    ↓
Knowledge Assistant Agent
    ↓
RAG Retrieval Tool
    ↓
HTTP Request to dsp-rag Service
    ↓
dsp-rag /retrieve endpoint
    ↓
Vector Search + Reranking
    ↓
Relevant Document Chunks
    ↓
Agent Synthesizes Answer
```

## Setup

### 1. Start dsp-rag Service

The RAG retrieval tool connects to a dsp-rag service. Make sure it's running:

```bash
# In dsp_ai_rag2 directory
python app/main.py
```

Default endpoint: `http://localhost:8000`

### 2. Configure RAG Collections

Ensure your dsp-rag service has configurations set up:
- `default` - Default knowledge base
- `technical_docs` - Technical documentation
- `customer_support` - Support articles
- `product_info` - Product information

### 3. Set Environment Variables

```bash
# RAG service endpoint (optional, defaults to localhost:8000)
export RAG_ENDPOINT=http://localhost:8000

# LLM API key
export NVAPI_KEY=your_nvidia_api_key
# OR
export OPENAI_API_KEY=your_openai_key
```

### 4. Run Example

```bash
# Interactive mode (recommended)
python examples/06-rag-knowledge-retrieval/run.py --mode interactive

# Automated demo
python examples/06-rag-knowledge-retrieval/run.py --mode auto

# Test tool directly
python examples/06-rag-knowledge-retrieval/run.py --mode test

# Custom RAG endpoint
python examples/06-rag-knowledge-retrieval/run.py --rag-endpoint http://your-rag-service:8000
```

## Usage

### Interactive Mode

```
You: What is machine learning?

Agent: [Searching knowledge base...]
       [Found 5 relevant chunks in 'default']
       
       Based on the retrieved information, machine learning is...
       [Provides comprehensive answer with source citations]
```

### Specific Knowledge Base

```
You: Search in technical_docs: How to configure the API?

Agent: [Searches technical_docs configuration]
       [Returns relevant API configuration documentation]
```

### With Metadata Filters

```
You: Find technical documentation about authentication

Agent: [Applies metadata filter: category=authentication]
       [Returns filtered, relevant chunks]
```

## Tool Parameters

The `rag-retrieval` tool supports:

- **query** (required): Search query or question
- **configuration_name**: Which knowledge base to search (default: "default")
- **top_k**: Number of chunks to retrieve (default: 5)
- **use_reranking**: Enable reranking for better relevance (default: true)
- **metadata_filter**: Filter by metadata (e.g., `{"source": "manual", "category": "api"}`)
- **min_score**: Minimum similarity score threshold (0.0-1.0)

## Example Questions

### Simple Queries
```
What is machine learning?
How does authentication work?
Explain the deployment process
```

### Specific Searches
```
Find information about API endpoints
Search for configuration examples
Look up troubleshooting steps
```

### Filtered Searches
```
Find technical documentation about databases
Search customer support articles about billing
Get product specifications for laptops
```

### Configuration-Specific
```
Search in technical_docs: How to configure the system?
Search in customer_support: How do I reset my password?
Search in product_info: What are the laptop specifications?
```

## Configuration

### Tool Configuration

Edit `data/tools/rag-retrieval.yaml`:

```yaml
implementation:
  endpoint: ${RAG_ENDPOINT:http://localhost:8000}/retrieve
  
  rag_configs:
    default:
      endpoint: ${RAG_ENDPOINT:http://localhost:8000}
      description: Default RAG configuration
      
    technical_docs:
      endpoint: ${RAG_ENDPOINT:http://localhost:8000}
      configuration_name: technical-docs
      description: Technical documentation
```

### Agent Configuration

Edit `data/agents/knowledge-assistant-agent.yaml`:

```yaml
system_prompt: |
  Your custom instructions for the agent...
  
tools:
  - rag-retrieval
```

## Direct Tool Usage

```python
from app.services.tool_service import ToolService

tool_service = ToolService(config)

result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "What is machine learning?",
        "configuration_name": "default",
        "top_k": 5,
        "use_reranking": True,
        "metadata_filter": {"category": "ml"}
    }
)

print(f"Found {result['total_chunks']} chunks")
for chunk in result['chunks']:
    print(f"Score: {chunk['score']}")
    print(f"Content: {chunk['content']}")
    print(f"Metadata: {chunk['metadata']}")
```

## Response Format

```json
{
  "success": true,
  "query": "What is machine learning?",
  "configuration_name": "default",
  "chunks": [
    {
      "content": "Machine learning is a subset of artificial intelligence...",
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

The tool uses the dsp-rag `/retrieve` endpoint which supports:

### Request Format
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

### Response Format
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

## Use Cases

### 1. Question Answering
```
User: How do I configure authentication?
Agent: [Retrieves auth docs] → Provides step-by-step answer
```

### 2. Documentation Search
```
User: Find API endpoint documentation
Agent: [Searches technical docs] → Returns relevant API docs
```

### 3. Troubleshooting
```
User: How to fix deployment errors?
Agent: [Searches troubleshooting guides] → Provides solutions
```

### 4. Product Information
```
User: What are the laptop specifications?
Agent: [Searches product catalog] → Returns specs
```

## Advanced Features

### Multiple Knowledge Bases

Search across different collections:
```python
# Technical documentation
result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "API configuration",
        "configuration_name": "technical_docs"
    }
)

# Customer support
result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "reset password",
        "configuration_name": "customer_support"
    }
)
```

### Metadata Filtering

Filter by document attributes:
```python
result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "database setup",
        "metadata_filter": {
            "source": "manual",
            "category": "database",
            "version": "2.0"
        }
    }
)
```

### Score Thresholding

Only return high-confidence results:
```python
result = await tool_service.execute_tool(
    tool_id="rag-retrieval",
    parameters={
        "query": "authentication",
        "min_score": 0.7,  # Only chunks with score >= 0.7
        "top_k": 10
    }
)
```

## Troubleshooting

### RAG Service Not Running
```
Error: Request error: Connection refused

Solution: Start dsp-rag service
cd dsp_ai_rag2
python app/main.py
```

### Configuration Not Found
```
Error: Configuration 'xyz' not found

Solution: Check available configurations in dsp-rag
Ensure configuration exists in RAG service
```

### No Results Found
```
Result: total_chunks: 0

Possible causes:
- Query doesn't match any documents
- Metadata filter too restrictive
- min_score threshold too high
- Configuration has no documents

Solutions:
- Broaden search query
- Remove or adjust metadata filters
- Lower min_score threshold
- Verify documents are indexed
```

### Connection Timeout
```
Error: Request timeout

Solutions:
- Check RAG service is responsive
- Increase timeout in tool config
- Check network connectivity
```

## Files

### Tool Configuration
- `data/tools/rag-retrieval.yaml` - RAG retrieval tool definition

### Tool Implementation
- `tools/rag_retrieval.py` - Python implementation

### Agent Configuration
- `data/agents/knowledge-assistant-agent.yaml` - Agent definition

### Example
- `examples/06-rag-knowledge-retrieval/run.py` - Demo script
- `examples/06-rag-knowledge-retrieval/README.md` - This file
- `examples/06-rag-knowledge-retrieval/config.yaml` - Configuration

## Testing

Run comprehensive tests:
```bash
python test_rag_retrieval.py
```

Tests:
- Tool loading
- Basic retrieval
- Metadata filtering
- Different configurations
- Error handling
- Agent integration

## Next Steps

1. **Add More Knowledge Bases**: Configure additional RAG collections
2. **Custom Metadata**: Add domain-specific metadata fields
3. **Hybrid Search**: Combine with other search tools
4. **Caching**: Implement result caching for common queries
5. **Analytics**: Track search patterns and popular queries

## See Also

- dsp-rag documentation for RAG service setup
- `DATABASE_TOOL.md` for database integration
- `VISUALIZATION_TOOL.md` for result visualization
