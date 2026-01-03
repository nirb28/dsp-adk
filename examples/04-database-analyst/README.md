# Database Analyst Agent Example

This example demonstrates an AI agent that can query databases using natural language, following the vanna.ai model for AI-powered database interactions.

## Features

- **Natural Language to SQL**: Convert questions into SQL queries automatically
- **Schema Awareness**: Agent understands database structure and relationships
- **Sample Query Learning**: Uses example queries to improve SQL generation
- **Safe Execution**: Read-only queries with validation
- **Interactive Analysis**: Ask follow-up questions and explore data

## Setup

1. **Create the sample database**:
```bash
python scripts/setup_sample_database.py
```

This creates a SQLite database at `data/databases/sample.db` with:
- 20 customers from various countries
- 20 products across multiple categories
- 100+ orders with different statuses

2. **Set environment variables**:
```bash
# For NVIDIA endpoint (default)
export NVAPI_KEY=your_nvidia_api_key

# Or use OpenAI
export OPENAI_API_KEY=your_openai_key
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export LLM_ENDPOINT=https://api.openai.com/v1
```

3. **Run the example**:
```bash
python examples/04-database-analyst/run.py
```

## Database Schema

### Customers Table
- `customer_id`: Unique identifier
- `name`: Customer name
- `email`: Email address
- `country`: Customer country
- `signup_date`: Registration date
- `total_spent`: Total amount spent

### Orders Table
- `order_id`: Unique identifier
- `customer_id`: Foreign key to customers
- `order_date`: Order date
- `amount`: Order total
- `status`: pending, completed, cancelled
- `product_category`: Product category

### Products Table
- `product_id`: Unique identifier
- `name`: Product name
- `category`: Product category
- `price`: Product price
- `stock`: Available quantity
- `supplier`: Supplier name

## Example Questions

Try asking the agent:

1. **Simple queries**:
   - "Who are the top 5 customers by spending?"
   - "Show me recent orders from the last 30 days"
   - "Which products are low on stock?"

2. **Analytical queries**:
   - "What is the total revenue by product category?"
   - "Show me the monthly revenue trend"
   - "Which customers have never placed an order?"

3. **Complex queries**:
   - "What's the average order value by country?"
   - "Show customer lifetime value distribution"
   - "Compare revenue across different product categories"

4. **Schema exploration**:
   - "What tables are available?"
   - "Show me the database schema"
   - "What data do you have about customers?"

## How It Works

1. **Schema Context**: The tool provides the LLM with complete schema information including table descriptions, column types, and relationships.

2. **Sample Queries**: Pre-defined example queries help the LLM understand query patterns and generate better SQL.

3. **Text-to-SQL**: The LLM converts natural language questions into SQL queries using the schema and examples as context.

4. **Validation**: Generated SQL is validated for safety (read-only, no dangerous operations).

5. **Execution**: Safe queries are executed and results are returned to the agent.

6. **Analysis**: The agent interprets results and provides insights in natural language.

## Tool Configuration

The `sql-database` tool is configured in `data/tools/sql-database.yaml` with:

- **Database connections**: SQLite, PostgreSQL, MySQL support
- **Schema definitions**: Complete table and column metadata
- **Sample queries**: Training examples for text-to-SQL
- **LLM configuration**: Provider, model, and parameters
- **Safety settings**: Read-only mode, query validation

## Architecture

```
User Question
    ↓
Agent (database-analyst)
    ↓
SQL Database Tool
    ↓
Text-to-SQL (LLM) ← Schema Context + Sample Queries
    ↓
SQL Validation
    ↓
Query Execution (SQLite)
    ↓
Results
    ↓
Agent Analysis & Response
```

## Extending

### Add More Databases

Edit `data/tools/sql-database.yaml` to add database connections:

```yaml
implementation:
  databases:
    production:
      type: postgresql
      connection_string_env: PROD_DB_URL
      schema: {...}
      sample_queries: [...]
```

### Add Sample Queries

Add more training examples to improve SQL generation:

```yaml
sample_queries:
  - purpose: Your query purpose
    question: Natural language question
    sql: |
      SELECT ...
      FROM ...
      WHERE ...
```

### Customize Agent Behavior

Modify `data/agents/database-analyst-agent.yaml`:
- Change system prompt for different analysis styles
- Adjust LLM parameters (temperature, max_tokens)
- Add more tools for enhanced capabilities

## Vanna.ai Inspiration

This implementation follows the vanna.ai model:
- **Schema awareness**: LLM understands database structure
- **Training data**: Sample queries improve accuracy
- **Iterative refinement**: Agent can retry with better queries
- **Safety first**: Read-only with validation
- **Natural interaction**: Conversational interface

## Troubleshooting

**SQL Generation Issues**:
- Add more sample queries for your use case
- Adjust LLM temperature (lower = more precise)
- Provide clearer schema descriptions

**Connection Errors**:
- Verify database path in tool configuration
- Check environment variables are set
- Ensure database file exists

**Permission Errors**:
- Tool is read-only by default
- Modify `read_only` setting if needed (not recommended)
