# ADK Examples

This folder contains examples demonstrating how to use the Agent Development Kit (ADK) components, from simple use cases to advanced patterns.

## Prerequisites

1. ADK server running on `http://localhost:8100`
2. Generic agents, tools, and skills loaded
3. Python 3.9+ with `httpx` installed

```bash
pip install httpx
```

## Examples Overview

| # | Example | Difficulty | Description |
|---|---------|------------|-------------|
| 01 | [Simple Q&A](./01-simple-qa/) | Beginner | Basic conversational agent |
| 02 | [Research with Tools](./02-research-with-tools/) | Beginner | Agent using web search and text processing |
| 03 | [Code Review Pipeline](./03-code-review-pipeline/) | Intermediate | Code analysis with file operations |
| 04 | [Data Analysis Workflow](./04-data-analysis-workflow/) | Intermediate | Database queries and reporting |
| 05 | [Simple Graph](./05-simple-graph/) | Intermediate | Sequential agent chaining |
| 06 | [Conditional Graph](./06-conditional-graph/) | Advanced | Routing based on classification |
| 07 | [Orchestrator Pattern](./07-orchestrator-pattern/) | Advanced | Multi-agent coordination |
| 08 | [RAG Integration](./08-rag-integration/) | Advanced | Vector search for knowledge retrieval |

---

## Beginner Examples

### 01 - Simple Q&A

The simplest use case: a conversational agent answering questions without tools.

```
Agent: conversational-assistant
Tools: None
Graph: None (direct interaction)
```

**Key Concepts:**
- Agent configuration
- System prompts
- Personality settings

### 02 - Research with Tools

A research agent that uses tools to gather and process information.

```
Agent: research-agent
Tools: web-search, text-processor
Graph: None (single agent)
```

**Key Concepts:**
- Tool integration
- Configurable parameters
- Multi-tool workflows

---

## Intermediate Examples

### 03 - Code Review Pipeline

Code assistant that reads files and provides comprehensive reviews.

```
Agent: code-assistant
Tools: file-operations, text-processor
Skills: code-generation, code-review
```

**Key Concepts:**
- File system access
- Security analysis
- Code quality metrics

### 04 - Data Analysis Workflow

Data analyst that queries databases and generates insights.

```
Agent: data-analyst
Tools: database-query, data-transformer, file-operations
Skills: sql-generation, statistical-analysis
```

**Key Concepts:**
- Natural language to SQL
- Data transformation
- Report generation

### 05 - Simple Graph

Sequential graph chaining multiple agents.

```
Graph Type: Sequential
Nodes: research → summarize
Flow: START → research → summarize → END
```

**Key Concepts:**
- Graph definition
- Node configuration
- State management
- Input/output mapping

---

## Advanced Examples

### 06 - Conditional Graph

Graph with conditional routing based on classification.

```
Graph Type: Conditional
Nodes: classify → [technical|research|general]
```

**Key Concepts:**
- Conditional edges
- Classification
- Dynamic routing
- Default fallback

### 07 - Orchestrator Pattern

Central orchestrator coordinating multiple specialized agents.

```
Agent: workflow-orchestrator
Pattern: Hub and spoke
Skills: task-decomposition
```

**Key Concepts:**
- Task decomposition
- Parallel execution
- Error handling & retry
- Result aggregation

### 08 - RAG Integration

Retrieval-Augmented Generation with vector search.

```
Tools: vector-search
Agent: research-agent
Pattern: Retrieve → Generate
```

**Key Concepts:**
- Vector embeddings
- Semantic search
- Context injection
- Citation handling

---

## Running Examples

Each example contains:
- `config.yaml` - Configuration defining agents, tools, and graphs
- `run.py` - Python script demonstrating the example
- `graph.yaml` (if applicable) - Graph definition

To run an example:

```bash
cd examples/01-simple-qa
python run.py
```

---

## Components Used

### Generic Agents
| Agent | Use Cases |
|-------|-----------|
| `conversational-assistant` | Q&A, general help, summarization |
| `research-agent` | Information gathering, analysis |
| `code-assistant` | Code review, debugging, generation |
| `data-analyst` | Data analysis, SQL, reporting |
| `workflow-orchestrator` | Complex task coordination |

### Generic Tools
| Tool | Capabilities |
|------|--------------|
| `http-request` | API calls, web requests |
| `text-processor` | Summarize, extract, classify |
| `data-transformer` | Format conversion, mapping |
| `file-operations` | Read, write, list files |
| `database-query` | SQL queries, parameterized |
| `vector-search` | Semantic similarity search |

### Skills
| Skill | Category |
|-------|----------|
| `information-synthesis` | Reasoning |
| `code-generation` | Coding |
| `task-decomposition` | Planning |
| `sql-generation` | Data |

---

## Graph Types

### Sequential
Agents execute one after another.
```
START → A → B → C → END
```

### Conditional
Routing based on conditions.
```
START → classify → [condition] → A or B → END
```

### Orchestrated
Central coordinator delegates to workers.
```
Orchestrator ↔ [Agent1, Agent2, Agent3, ...]
```

---

## Configuration Reference

### Agent Configuration
```yaml
agent:
  base: research-agent  # Base agent ID
  config:
    research_depth: standard
    max_sources: 5
```

### Tool Configuration
```yaml
tools:
  - id: vector-search
    config:
      top_k: 5
      threshold: 0.7
```

### Graph Node
```yaml
nodes:
  - id: my-node
    type: agent
    agent_id: research-agent
    input_mapping:
      query: "$.user_input"
    output_mapping:
      result: "$.response"
```

### Conditional Edge
```yaml
edges:
  - source: classify
    target: technical-support
    condition:
      type: expression
      expression: "state.category == 'technical'"
```

---

## Next Steps

1. Start with beginner examples to understand basics
2. Progress to intermediate for tool and graph usage
3. Explore advanced patterns for production architectures
4. Combine patterns for your specific use case

For more information, see the main [ADK README](../README.md).
