# Data Insights Agent - Setup Guide

Quick setup guide for the Database + Visualization example.

## Prerequisites

1. **Python 3.8+**
2. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### 1. Install Visualization Dependencies

```bash
pip install plotly pandas kaleido
```

### 2. Create Sample Database

```bash
python scripts/setup_sample_database.py
```

This creates `data/databases/sample.db` with realistic e-commerce data.

### 3. Set API Key

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

### 4. Run Example

**Interactive Mode** (recommended):
```bash
python examples/05-data-insights/run.py --mode interactive
```

**Automated Demo**:
```bash
python examples/05-data-insights/run.py --mode auto
```

**Test Tools**:
```bash
python examples/05-data-insights/run.py --mode test
```

**Quick Start Script**:
```bash
# Windows
examples\05-data-insights\quickstart.bat
```

## What You'll Get

### Tools
1. **sql-database**: Query databases with natural language
2. **plotly-visualizer**: Create interactive charts

### Agent
- **data-insights**: Combines both tools for comprehensive analysis

### Example Interactions

```
You: Show me the top 5 customers by spending with a bar chart

Agent: [Uses sql-database to query]
        [Uses plotly-visualizer to create chart]
        [Provides analysis and insights]
        
Result: Interactive bar chart saved to data/visualizations/
```

## Testing

Run comprehensive tests:
```bash
python test_data_insights.py
```

Tests:
- ✓ Plotly tool loading
- ✓ Bar chart creation
- ✓ Pie chart creation
- ✓ Line chart creation
- ✓ Database + Visualization integration
- ✓ Agent loading
- ✓ Table visualization

## Output

All visualizations are saved to: `data/visualizations/`

Each chart is an interactive HTML file you can:
- Open in any browser
- Zoom, pan, hover for details
- Share with others
- Embed in web pages

## Example Questions

Try these with the interactive demo:

### Simple Queries + Charts
```
Show me the top 5 customers by spending with a bar chart
Create a pie chart of revenue by product category
Visualize the monthly revenue trend as a line chart
```

### Analytical Questions
```
Compare revenue across product categories and visualize it
Show customer distribution by country with a chart
What's the relationship between order count and revenue?
```

### Multi-Step Analysis
```
What are the top selling categories? Show me a chart.
Which countries have the most customers? Visualize this.
How has revenue changed over time? Create a trend chart.
```

## Files Created

### Tools
- `data/tools/sql-database.yaml` - Database query tool
- `data/tools/plotly-visualizer.yaml` - Visualization tool
- `tools/sql_database.py` - Database implementation
- `tools/plotly_visualizer.py` - Visualization implementation

### Agent
- `data/agents/data-insights-agent.yaml` - Combined agent

### Example
- `examples/05-data-insights/run.py` - Interactive demo
- `examples/05-data-insights/README.md` - Full documentation
- `examples/05-data-insights/config.yaml` - Configuration
- `examples/05-data-insights/SETUP.md` - This file

### Documentation
- `DATABASE_TOOL.md` - Database tool docs
- `VISUALIZATION_TOOL.md` - Visualization tool docs

### Testing
- `test_sql_database_tool.py` - Database tests
- `test_data_insights.py` - Combined tests

## Troubleshooting

### Database Not Found
```bash
python scripts/setup_sample_database.py
```

### API Key Not Set
```bash
export NVAPI_KEY=your_key_here
```

### Plotly Not Installed
```bash
pip install plotly pandas kaleido
```

### Visualizations Not Created
- Check `data/visualizations/` directory exists
- Verify file permissions
- Check tool configuration

### Agent Not Using Both Tools
- Verify both tools are loaded
- Check agent configuration includes both tools
- Try explicit requests: "query the database AND create a chart"

## Architecture

```
User Question
    ↓
Data Insights Agent
    ↓
┌─────────────────────┐
│ 1. SQL Database     │
│    - Text-to-SQL    │
│    - Query data     │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ 2. Plotly Viz       │
│    - Choose chart   │
│    - Create viz     │
└─────────────────────┘
    ↓
Insights + Analysis
```

## Next Steps

1. **Try Different Charts**: Experiment with pie, line, scatter plots
2. **Custom Queries**: Write your own SQL queries
3. **Add Data**: Extend the sample database
4. **New Visualizations**: Create custom chart types
5. **Real Database**: Connect to production databases

## Support

- Check `README.md` for detailed documentation
- Review `DATABASE_TOOL.md` for database features
- Review `VISUALIZATION_TOOL.md` for chart options
- Run tests to verify setup: `python test_data_insights.py`

## Key Features

✓ **Natural Language Queries** - Ask questions in plain English
✓ **Automatic Visualization** - Agent creates appropriate charts
✓ **Interactive Charts** - Plotly-powered HTML visualizations
✓ **Multiple Chart Types** - Bar, line, pie, scatter, and more
✓ **Tool Composition** - Seamless integration of database + visualization
✓ **Smart Recommendations** - Agent suggests best chart types
