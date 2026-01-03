# Plotly Visualization Tool

Interactive data visualization tool for the ADK using Plotly.

## Overview

The Plotly Visualization Tool creates interactive, publication-quality charts from data arrays. It integrates seamlessly with other tools (especially the SQL Database Tool) to provide comprehensive data analysis capabilities.

## Features

- **Multiple Chart Types**: Bar, line, scatter, pie, histogram, box plots, heatmaps, tables
- **Interactive Output**: HTML files with zoom, pan, hover capabilities
- **Multiple Formats**: HTML, JSON, static images (PNG, SVG)
- **Customizable Styling**: Themes, colors, dimensions
- **Data Flexibility**: Works with arrays of dictionaries (perfect for database results)

## Chart Types

### Bar Charts
Compare categories or show rankings.

```python
{
    "chart_type": "bar",
    "data": [
        {"category": "Electronics", "revenue": 8450},
        {"category": "Clothing", "revenue": 5640}
    ],
    "x_column": "category",
    "y_column": "revenue",
    "title": "Revenue by Category"
}
```

### Line Charts
Show trends over time or continuous data.

```python
{
    "chart_type": "line",
    "data": [
        {"month": "2024-01", "revenue": 12500},
        {"month": "2024-02", "revenue": 15200}
    ],
    "x_column": "month",
    "y_column": "revenue",
    "title": "Monthly Revenue Trend"
}
```

### Pie Charts
Display proportions and percentages.

```python
{
    "chart_type": "pie",
    "data": [
        {"status": "Completed", "count": 85},
        {"status": "Pending", "count": 12}
    ],
    "x_column": "status",
    "y_column": "count",
    "title": "Order Status Distribution"
}
```

### Scatter Plots
Show relationships between variables.

```python
{
    "chart_type": "scatter",
    "data": [
        {"orders": 10, "revenue": 1250},
        {"orders": 15, "revenue": 1890}
    ],
    "x_column": "orders",
    "y_column": "revenue",
    "title": "Orders vs Revenue"
}
```

### Histograms
Display data distributions.

```python
{
    "chart_type": "histogram",
    "data": [
        {"spending": 125}, {"spending": 340}, {"spending": 890}
    ],
    "x_column": "spending",
    "title": "Customer Spending Distribution"
}
```

### Box Plots
Show statistical distributions with quartiles.

```python
{
    "chart_type": "box",
    "data": [
        {"category": "A", "value": 100},
        {"category": "A", "value": 120}
    ],
    "x_column": "category",
    "y_column": "value",
    "title": "Value Distribution by Category"
}
```

### Heatmaps
Visualize correlation matrices or 2D data.

```python
{
    "chart_type": "heatmap",
    "data": [
        {"var1": 0.8, "var2": 0.6, "var3": 0.3},
        {"var1": 0.6, "var2": 1.0, "var3": 0.5}
    ],
    "title": "Correlation Matrix"
}
```

### Interactive Tables
Display data in sortable, filterable tables.

```python
{
    "chart_type": "table",
    "data": [
        {"name": "John", "sales": 1250, "region": "North"},
        {"name": "Emma", "sales": 980, "region": "South"}
    ],
    "title": "Sales by Representative"
}
```

## Parameters

### Required
- `chart_type`: Type of chart (bar, line, scatter, pie, histogram, box, heatmap, table)
- `data`: Array of dictionaries with data

### Chart-Specific
- `x_column`: Column for x-axis (required for most charts)
- `y_column`: Column for y-axis (required for most charts)
- `color_column`: Column for color grouping (optional)

### Styling
- `title`: Chart title
- `x_label`: X-axis label
- `y_label`: Y-axis label
- `theme`: Plotly theme (plotly, plotly_white, plotly_dark, ggplot2, seaborn, simple_white)
- `width`: Chart width in pixels (default: 800)
- `height`: Chart height in pixels (default: 600)
- `show_legend`: Show/hide legend (default: true)
- `orientation`: Chart orientation - 'v' or 'h' for bar charts (default: 'v')

### Output
- `output_format`: Format (html, json, image) (default: html)
- `output_path`: Custom file path (optional)

## Usage

### With Tool Service

```python
from app.services.tool_service import ToolService

tool_service = ToolService(config)

result = await tool_service.execute_tool(
    tool_id="plotly-visualizer",
    parameters={
        "chart_type": "bar",
        "data": [
            {"product": "Laptop", "sales": 1250},
            {"product": "Mouse", "sales": 340}
        ],
        "x_column": "product",
        "y_column": "sales",
        "title": "Product Sales",
        "theme": "plotly_white"
    }
)

print(result['output_path'])
```

### With Database Results

```python
# Query database
sql_result = await tool_service.execute_tool(
    tool_id="sql-database",
    parameters={
        "question": "SELECT category, SUM(revenue) as total FROM sales GROUP BY category",
        "mode": "sql"
    }
)

# Visualize results
viz_result = await tool_service.execute_tool(
    tool_id="plotly-visualizer",
    parameters={
        "chart_type": "bar",
        "data": sql_result['results'],
        "x_column": "category",
        "y_column": "total",
        "title": "Revenue by Category"
    }
)
```

### With Agent

The Data Insights Agent automatically uses both tools:

```python
response = await executor.execute_agent(
    agent_id="data-insights",
    user_message="Show me revenue by category with a bar chart"
)
```

## Output

Visualizations are saved to: `data/visualizations/`

### HTML Output (Default)
- Interactive charts that can be opened in any browser
- Zoom, pan, hover for details
- Can be embedded in web pages
- Shareable files

### JSON Output
- Plotly JSON specification
- Can be loaded and modified programmatically
- Useful for custom integrations

### Image Output
- Static PNG, JPG, or SVG files
- Requires kaleido package
- Good for reports and presentations

## Themes

Available themes:
- `plotly`: Default Plotly theme
- `plotly_white`: Clean white background
- `plotly_dark`: Dark theme
- `ggplot2`: R's ggplot2 style
- `seaborn`: Seaborn style
- `simple_white`: Minimal white theme
- `none`: No theme

## Integration with Database Tool

Perfect combination for data analysis:

1. **Query Data**: Use sql-database tool to get data
2. **Visualize**: Use plotly-visualizer to create charts
3. **Analyze**: Agent provides insights

Example workflow:
```
User: "Show top customers by spending with a chart"
  ↓
Agent uses sql-database → Gets customer data
  ↓
Agent uses plotly-visualizer → Creates bar chart
  ↓
Agent explains insights from the visualization
```

## Configuration

Tool configuration in `data/tools/plotly-visualizer.yaml`:

```yaml
implementation:
  output_directory: ./data/visualizations
  auto_open: false
  
  default_colors:
    - "#1f77b4"
    - "#ff7f0e"
    - "#2ca02c"
    # ... more colors
  
  chart_defaults:
    bar:
      bargap: 0.2
    line:
      line_width: 2
    scatter:
      marker_size: 8
```

## Response Format

```json
{
  "success": true,
  "chart_type": "bar",
  "output_format": "html",
  "output_path": "/path/to/visualization.html",
  "file_url": "file:///path/to/visualization.html",
  "data_points": 5,
  "plotly_json": {...}
}
```

## Examples

### Example 1: Revenue Analysis

```python
# Get revenue data from database
sql_result = await tool_service.execute_tool(
    tool_id="sql-database",
    parameters={
        "question": "What is revenue by product category?",
        "mode": "natural"
    }
)

# Create pie chart
viz_result = await tool_service.execute_tool(
    tool_id="plotly-visualizer",
    parameters={
        "chart_type": "pie",
        "data": sql_result['results'],
        "x_column": "product_category",
        "y_column": "total_revenue",
        "title": "Revenue Distribution by Category",
        "theme": "plotly_white"
    }
)
```

### Example 2: Trend Analysis

```python
# Get monthly data
sql_result = await tool_service.execute_tool(
    tool_id="sql-database",
    parameters={
        "question": "Show monthly revenue for the last 6 months",
        "mode": "natural"
    }
)

# Create line chart
viz_result = await tool_service.execute_tool(
    tool_id="plotly-visualizer",
    parameters={
        "chart_type": "line",
        "data": sql_result['results'],
        "x_column": "month",
        "y_column": "revenue",
        "title": "Revenue Trend",
        "x_label": "Month",
        "y_label": "Revenue ($)",
        "theme": "seaborn",
        "height": 500
    }
)
```

### Example 3: Comparison

```python
# Get comparison data
data = [
    {"region": "North", "q1": 12500, "q2": 15200, "q3": 14800, "q4": 18900},
    {"region": "South", "q1": 10200, "q2": 11500, "q3": 13200, "q4": 15800}
]

# Create grouped bar chart
viz_result = await tool_service.execute_tool(
    tool_id="plotly-visualizer",
    parameters={
        "chart_type": "bar",
        "data": data,
        "x_column": "region",
        "y_column": "q1",
        "color_column": "region",
        "title": "Quarterly Sales by Region",
        "orientation": "v"
    }
)
```

## Best Practices

### Data Preparation
1. Ensure data is in array of dictionaries format
2. Use consistent column names
3. Handle null/missing values before visualization
4. Aggregate data appropriately for the chart type

### Chart Selection
- **Bar**: Categories, rankings, comparisons
- **Line**: Time series, trends, continuous data
- **Pie**: Proportions (limit to 5-7 slices)
- **Scatter**: Correlations, relationships
- **Histogram**: Distributions, frequency
- **Box**: Statistical analysis, outliers

### Styling
- Use consistent themes across related charts
- Choose appropriate colors for your data
- Keep titles clear and descriptive
- Label axes with units
- Don't overcrowd charts with too much data

### Performance
- Limit data points for large datasets (use aggregation)
- Use appropriate chart types for data size
- Consider static images for very large datasets

## Troubleshooting

### Chart Not Created
- Check data format (must be array of dictionaries)
- Verify column names exist in data
- Ensure chart type matches data structure

### Missing Dependencies
```bash
pip install plotly pandas kaleido
```

### Output Directory Issues
- Tool creates `data/visualizations/` automatically
- Check file permissions
- Verify disk space

### Image Export Issues
- Install kaleido: `pip install kaleido`
- Use HTML format as alternative
- Check output_format parameter

## Files

- `data/tools/plotly-visualizer.yaml` - Tool configuration
- `tools/plotly_visualizer.py` - Implementation
- `data/agents/data-insights-agent.yaml` - Agent using both tools
- `examples/05-data-insights/` - Complete example
- `test_data_insights.py` - Test suite

## Dependencies

```
plotly>=5.18.0
pandas>=2.0.0
kaleido>=0.2.1  # Optional, for image export
```

## Advanced Usage

### Custom Colors

```python
result = await tool_service.execute_tool(
    tool_id="plotly-visualizer",
    parameters={
        "chart_type": "bar",
        "data": data,
        "x_column": "category",
        "y_column": "value",
        # Custom colors via theme or modify tool config
    }
)
```

### Multiple Series

Use `color_column` to create grouped visualizations:

```python
result = await tool_service.execute_tool(
    tool_id="plotly-visualizer",
    parameters={
        "chart_type": "bar",
        "data": data,
        "x_column": "month",
        "y_column": "sales",
        "color_column": "region",  # Creates grouped bars
        "title": "Sales by Region and Month"
    }
)
```

### Programmatic Access

```python
from tools.plotly_visualizer import create_visualization

result = await create_visualization(
    chart_type="line",
    data=my_data,
    x_column="date",
    y_column="value",
    title="My Chart",
    tool_config=config
)
```

## See Also

- `DATABASE_TOOL.md` - SQL Database Tool documentation
- `examples/05-data-insights/README.md` - Complete example
- [Plotly Documentation](https://plotly.com/python/)
