# Data Insights Agent - Database + Visualization

This example demonstrates an AI agent that combines **database querying** and **interactive visualization** to provide comprehensive data insights.

## Features

- **Natural Language Queries**: Ask questions about data in plain English
- **Automatic Visualization**: Agent creates appropriate charts for the data
- **Multiple Chart Types**: Bar, line, pie, scatter, histogram, box plots, and more
- **Interactive Charts**: Plotly-powered interactive HTML visualizations
- **Smart Recommendations**: Agent suggests best chart types for your data
- **Two-Tool Integration**: Seamlessly combines sql-database and plotly-visualizer tools

## How It Works

```
User Question
    ↓
Data Insights Agent
    ↓
┌─────────────────────┐
│ 1. Query Database   │ (sql-database tool)
│    - Text-to-SQL    │
│    - Get results    │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ 2. Create Chart     │ (plotly-visualizer tool)
│    - Choose type    │
│    - Generate viz   │
└─────────────────────┘
    ↓
Analysis + Insights
```

## Setup

### 1. Create Sample Database

```bash
python scripts/setup_sample_database.py
```

### 2. Install Plotly

```bash
pip install plotly pandas
```

### 3. Set API Key

```bash
# For NVIDIA (default)
export NVAPI_KEY=your_nvidia_api_key

# Or for OpenAI
export OPENAI_API_KEY=your_openai_key
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
```

### 4. Run Example

```bash
# Interactive mode (recommended)
python examples/05-data-insights/run.py --mode interactive

# Automated demo
python examples/05-data-insights/run.py --mode auto

# Test tools separately
python examples/05-data-insights/run.py --mode test
```

## Example Questions

### Simple Queries with Visualization

```
You: Show me the top 5 customers by spending with a bar chart
```
→ Agent queries database AND creates bar chart

```
You: Create a pie chart of revenue by product category
```
→ Agent gets category revenue AND creates pie chart

```
You: Visualize the monthly revenue trend as a line chart
```
→ Agent calculates monthly revenue AND creates line chart

### Complex Analysis

```
You: Compare revenue across product categories and visualize it
```
→ Agent analyzes data, creates appropriate visualization, provides insights

```
You: Show customer distribution by country with a chart
```
→ Agent groups by country, creates bar chart, explains patterns

```
You: What's the relationship between order count and total revenue?
```
→ Agent calculates metrics, creates scatter plot, analyzes correlation

## Chart Types

The agent can create:

- **Bar Charts**: Category comparisons (revenue by category, top customers)
- **Line Charts**: Trends over time (monthly revenue, growth patterns)
- **Pie Charts**: Proportions (market share, distribution percentages)
- **Scatter Plots**: Relationships between variables
- **Histograms**: Distributions (customer spending patterns)
- **Box Plots**: Statistical distributions and outliers
- **Heatmaps**: Correlation matrices
- **Tables**: Interactive data tables

## Output

Visualizations are saved to: `data/visualizations/`

Each chart is an interactive HTML file that you can:
- Open in any web browser
- Zoom, pan, and hover for details
- Save as static images
- Share with others

## Tools Used

### 1. SQL Database Tool (`sql-database`)
- Converts natural language to SQL
- Executes queries safely (read-only)
- Returns structured data

### 2. Plotly Visualizer Tool (`plotly-visualizer`)
- Creates interactive charts
- Multiple chart types
- Customizable styling
- HTML/JSON/Image export

## Agent Workflow

1. **Understand Question**: Parse user's data question
2. **Query Database**: Use sql-database tool to get data
3. **Analyze Results**: Understand what the data shows
4. **Choose Chart Type**: Select appropriate visualization
5. **Create Visualization**: Use plotly-visualizer tool
6. **Provide Insights**: Explain patterns and findings

## Example Session

```
You: Show me the top 5 customers by spending with a bar chart

Agent: [Using tool: sql-database]
[Using tool: plotly-visualizer]
[Visualization saved: data/visualizations/bar_20260102_182345.html]

I've analyzed the customer spending data and created a bar chart 
showing the top 5 customers. Here's what I found:

1. John Smith leads with $1,250.50 in total spending
2. Emma Johnson is second with $980.25
3. The top 5 customers account for 35% of total revenue
4. All top customers are from USA, UK, or Canada

The bar chart clearly shows the spending gap between the top 
customer and others. You can open the interactive chart to 
explore the details.

You: Now show me revenue by product category

Agent: [Using tool: sql-database]
[Using tool: plotly-visualizer]
[Visualization saved: data/visualizations/pie_20260102_182401.html]

I've created a pie chart showing revenue distribution across 
product categories:

- Electronics: 42% ($8,450)
- Clothing: 28% ($5,640)
- Books: 15% ($3,020)
- Home: 10% ($2,015)
- Sports: 5% ($1,008)

Electronics is clearly the dominant category, generating nearly 
half of all revenue. This suggests focusing marketing efforts 
on electronics could yield the best ROI.
```

## Files

### Agent Configuration
- `data/agents/data-insights-agent.yaml` - Agent with both tools

### Tool Configurations
- `data/tools/sql-database.yaml` - Database query tool
- `data/tools/plotly-visualizer.yaml` - Visualization tool

### Tool Implementations
- `tools/sql_database.py` - Database querying logic
- `tools/plotly_visualizer.py` - Visualization creation logic

### Example
- `examples/05-data-insights/run.py` - Interactive demo
- `examples/05-data-insights/README.md` - This file
- `examples/05-data-insights/config.yaml` - Configuration

## Customization

### Add Custom Chart Types

Edit `tools/plotly_visualizer.py` to add new chart creators:

```python
def _create_custom_chart(self, data, **kwargs):
    # Your custom chart logic
    fig = go.Figure(...)
    return fig
```

### Modify Agent Behavior

Edit `data/agents/data-insights-agent.yaml`:

```yaml
system_prompt: |
  Your custom instructions for the agent...
  - Focus on specific analysis types
  - Use particular chart styles
  - Provide domain-specific insights
```

### Change Visualization Defaults

Edit `data/tools/plotly-visualizer.yaml`:

```yaml
implementation:
  chart_defaults:
    bar:
      bargap: 0.3
      color: custom_color
    line:
      line_width: 3
```

## Advanced Usage

### Programmatic Access

```python
from app.services.tool_service import ToolService

# Query database
sql_result = await tool_service.execute_tool(
    tool_id="sql-database",
    parameters={
        "question": "What are the top products?",
        "mode": "natural"
    }
)

# Create visualization
viz_result = await tool_service.execute_tool(
    tool_id="plotly-visualizer",
    parameters={
        "chart_type": "bar",
        "data": sql_result['results'],
        "x_column": "product_name",
        "y_column": "sales",
        "title": "Top Products by Sales"
    }
)
```

### Multi-Chart Analysis

Ask the agent to create multiple visualizations:

```
You: Analyze customer data from multiple angles - show me 
spending distribution, geographic distribution, and order 
frequency. Create separate charts for each.
```

## Troubleshooting

### Charts Not Opening
- Check `data/visualizations/` folder exists
- Verify file permissions
- Try opening HTML files manually in browser

### Visualization Errors
- Ensure plotly is installed: `pip install plotly`
- Check data has required columns
- Verify chart type matches data structure

### Agent Not Using Both Tools
- Check both tools are loaded
- Verify agent configuration includes both tools
- Try more explicit requests: "query the database AND create a chart"

## Performance Tips

1. **Limit Data**: Use LIMIT in queries for large datasets
2. **Cache Results**: Agent remembers conversation context
3. **Specific Requests**: Be clear about desired chart type
4. **Batch Questions**: Ask related questions in sequence

## Next Steps

1. **Add More Chart Types**: Extend plotly_visualizer.py
2. **Custom Themes**: Create branded visualization themes
3. **Export Options**: Add PDF/PNG export capabilities
4. **Dashboard Mode**: Combine multiple charts in one view
5. **Real-time Data**: Connect to live databases

## Architecture

This example demonstrates **tool composition** - combining multiple specialized tools to create powerful capabilities:

- **sql-database**: Data retrieval specialist
- **plotly-visualizer**: Visualization specialist
- **data-insights agent**: Orchestrator that uses both

This pattern can be extended to any combination of tools!
