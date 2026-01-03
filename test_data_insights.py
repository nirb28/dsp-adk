"""
Test script for Data Insights functionality (Database + Visualization).

Tests both tools separately and together.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_plotly_tool_loading():
    """Test Plotly visualizer tool loading."""
    print("="*70)
    print("TEST 1: Plotly Visualizer Tool Loading")
    print("="*70)
    
    try:
        from app.services.tool_service import ToolService
        from app.core.config import load_config
        
        config = load_config()
        tool_service = ToolService(config)
        
        tool = await tool_service.load_tool("plotly-visualizer")
        print(f"\n✓ Tool loaded: {tool.name}")
        print(f"  Type: {tool.tool_type}")
        print(f"  Parameters: {len(tool.parameters)}")
        print(f"  Chart types: bar, line, scatter, pie, histogram, box, heatmap, table")
        return True
    except Exception as e:
        print(f"\n❌ Tool loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bar_chart():
    """Test creating a bar chart."""
    print("\n" + "="*70)
    print("TEST 2: Create Bar Chart")
    print("="*70)
    
    try:
        from app.services.tool_service import ToolService
        from app.core.config import load_config
        
        config = load_config()
        tool_service = ToolService(config)
        
        # Sample data
        data = [
            {"category": "Electronics", "revenue": 8450.50},
            {"category": "Clothing", "revenue": 5640.25},
            {"category": "Books", "revenue": 3020.75},
            {"category": "Home", "revenue": 2015.00},
            {"category": "Sports", "revenue": 1008.50}
        ]
        
        result = await tool_service.execute_tool(
            tool_id="plotly-visualizer",
            parameters={
                "chart_type": "bar",
                "data": data,
                "x_column": "category",
                "y_column": "revenue",
                "title": "Revenue by Category",
                "x_label": "Product Category",
                "y_label": "Revenue ($)",
                "output_format": "html",
                "theme": "plotly_white"
            }
        )
        
        if result.get('success'):
            print(f"\n✓ Bar chart created successfully")
            print(f"  Output: {result.get('output_path')}")
            print(f"  Data points: {result.get('data_points')}")
            print(f"  Format: {result.get('output_format')}")
            return True
        else:
            print(f"\n❌ Bar chart creation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Bar chart test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pie_chart():
    """Test creating a pie chart."""
    print("\n" + "="*70)
    print("TEST 3: Create Pie Chart")
    print("="*70)
    
    try:
        from app.services.tool_service import ToolService
        from app.core.config import load_config
        
        config = load_config()
        tool_service = ToolService(config)
        
        # Sample data
        data = [
            {"status": "Completed", "count": 85},
            {"status": "Pending", "count": 12},
            {"status": "Cancelled", "count": 8}
        ]
        
        result = await tool_service.execute_tool(
            tool_id="plotly-visualizer",
            parameters={
                "chart_type": "pie",
                "data": data,
                "x_column": "status",
                "y_column": "count",
                "title": "Order Status Distribution",
                "output_format": "html",
                "theme": "plotly"
            }
        )
        
        if result.get('success'):
            print(f"\n✓ Pie chart created successfully")
            print(f"  Output: {result.get('output_path')}")
            print(f"  Data points: {result.get('data_points')}")
            return True
        else:
            print(f"\n❌ Pie chart creation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Pie chart test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_line_chart():
    """Test creating a line chart."""
    print("\n" + "="*70)
    print("TEST 4: Create Line Chart")
    print("="*70)
    
    try:
        from app.services.tool_service import ToolService
        from app.core.config import load_config
        
        config = load_config()
        tool_service = ToolService(config)
        
        # Sample data
        data = [
            {"month": "2024-01", "revenue": 12500},
            {"month": "2024-02", "revenue": 15200},
            {"month": "2024-03", "revenue": 14800},
            {"month": "2024-04", "revenue": 18900},
            {"month": "2024-05", "revenue": 21300},
            {"month": "2024-06", "revenue": 19800}
        ]
        
        result = await tool_service.execute_tool(
            tool_id="plotly-visualizer",
            parameters={
                "chart_type": "line",
                "data": data,
                "x_column": "month",
                "y_column": "revenue",
                "title": "Monthly Revenue Trend",
                "x_label": "Month",
                "y_label": "Revenue ($)",
                "output_format": "html",
                "theme": "seaborn"
            }
        )
        
        if result.get('success'):
            print(f"\n✓ Line chart created successfully")
            print(f"  Output: {result.get('output_path')}")
            print(f"  Data points: {result.get('data_points')}")
            return True
        else:
            print(f"\n❌ Line chart creation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Line chart test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_db_plus_visualization():
    """Test database query + visualization together."""
    print("\n" + "="*70)
    print("TEST 5: Database Query + Visualization Integration")
    print("="*70)
    
    # Check database exists
    db_path = Path(__file__).parent / "data" / "databases" / "sample.db"
    if not db_path.exists():
        print("\n⚠️  Skipping - sample database not found")
        print("   Run: python scripts/setup_sample_database.py")
        return None
    
    try:
        from app.services.tool_service import ToolService
        from app.core.config import load_config
        
        config = load_config()
        tool_service = ToolService(config)
        
        # Step 1: Query database
        print("\nStep 1: Query database for revenue by category")
        sql_result = await tool_service.execute_tool(
            tool_id="sql-database",
            parameters={
                "question": "SELECT product_category, SUM(amount) as total_revenue FROM orders WHERE status='completed' GROUP BY product_category ORDER BY total_revenue DESC",
                "mode": "sql"
            }
        )
        
        if not sql_result.get('success'):
            print(f"❌ Database query failed: {sql_result.get('error')}")
            return False
        
        print(f"✓ Query successful - {sql_result.get('row_count')} rows")
        
        # Step 2: Create visualization from query results
        print("\nStep 2: Create bar chart from query results")
        viz_result = await tool_service.execute_tool(
            tool_id="plotly-visualizer",
            parameters={
                "chart_type": "bar",
                "data": sql_result.get('results', []),
                "x_column": "product_category",
                "y_column": "total_revenue",
                "title": "Revenue by Product Category (from Database)",
                "x_label": "Category",
                "y_label": "Total Revenue ($)",
                "output_format": "html",
                "theme": "plotly_white",
                "height": 500
            }
        )
        
        if viz_result.get('success'):
            print(f"✓ Visualization created successfully")
            print(f"  Chart: {viz_result.get('output_path')}")
            print(f"\n✓ Integration test passed!")
            print(f"  Database → {sql_result.get('row_count')} rows")
            print(f"  Visualization → {viz_result.get('data_points')} data points")
            return True
        else:
            print(f"❌ Visualization failed: {viz_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_loading():
    """Test data insights agent loading."""
    print("\n" + "="*70)
    print("TEST 6: Data Insights Agent Loading")
    print("="*70)
    
    try:
        from app.services.agent_executor import AgentExecutor
        from app.core.config import load_config
        
        config = load_config()
        executor = AgentExecutor(config)
        
        agent = await executor.load_agent("data-insights")
        print(f"\n✓ Agent loaded: {agent.name}")
        print(f"  Type: {agent.agent_type}")
        print(f"  Tools: {', '.join(agent.tools)}")
        print(f"  Expected tools: sql-database, plotly-visualizer")
        
        if 'sql-database' in agent.tools and 'plotly-visualizer' in agent.tools:
            print(f"  ✓ Both tools configured correctly")
            return True
        else:
            print(f"  ❌ Missing required tools")
            return False
            
    except Exception as e:
        print(f"\n❌ Agent loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_table_visualization():
    """Test creating an interactive table."""
    print("\n" + "="*70)
    print("TEST 7: Create Interactive Table")
    print("="*70)
    
    try:
        from app.services.tool_service import ToolService
        from app.core.config import load_config
        
        config = load_config()
        tool_service = ToolService(config)
        
        # Sample data
        data = [
            {"name": "John Smith", "country": "USA", "total_spent": 1250.50},
            {"name": "Emma Johnson", "country": "UK", "total_spent": 980.25},
            {"name": "Michael Brown", "country": "Canada", "total_spent": 875.00}
        ]
        
        result = await tool_service.execute_tool(
            tool_id="plotly-visualizer",
            parameters={
                "chart_type": "table",
                "data": data,
                "title": "Top Customers",
                "output_format": "html"
            }
        )
        
        if result.get('success'):
            print(f"\n✓ Table created successfully")
            print(f"  Output: {result.get('output_path')}")
            return True
        else:
            print(f"\n❌ Table creation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Table test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("DATA INSIGHTS - COMPREHENSIVE TEST SUITE")
    print("Database + Visualization Integration")
    print("="*70)
    print()
    
    results = {}
    
    # Test 1: Plotly tool loading
    results['plotly_loading'] = await test_plotly_tool_loading()
    
    # Test 2: Bar chart
    results['bar_chart'] = await test_bar_chart()
    
    # Test 3: Pie chart
    results['pie_chart'] = await test_pie_chart()
    
    # Test 4: Line chart
    results['line_chart'] = await test_line_chart()
    
    # Test 5: Database + Visualization integration
    results['db_viz_integration'] = await test_db_plus_visualization()
    
    # Test 6: Agent loading
    results['agent_loading'] = await test_agent_loading()
    
    # Test 7: Table visualization
    results['table_viz'] = await test_table_visualization()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result is True else "⚠️  SKIP" if result is None else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print()
    print(f"Total: {total} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    
    # Show visualizations directory
    viz_dir = Path(__file__).parent / "data" / "visualizations"
    if viz_dir.exists():
        viz_files = list(viz_dir.glob("*.html"))
        print(f"\nVisualizations created: {len(viz_files)}")
        print(f"Location: {viz_dir}")
    
    if failed == 0:
        print("\n✓ All tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")
    
    print("="*70)
    
    return failed == 0


if __name__ == '__main__':
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
