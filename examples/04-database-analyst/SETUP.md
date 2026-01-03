# Database Analyst Agent - Setup Guide

## Quick Start

### 1. Create Sample Database

```bash
python scripts/setup_sample_database.py
```

This creates `data/databases/sample.db` with:
- 20 customers
- 20 products  
- 100+ orders

### 2. Set API Key

**For NVIDIA (default)**:
```bash
export NVAPI_KEY=your_nvidia_api_key
```

**For OpenAI**:
```bash
export OPENAI_API_KEY=your_openai_key
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export LLM_ENDPOINT=https://api.openai.com/v1
```

### 3. Run Example

**Interactive Mode** (recommended):
```bash
python examples/04-database-analyst/run.py --mode interactive
```

**Automated Demo**:
```bash
python examples/04-database-analyst/run.py --mode auto
```

**Test Tool Directly**:
```bash
python examples/04-database-analyst/run.py --mode test
```

**Quick Start Scripts**:
```bash
# Windows
examples\04-database-analyst\quickstart.bat

# Linux/Mac
chmod +x examples/04-database-analyst/quickstart.sh
./examples/04-database-analyst/quickstart.sh
```

## Test Everything

Run comprehensive test suite:
```bash
python test_sql_database_tool.py
```

This tests:
- Database setup
- Tool loading
- Schema retrieval
- Direct SQL execution
- Natural language to SQL (requires API key)
- Agent loading

## Files Created

### Tool Configuration
- `data/tools/sql-database.yaml` - Tool definition with schema and sample queries

### Tool Implementation
- `tools/sql_database.py` - Python implementation with text-to-SQL

### Database Setup
- `scripts/setup_sample_database.py` - Creates sample SQLite database
- `data/databases/sample.db` - Sample database (created by script)

### Agent Configuration
- `data/agents/database-analyst-agent.yaml` - Agent definition

### Example
- `examples/04-database-analyst/run.py` - Interactive demo
- `examples/04-database-analyst/config.yaml` - Configuration
- `examples/04-database-analyst/README.md` - Documentation
- `examples/04-database-analyst/SETUP.md` - This file
- `examples/04-database-analyst/quickstart.bat` - Windows quick start
- `examples/04-database-analyst/quickstart.sh` - Linux/Mac quick start

### Documentation
- `DATABASE_TOOL.md` - Comprehensive documentation

### Testing
- `test_sql_database_tool.py` - Test suite

## Example Questions

Once running, try:

```
You: Who are the top 5 customers by spending?
You: What is the total revenue by product category?
You: Show me orders from the last 30 days
You: Which customers have never placed an order?
You: What's the monthly revenue trend?
```

## Troubleshooting

### Database Not Found
```bash
python scripts/setup_sample_database.py
```

### API Key Not Set
```bash
export NVAPI_KEY=your_key_here
```

### Tool Not Loading
Check that `data/tools/sql-database.yaml` exists and is valid YAML.

### Import Errors
Ensure you're running from the project root:
```bash
cd /path/to/dsp-adk
python examples/04-database-analyst/run.py
```

## Architecture

```
User Question
    ↓
Database Analyst Agent
    ↓
SQL Database Tool
    ↓
┌─────────────────────┐
│ Text-to-SQL (LLM)   │ ← Schema Context
│                     │ ← Sample Queries  
└─────────────────────┘
    ↓
SQL Validation
    ↓
SQLite Execution
    ↓
Results + Analysis
```

## Key Features

✓ **Natural Language Queries** - Ask questions in plain English
✓ **Schema Awareness** - Understands database structure
✓ **Sample Query Learning** - Uses examples to improve SQL generation
✓ **Safe Execution** - Read-only with validation
✓ **Interactive Analysis** - Conversational interface
✓ **Multiple Modes** - Natural language, direct SQL, or schema exploration

## Next Steps

1. **Customize Schema**: Edit `data/tools/sql-database.yaml` to add your database
2. **Add Sample Queries**: Include more training examples
3. **Adjust Agent**: Modify `data/agents/database-analyst-agent.yaml` for different behavior
4. **Connect Real Database**: Add PostgreSQL/MySQL connections

See `DATABASE_TOOL.md` for complete documentation.
