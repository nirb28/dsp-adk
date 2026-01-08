# SQL Database Tool - AI-Powered Database Querying

This document describes the SQL Database Tool implementation in the ADK, inspired by vanna.ai and other AI database integrations.

## Overview

The SQL Database Tool enables AI agents to query databases using natural language. It combines:
- **Schema Awareness**: Complete understanding of database structure
- **Text-to-SQL**: LLM-powered conversion of natural language to SQL
- **Sample Query Learning**: Training examples improve SQL generation
- **Safe Execution**: Read-only queries with validation
- **Multiple Databases**: Support for SQLite, PostgreSQL, MySQL

## Architecture

```
Natural Language Question
         ↓
    SQL Database Tool
         ↓
    ┌────────────────┐
    │  Text-to-SQL   │ ← Schema Context
    │  (LLM)         │ ← Sample Queries
    └────────────────┘
         ↓
    SQL Validation
         ↓
    Query Execution
         ↓
    Results + Metadata
```

## Components

### 1. Tool Configuration (`data/tools/sql-database.yaml`)

Defines the tool with:
- **Parameters**: question, mode, database_name, limit
- **Database Connections**: Multiple named databases
- **Schema Definitions**: Tables, columns, types, relationships
- **Sample Queries**: Training examples with purpose and SQL
- **LLM Configuration**: Provider, model, endpoint settings
- **Safety Settings**: Read-only mode, allowed operations, blocked keywords

### 2. Tool Implementation (`tools/sql_database.py`)

Python implementation providing:
- **SQLDatabaseTool Class**: Core functionality
- **Connection Management**: Database connections
- **SQL Validation**: Safety checks
- **Schema Context Generation**: Format schema for LLM
- **Text-to-SQL Conversion**: LLM-powered query generation
- **Query Execution**: Safe SQL execution
- **Result Formatting**: Structured response

### 3. Sample Database (`scripts/setup_sample_database.py`)

Creates a realistic e-commerce database with:
- **Customers Table**: 20 customers with contact info and spending
- **Products Table**: 20 products across multiple categories
- **Orders Table**: 100+ orders with various statuses

### 4. Database Analyst Agent (`data/agents/database-analyst-agent.yaml`)

Conversational agent that:
- Understands natural language questions
- Uses the SQL database tool
- Provides insights and analysis
- Explains results clearly

## Features

### Schema Awareness

The tool provides complete schema information to the LLM:

```yaml
schema:
  tables:
    - name: customers
      description: Customer information and contact details
      columns:
        - name: customer_id
          type: INTEGER
          description: Unique customer identifier
          primary_key: true
        - name: name
          type: TEXT
          description: Customer full name
        # ... more columns
```

### Sample Queries

Training examples help the LLM generate better SQL:

```yaml
sample_queries:
  - purpose: Find top spending customers
    question: Who are the top 5 customers by total spending?
    sql: |
      SELECT name, email, country, total_spent 
      FROM customers 
      ORDER BY total_spent DESC 
      LIMIT 5
```

### Query Modes

1. **Natural Language Mode** (`mode: natural`):
   - Converts questions to SQL using LLM
   - Uses schema and sample queries as context
   - Best for complex analytical queries

2. **Direct SQL Mode** (`mode: sql`):
   - Executes SQL directly
   - Still validates for safety
   - Best for precise control

3. **Schema Mode** (`mode: schema`):
   - Returns database schema information
   - No query execution
   - Best for exploration

### Safety Features

- **Read-Only**: Only SELECT queries allowed by default
- **Keyword Blocking**: Blocks DROP, DELETE, UPDATE, etc.
- **Row Limits**: Maximum rows returned (configurable)
- **Timeout Protection**: Query timeout limits
- **SQL Validation**: Pre-execution validation

## Usage

### Basic Usage

```python
from app.services.tool_service import ToolService

tool_service = ToolService(config)

# Natural language query
result = await tool_service.execute_tool(
    tool_id="sql-database",
    parameters={
        "question": "Who are the top 5 customers by spending?",
        "mode": "natural",
        "limit": 5
    }
)

print(result['generated_sql'])
print(result['results'])
```

### With Agent

```python
from app.services.agent_executor import AgentExecutor

executor = AgentExecutor(config)

response = await executor.execute_agent(
    agent_id="database-analyst",
    user_message="What is the total revenue by product category?",
    conversation_id="session-123"
)
```

### Direct Tool Call

```python
from tools.sql_database import query_database

result = await query_database(
    question="Show me recent orders",
    mode="natural",
    database_name="default",
    limit=10,
    tool_config=tool_config
)
```

## Configuration

### Adding a Database

Edit `data/tools/sql-database.yaml`:

```yaml
implementation:
  databases:
    production:
      type: postgresql
      connection_string_env: PROD_DB_URL
      description: Production database
      
      schema:
        tables:
          - name: users
            description: User accounts
            columns:
              - name: user_id
                type: INTEGER
                primary_key: true
              # ... more columns
      
      sample_queries:
        - purpose: Get active users
          question: How many active users do we have?
          sql: SELECT COUNT(*) FROM users WHERE status = 'active'
```

### LLM Configuration

Configure the LLM for text-to-SQL:

```yaml
llm_config:
  provider: openai_compatible
  model: meta/llama-3.3-70b-instruct
  endpoint: https://integrate.api.nvidia.com/v1
  api_key: ${LLM_API_KEY}
  temperature: 0.1  # Lower for more precise SQL
  max_tokens: 500
```

### Safety Settings

```yaml
read_only: true
max_rows: 1000
timeout: 30
allowed_operations:
  - SELECT
blocked_keywords:
  - DROP
  - DELETE
  - UPDATE
  - INSERT
```

## Example Questions

### Simple Queries
- "Who are the top 5 customers by spending?"
- "Show me recent orders from the last 30 days"
- "Which products are low on stock?"

### Analytical Queries
- "What is the total revenue by product category?"
- "Show me the monthly revenue trend"
- "Which customers have never placed an order?"

### Complex Queries
- "What's the average order value by country?"
- "Show customer lifetime value distribution"
- "Compare revenue across different product categories"

### Schema Exploration
- "What tables are available?"
- "Show me the database schema"
- "What data do you have about customers?"

## Response Format

```json
{
  "success": true,
  "mode": "natural",
  "question": "Who are the top 5 customers?",
  "generated_sql": "SELECT name, email, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5",
  "results": [
    {"name": "John Smith", "email": "john@email.com", "total_spent": 1250.50},
    {"name": "Emma Johnson", "email": "emma@email.com", "total_spent": 980.25}
  ],
  "row_count": 5,
  "execution_time": 0.023,
  "database": "default"
}
```

## Best Practices

### Schema Design

1. **Descriptive Names**: Use clear table and column names
2. **Rich Descriptions**: Provide detailed descriptions for LLM context
3. **Relationships**: Document foreign keys and relationships
4. **Data Types**: Specify accurate data types

### Sample Queries

1. **Coverage**: Include examples for common query patterns
2. **Variety**: Cover simple, analytical, and complex queries
3. **Purpose**: Clearly state what each query accomplishes
4. **Quality**: Use well-formed, efficient SQL

### LLM Configuration

1. **Temperature**: Use low temperature (0.1-0.2) for precise SQL
2. **Model Selection**: Use capable models (GPT-4, Llama 3.3 70B+)
3. **Context**: Provide complete schema and examples
4. **Prompting**: Clear instructions in system prompt

### Security

1. **Read-Only**: Keep read_only=true for production
2. **Validation**: Always validate SQL before execution
3. **Limits**: Set appropriate row and timeout limits
4. **Credentials**: Use environment variables for sensitive data

## Troubleshooting

### SQL Generation Issues

**Problem**: Generated SQL is incorrect or inefficient

**Solutions**:
- Add more sample queries for similar patterns
- Lower LLM temperature for more precise output
- Improve schema descriptions
- Use a more capable LLM model

### Connection Errors

**Problem**: Cannot connect to database

**Solutions**:
- Verify connection string/path
- Check environment variables
- Ensure database exists and is accessible
- Verify credentials

### Validation Errors

**Problem**: SQL fails validation

**Solutions**:
- Check allowed_operations list
- Review blocked_keywords
- Ensure query is read-only
- Verify SQL syntax

### Performance Issues

**Problem**: Queries are slow

**Solutions**:
- Add appropriate indexes to database
- Reduce row limits
- Optimize sample queries
- Set lower timeout values

## Extending

### Adding Database Types

Extend `_get_connection()` in `tools/sql_database.py`:

```python
def _get_connection(self, database_name: str):
    db_config = self.databases[database_name]
    db_type = db_config.get('type')
    
    if db_type == 'postgresql':
        import psycopg2
        return psycopg2.connect(os.getenv(db_config['connection_string_env']))
    elif db_type == 'mysql':
        import mysql.connector
        return mysql.connector.connect(...)
```

### Custom Validation

Add custom validation rules:

```python
def _validate_sql(self, sql: str):
    # Custom validation logic
    if 'UNION' in sql.upper() and not self.allow_unions:
        return False, "UNION queries not allowed"
    
    return True, None
```

### Query Optimization

Add query optimization hints:

```python
def _optimize_sql(self, sql: str):
    # Add indexes, rewrite joins, etc.
    return optimized_sql
```

## Vanna.ai Comparison

This implementation follows vanna.ai principles:

| Feature | Vanna.ai | ADK SQL Tool |
|---------|----------|--------------|
| Schema Awareness | ✓ | ✓ |
| Sample Query Training | ✓ | ✓ |
| Text-to-SQL | ✓ | ✓ |
| Multiple Databases | ✓ | ✓ |
| Safety Validation | ✓ | ✓ |
| Agent Integration | Limited | ✓ Full |
| Tool Ecosystem | Standalone | ✓ Part of ADK |
| Streaming Support | Limited | ✓ Full |

## Files

- `data/tools/sql-database.yaml` - Tool configuration
- `tools/sql_database.py` - Tool implementation
- `scripts/setup_sample_database.py` - Database setup script
- `data/agents/database-analyst-agent.yaml` - Agent configuration
- `examples/04-database-analyst/` - Complete example
- `DATABASE_TOOL.md` - This documentation

## Support

For issues or questions:
1. Check the example in `examples/04-database-analyst/`
2. Review sample queries in tool configuration
3. Test with `--mode test` to verify tool functionality
4. Check logs for detailed error messages
