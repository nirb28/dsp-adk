# Data Insights - Database + Visualization Integration

Complete implementation of database querying and visualization tools working together.

## What Was Built

### 1. Plotly Visualization Tool
**File**: `data/tools/plotly-visualizer.yaml`

Interactive visualization tool supporting:
- **Chart Types**: Bar, line, scatter, pie, histogram, box, heatmap, table
- **Output Formats**: HTML (interactive), JSON, static images
- **Customization**: Themes, colors, dimensions, labels
- **Data Input**: Arrays of dictionaries (perfect for database results)

**Implementation**: `tools/plotly_visualizer.py`
- PlotlyVisualizer class with chart creation methods
- Support for all major chart types
- Automatic output directory management
- Theme and styling support

### 2. Enhanced SQL Database Tool
**File**: `data/tools/sql-database.yaml`

Already created with:
- Natural language to SQL conversion
- Schema awareness
- Sample query training
- Safe execution (read-only)

**Implementation**: `tools/sql_database.py`

### 3. Data Insights Agent
**File**: `data/agents/data-insights-agent.yaml`

Conversational agent that combines both tools:
- Queries databases using natural language
- Creates appropriate visualizations automatically
- Provides data analysis and insights
- Recommends chart types based on data

### 4. Complete Example
**Directory**: `examples/05-data-insights/`

Files:
- `run.py` - Interactive, automated, and test modes
- `README.md` - Comprehensive documentation
- `SETUP.md` - Quick setup guide
- `config.yaml` - Configuration
- `quickstart.bat` - Windows quick start

### 5. Documentation
- `VISUALIZATION_TOOL.md` - Plotly tool documentation
- `DATABASE_TOOL.md` - Database tool documentation (already created)
- `DATA_INSIGHTS_SUMMARY.md` - This file

### 6. Testing
- `test_data_insights.py` - Comprehensive test suite
- Tests both tools separately and together
- Validates agent integration

## How It Works

```
User: "Show me the top 5 customers by spending with a bar chart"
    ↓
Data Insights Agent
    ↓
Step 1: sql-database tool
    - Converts question to SQL
    - Queries database
    - Returns results: [{"name": "John", "total_spent": 1250}, ...]
    ↓
Step 2: plotly-visualizer tool
    - Receives database results
    - Creates bar chart
    - Saves to data/visualizations/bar_20260102_182345.html
    ↓
Agent Response
    - Explains the data
    - Provides insights
    - References the visualization
```

## Quick Start

```bash
# 1. Install dependencies
pip install plotly pandas kaleido

# 2. Create sample database
python scripts/setup_sample_database.py

# 3. Set API key
export NVAPI_KEY=your_key

# 4. Run interactive demo
python examples/05-data-insights/run.py --mode interactive

# 5. Test everything
python test_data_insights.py
```

## Example Usage

### Direct Tool Usage

```python
from app.services.tool_service import ToolService

# Query database
sql_result = await tool_service.execute_tool(
    tool_id="sql-database",
    parameters={
        "question": "What is revenue by category?",
        "mode": "natural"
    }
)

# Create visualization
viz_result = await tool_service.execute_tool(
    tool_id="plotly-visualizer",
    parameters={
        "chart_type": "bar",
        "data": sql_result['results'],
        "x_column": "category",
        "y_column": "revenue",
        "title": "Revenue by Category"
    }
)
```

### With Agent

```python
from app.services.agent_executor import AgentExecutor

response = await executor.execute_agent(
    agent_id="data-insights",
    user_message="Show me revenue by category with a bar chart",
    conversation_id="session-123",
    stream=True
)
```

## Chart Types Supported

| Chart Type | Use Case | Example |
|------------|----------|---------|
| Bar | Category comparisons | Revenue by product category |
| Line | Trends over time | Monthly revenue trend |
| Pie | Proportions | Order status distribution |
| Scatter | Relationships | Orders vs revenue correlation |
| Histogram | Distributions | Customer spending distribution |
| Box | Statistical analysis | Sales distribution by region |
| Heatmap | Correlations | Variable correlation matrix |
| Table | Data display | Top customers list |

## Files Created

### Tool Configurations
- `data/tools/plotly-visualizer.yaml` (NEW)
- `data/tools/sql-database.yaml` (already created)

### Tool Implementations
- `tools/plotly_visualizer.py` (NEW)
- `tools/sql_database.py` (already created)

### Agent Configuration
- `data/agents/data-insights-agent.yaml` (NEW)

### Example Files
- `examples/05-data-insights/run.py` (NEW)
- `examples/05-data-insights/README.md` (NEW)
- `examples/05-data-insights/SETUP.md` (NEW)
- `examples/05-data-insights/config.yaml` (NEW)
- `examples/05-data-insights/quickstart.bat` (NEW)

### Documentation
- `VISUALIZATION_TOOL.md` (NEW)
- `DATA_INSIGHTS_SUMMARY.md` (NEW)
- `DATABASE_TOOL.md` (already created)

### Testing
- `test_data_insights.py` (NEW)
- `test_sql_database_tool.py` (already created)

### Dependencies
- Updated `requirements.txt` with plotly, pandas, kaleido

## Key Features

### Tool Composition
Demonstrates how multiple specialized tools work together:
- **sql-database**: Data retrieval specialist
- **plotly-visualizer**: Visualization specialist
- **data-insights agent**: Orchestrator

### Interactive Visualizations
All charts are interactive HTML files with:
- Zoom and pan capabilities
- Hover tooltips with details
- Legend toggling
- Responsive design

### Smart Agent Behavior
The agent automatically:
- Chooses appropriate chart types
- Formats data correctly
- Provides insights and analysis
- Explains visualizations

### Flexible Configuration
Customize:
- Chart themes and colors
- Output formats (HTML, JSON, images)
- Dimensions and styling
- Database connections

## Example Questions

Try these with the interactive demo:

1. **"Show me the top 5 customers by spending with a bar chart"**
   - Queries database for top customers
   - Creates bar chart
   - Explains spending patterns

2. **"Create a pie chart of revenue by product category"**
   - Aggregates revenue by category
   - Creates pie chart
   - Shows category distribution

3. **"Visualize the monthly revenue trend as a line chart"**
   - Calculates monthly revenue
   - Creates line chart
   - Identifies trends

4. **"Compare revenue across product categories and visualize it"**
   - Analyzes category performance
   - Creates appropriate chart
   - Provides comparative insights

## Architecture Pattern

This implementation demonstrates **tool composition** - a powerful pattern where:

1. **Specialized Tools**: Each tool does one thing well
   - sql-database: Query data
   - plotly-visualizer: Create charts

2. **Orchestration**: Agent combines tools intelligently
   - Understands user intent
   - Calls tools in sequence
   - Synthesizes results

3. **Extensibility**: Easy to add more tools
   - Add statistical analysis tool
   - Add export/reporting tool
   - Add data transformation tool

## Testing

Run comprehensive tests:

```bash
# Test everything
python test_data_insights.py

# Test database tool only
python test_sql_database_tool.py

# Test with example
python examples/05-data-insights/run.py --mode test
```

## Output

All visualizations saved to: `data/visualizations/`

Example files:
- `bar_20260102_182345.html` - Bar chart
- `pie_20260102_182401.html` - Pie chart
- `line_20260102_182515.html` - Line chart

## Dependencies Added

```txt
# Visualization
plotly>=5.18.0
pandas>=2.0.0
kaleido>=0.2.1
```

## Next Steps

### Extend Functionality
1. Add more chart types (3D plots, maps, etc.)
2. Create dashboard combining multiple charts
3. Add export to PDF/PowerPoint
4. Implement real-time data updates

### Connect Real Data
1. Add PostgreSQL/MySQL database connections
2. Connect to data warehouses
3. Integrate with APIs
4. Add data transformation tools

### Enhance Agent
1. Add statistical analysis capabilities
2. Implement predictive analytics
3. Add natural language insights generation
4. Create automated reporting

## Comparison: Before vs After

### Before
- Database tool only
- Manual visualization needed
- Separate steps for query and viz
- No integrated insights

### After
- Database + Visualization tools
- Automatic chart creation
- Single request for query + viz
- Integrated analysis and insights

## Success Criteria

✓ Plotly visualization tool created and working
✓ Multiple chart types supported
✓ Integration with database tool successful
✓ Combined agent working correctly
✓ Interactive demo functional
✓ Comprehensive tests passing
✓ Documentation complete

## Summary

Successfully implemented a complete data insights solution that combines:
- **SQL Database Tool**: Natural language to SQL, schema-aware querying
- **Plotly Visualization Tool**: Interactive charts in multiple formats
- **Data Insights Agent**: Intelligent orchestration of both tools
- **Complete Example**: Interactive demo with multiple modes
- **Comprehensive Testing**: Full test coverage
- **Rich Documentation**: Setup guides and API docs

This demonstrates the power of **tool composition** in the ADK, where specialized tools work together to create sophisticated capabilities that are greater than the sum of their parts.
