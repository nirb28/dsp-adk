"""
Plotly Visualization Tool

Creates interactive visualizations using Plotly from data arrays or database results.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


class PlotlyVisualizer:
    """Create interactive Plotly visualizations from data."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Plotly visualizer.
        
        Args:
            config: Tool configuration
        """
        self.config = config
        self.output_directory = config.get('output_directory', './data/visualizations')
        self.auto_open = config.get('auto_open', False)
        self.default_colors = config.get('default_colors', px.colors.qualitative.Plotly)
        self.chart_defaults = config.get('chart_defaults', {})
        
        # Ensure output directory exists
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)
    
    def _prepare_data(self, data: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Convert array of dictionaries to column-based format.
        
        Args:
            data: Array of dictionaries
            
        Returns:
            Dictionary with column names as keys and lists as values
        """
        if not data:
            return {}
        
        columns = {}
        for row in data:
            for key, value in row.items():
                if key not in columns:
                    columns[key] = []
                columns[key].append(value)
        
        return columns
    
    def _create_bar_chart(
        self,
        data: List[Dict[str, Any]],
        x_column: str,
        y_column: str,
        color_column: Optional[str] = None,
        orientation: str = 'v',
        **kwargs
    ) -> go.Figure:
        """Create a bar chart."""
        columns = self._prepare_data(data)
        
        if color_column and color_column in columns:
            fig = px.bar(
                data,
                x=x_column,
                y=y_column,
                color=color_column,
                orientation=orientation,
                color_discrete_sequence=self.default_colors
            )
        else:
            fig = px.bar(
                data,
                x=x_column,
                y=y_column,
                orientation=orientation,
                color_discrete_sequence=self.default_colors
            )
        
        # Apply chart defaults
        defaults = self.chart_defaults.get('bar', {})
        if 'bargap' in defaults:
            fig.update_layout(bargap=defaults['bargap'])
        if 'bargroupgap' in defaults:
            fig.update_layout(bargroupgap=defaults['bargroupgap'])
        
        return fig
    
    def _create_line_chart(
        self,
        data: List[Dict[str, Any]],
        x_column: str,
        y_column: str,
        color_column: Optional[str] = None,
        **kwargs
    ) -> go.Figure:
        """Create a line chart."""
        if color_column and color_column in self._prepare_data(data):
            fig = px.line(
                data,
                x=x_column,
                y=y_column,
                color=color_column,
                markers=True,
                color_discrete_sequence=self.default_colors
            )
        else:
            fig = px.line(
                data,
                x=x_column,
                y=y_column,
                markers=True,
                color_discrete_sequence=self.default_colors
            )
        
        # Apply chart defaults
        defaults = self.chart_defaults.get('line', {})
        if 'line_width' in defaults:
            fig.update_traces(line=dict(width=defaults['line_width']))
        if 'marker_size' in defaults:
            fig.update_traces(marker=dict(size=defaults['marker_size']))
        
        return fig
    
    def _create_scatter_chart(
        self,
        data: List[Dict[str, Any]],
        x_column: str,
        y_column: str,
        color_column: Optional[str] = None,
        **kwargs
    ) -> go.Figure:
        """Create a scatter plot."""
        if color_column and color_column in self._prepare_data(data):
            fig = px.scatter(
                data,
                x=x_column,
                y=y_column,
                color=color_column,
                color_discrete_sequence=self.default_colors
            )
        else:
            fig = px.scatter(
                data,
                x=x_column,
                y=y_column,
                color_discrete_sequence=self.default_colors
            )
        
        # Apply chart defaults
        defaults = self.chart_defaults.get('scatter', {})
        if 'marker_size' in defaults:
            fig.update_traces(marker=dict(size=defaults['marker_size']))
        if 'marker_opacity' in defaults:
            fig.update_traces(marker=dict(opacity=defaults['marker_opacity']))
        
        return fig
    
    def _create_pie_chart(
        self,
        data: List[Dict[str, Any]],
        x_column: str,
        y_column: str,
        **kwargs
    ) -> go.Figure:
        """Create a pie chart."""
        fig = px.pie(
            data,
            names=x_column,
            values=y_column,
            color_discrete_sequence=self.default_colors
        )
        
        # Apply chart defaults
        defaults = self.chart_defaults.get('pie', {})
        if 'hole' in defaults:
            fig.update_traces(hole=defaults['hole'])
        if 'textposition' in defaults:
            fig.update_traces(textposition=defaults['textposition'])
        
        return fig
    
    def _create_histogram(
        self,
        data: List[Dict[str, Any]],
        x_column: str,
        **kwargs
    ) -> go.Figure:
        """Create a histogram."""
        fig = px.histogram(
            data,
            x=x_column,
            color_discrete_sequence=self.default_colors
        )
        
        # Apply chart defaults
        defaults = self.chart_defaults.get('histogram', {})
        if 'nbins' in defaults:
            fig.update_traces(nbinsx=defaults['nbins'])
        if 'opacity' in defaults:
            fig.update_traces(opacity=defaults['opacity'])
        
        return fig
    
    def _create_box_plot(
        self,
        data: List[Dict[str, Any]],
        x_column: Optional[str],
        y_column: str,
        color_column: Optional[str] = None,
        **kwargs
    ) -> go.Figure:
        """Create a box plot."""
        if color_column and color_column in self._prepare_data(data):
            fig = px.box(
                data,
                x=x_column,
                y=y_column,
                color=color_column,
                color_discrete_sequence=self.default_colors
            )
        else:
            fig = px.box(
                data,
                x=x_column,
                y=y_column,
                color_discrete_sequence=self.default_colors
            )
        
        # Apply chart defaults
        defaults = self.chart_defaults.get('box', {})
        if 'boxmean' in defaults:
            fig.update_traces(boxmean=defaults['boxmean'])
        
        return fig
    
    def _create_heatmap(
        self,
        data: List[Dict[str, Any]],
        **kwargs
    ) -> go.Figure:
        """Create a heatmap."""
        columns = self._prepare_data(data)
        
        # Get all numeric columns
        numeric_columns = []
        for col_name, col_data in columns.items():
            if all(isinstance(x, (int, float)) for x in col_data if x is not None):
                numeric_columns.append(col_name)
        
        # Create correlation matrix
        import pandas as pd
        df = pd.DataFrame(data)
        corr_matrix = df[numeric_columns].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale=self.chart_defaults.get('heatmap', {}).get('colorscale', 'Viridis'),
            text=corr_matrix.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10}
        ))
        
        return fig
    
    def _create_table(
        self,
        data: List[Dict[str, Any]],
        **kwargs
    ) -> go.Figure:
        """Create an interactive table."""
        columns = self._prepare_data(data)
        
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(columns.keys()),
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=list(columns.values()),
                fill_color='lavender',
                align='left',
                font=dict(size=11)
            )
        )])
        
        return fig
    
    def create_visualization(
        self,
        chart_type: str,
        data: List[Dict[str, Any]],
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        color_column: Optional[str] = None,
        title: str = "",
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        output_format: str = 'html',
        output_path: Optional[str] = None,
        width: int = 800,
        height: int = 600,
        theme: str = 'plotly',
        show_legend: bool = True,
        orientation: str = 'v',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a visualization.
        
        Args:
            chart_type: Type of chart
            data: Data to visualize
            x_column: X-axis column name
            y_column: Y-axis column name
            color_column: Color grouping column
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            output_format: Output format (html, json, image)
            output_path: Output file path
            width: Chart width
            height: Chart height
            theme: Plotly theme
            show_legend: Show legend
            orientation: Chart orientation
            
        Returns:
            Result dictionary with visualization info
        """
        try:
            if not data:
                return {
                    'success': False,
                    'error': 'No data provided'
                }
            
            # Create the appropriate chart
            chart_creators = {
                'bar': self._create_bar_chart,
                'line': self._create_line_chart,
                'scatter': self._create_scatter_chart,
                'pie': self._create_pie_chart,
                'histogram': self._create_histogram,
                'box': self._create_box_plot,
                'heatmap': self._create_heatmap,
                'table': self._create_table
            }
            
            if chart_type not in chart_creators:
                return {
                    'success': False,
                    'error': f"Unsupported chart type: {chart_type}"
                }
            
            # Create figure
            creator = chart_creators[chart_type]
            
            # Prepare kwargs for chart creation
            chart_kwargs = {
                'x_column': x_column,
                'y_column': y_column,
                'color_column': color_column,
                'orientation': orientation
            }
            
            fig = creator(data, **chart_kwargs)
            
            # Update layout
            layout_updates = {
                'title': title,
                'width': width,
                'height': height,
                'showlegend': show_legend
            }
            
            if x_label:
                layout_updates['xaxis_title'] = x_label
            if y_label:
                layout_updates['yaxis_title'] = y_label
            
            # Apply theme
            if theme and theme != 'none':
                layout_updates['template'] = theme
            
            fig.update_layout(**layout_updates)
            
            # Generate output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                extension = 'html' if output_format == 'html' else 'json' if output_format == 'json' else 'png'
                output_path = f"{chart_type}_{timestamp}.{extension}"
            
            full_path = Path(self.output_directory) / output_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save based on format
            if output_format == 'html':
                fig.write_html(str(full_path), auto_open=self.auto_open)
                file_url = f"file:///{full_path.absolute()}"
            elif output_format == 'json':
                with open(full_path, 'w') as f:
                    json.dump(fig.to_dict(), f, indent=2)
                file_url = f"file:///{full_path.absolute()}"
            elif output_format == 'image':
                # Note: Requires kaleido package
                fig.write_image(str(full_path))
                file_url = f"file:///{full_path.absolute()}"
            else:
                return {
                    'success': False,
                    'error': f"Unsupported output format: {output_format}"
                }
            
            return {
                'success': True,
                'chart_type': chart_type,
                'output_format': output_format,
                'output_path': str(full_path),
                'file_url': file_url,
                'data_points': len(data),
                'plotly_json': fig.to_dict() if output_format == 'json' else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


async def create_visualization(
    chart_type: str,
    data: List[Dict[str, Any]],
    x_column: Optional[str] = None,
    y_column: Optional[str] = None,
    color_column: Optional[str] = None,
    title: str = "",
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    output_format: str = 'html',
    output_path: Optional[str] = None,
    width: int = 800,
    height: int = 600,
    theme: str = 'plotly',
    show_legend: bool = True,
    orientation: str = 'v',
    **kwargs
) -> Dict[str, Any]:
    """
    Create a Plotly visualization.
    
    This is the main entry point called by the ADK tool system.
    
    Args:
        chart_type: Type of chart to create
        data: Data to visualize (array of dictionaries)
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        color_column: Column name for color grouping
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        output_format: Output format (html, json, image)
        output_path: Path to save the visualization
        width: Chart width in pixels
        height: Chart height in pixels
        theme: Plotly theme
        show_legend: Whether to show legend
        orientation: Chart orientation (v or h)
        **kwargs: Additional arguments including tool config
        
    Returns:
        Result dictionary with visualization information
    """
    try:
        # Get tool config from kwargs
        tool_config = kwargs.get('tool_config', {})
        implementation = tool_config.get('implementation', {})
        
        # Initialize visualizer
        visualizer = PlotlyVisualizer(implementation)
        
        # Create visualization
        result = visualizer.create_visualization(
            chart_type=chart_type,
            data=data,
            x_column=x_column,
            y_column=y_column,
            color_column=color_column,
            title=title,
            x_label=x_label,
            y_label=y_label,
            output_format=output_format,
            output_path=output_path,
            width=width,
            height=height,
            theme=theme,
            show_legend=show_legend,
            orientation=orientation
        )
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
