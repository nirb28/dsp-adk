"""
Test script for SQL Database Tool.

Tests the database tool functionality including:
- Database setup
- Schema retrieval
- Direct SQL queries
- Natural language to SQL conversion
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_database_setup():
    """Test database setup."""
    print("="*70)
    print("TEST 1: Database Setup")
    print("="*70)
    
    from scripts.setup_sample_database import create_sample_database, verify_database
    
    db_path = "./data/databases/sample.db"
    
    try:
        create_sample_database(db_path)
        verify_database(db_path)
        print("\n✓ Database setup successful")
        return True
    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        return False


async def test_tool_loading():
    """Test tool loading."""
    print("\n" + "="*70)
    print("TEST 2: Tool Loading")
    print("="*70)
    
    try:
        from app.services.tool_service import ToolService
        from app.core.config import load_config
        
        config = load_config()
        tool_service = ToolService(config)
        
        tool = await tool_service.load_tool("sql-database")
        print(f"\n✓ Tool loaded: {tool.name}")
        print(f"  Type: {tool.tool_type}")
        print(f"  Parameters: {len(tool.parameters)}")
        return True
    except Exception as e:
        print(f"\n❌ Tool loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_schema_mode():
    """Test schema retrieval."""
    print("\n" + "="*70)
    print("TEST 3: Schema Mode")
    print("="*70)
    
    try:
        from app.services.tool_service import ToolService
        from app.core.config import load_config
        
        config = load_config()
        tool_service = ToolService(config)
        
        result = await tool_service.execute_tool(
            tool_id="sql-database",
            parameters={
                "question": "show schema",
                "mode": "schema"
            }
        )
        
        if result.get('success'):
            schema = result.get('schema', {})
            print(f"\n✓ Schema retrieved")
            print(f"  Database: {schema.get('database')}")
            print(f"  Tables: {len(schema.get('tables', []))}")
            
            for table in schema.get('tables', []):
                print(f"    - {table.get('name')}: {len(table.get('columns', []))} columns")
            
            print(f"  Sample queries: {len(schema.get('sample_queries', []))}")
            return True
        else:
            print(f"\n❌ Schema retrieval failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Schema mode test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_direct_sql():
    """Test direct SQL execution."""
    print("\n" + "="*70)
    print("TEST 4: Direct SQL Mode")
    print("="*70)
    
    try:
        from app.services.tool_service import ToolService
        from app.core.config import load_config
        
        config = load_config()
        tool_service = ToolService(config)
        
        sql = "SELECT name, email, country, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5"
        print(f"\nSQL: {sql}")
        
        result = await tool_service.execute_tool(
            tool_id="sql-database",
            parameters={
                "question": sql,
                "mode": "sql",
                "limit": 5
            }
        )
        
        if result.get('success'):
            print(f"\n✓ Query executed successfully")
            print(f"  Rows returned: {result.get('row_count')}")
            print(f"  Execution time: {result.get('execution_time')}s")
            
            print("\n  Results:")
            for i, row in enumerate(result.get('results', []), 1):
                print(f"    {i}. {row.get('name')} ({row.get('country')}): ${row.get('total_spent'):.2f}")
            
            return True
        else:
            print(f"\n❌ Query failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Direct SQL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_natural_language():
    """Test natural language to SQL conversion."""
    print("\n" + "="*70)
    print("TEST 5: Natural Language Mode")
    print("="*70)
    
    # Check for API key
    api_key = os.getenv('NVAPI_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n⚠️  Skipping natural language test - no API key found")
        print("   Set NVAPI_KEY or OPENAI_API_KEY to test this feature")
        return None
    
    try:
        from app.services.tool_service import ToolService
        from app.core.config import load_config
        
        config = load_config()
        tool_service = ToolService(config)
        
        question = "What is the total revenue by product category for completed orders?"
        print(f"\nQuestion: {question}")
        
        result = await tool_service.execute_tool(
            tool_id="sql-database",
            parameters={
                "question": question,
                "mode": "natural",
                "limit": 10
            }
        )
        
        if result.get('success'):
            print(f"\n✓ Natural language query successful")
            print(f"\n  Generated SQL:")
            print(f"  {result.get('generated_sql')}")
            print(f"\n  Rows returned: {result.get('row_count')}")
            print(f"  Execution time: {result.get('execution_time')}s")
            
            print("\n  Results:")
            for row in result.get('results', []):
                print(f"    {row}")
            
            return True
        else:
            print(f"\n❌ Natural language query failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Natural language test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_loading():
    """Test agent loading."""
    print("\n" + "="*70)
    print("TEST 6: Agent Loading")
    print("="*70)
    
    try:
        from app.services.agent_executor import AgentExecutor
        from app.core.config import load_config
        
        config = load_config()
        executor = AgentExecutor(config)
        
        agent = await executor.load_agent("database-analyst")
        print(f"\n✓ Agent loaded: {agent.name}")
        print(f"  Type: {agent.agent_type}")
        print(f"  Tools: {', '.join(agent.tools)}")
        return True
    except Exception as e:
        print(f"\n❌ Agent loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("SQL DATABASE TOOL - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print()
    
    results = {}
    
    # Test 1: Database Setup
    results['database_setup'] = await test_database_setup()
    
    # Test 2: Tool Loading
    results['tool_loading'] = await test_tool_loading()
    
    # Test 3: Schema Mode
    results['schema_mode'] = await test_schema_mode()
    
    # Test 4: Direct SQL
    results['direct_sql'] = await test_direct_sql()
    
    # Test 5: Natural Language (optional)
    results['natural_language'] = await test_natural_language()
    
    # Test 6: Agent Loading
    results['agent_loading'] = await test_agent_loading()
    
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
    
    if failed == 0:
        print("\n✓ All tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")
    
    print("="*70)
    
    return failed == 0


if __name__ == '__main__':
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
