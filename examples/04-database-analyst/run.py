"""
Database Analyst Agent Example

Demonstrates an AI agent that can query databases using natural language,
following the vanna.ai model for AI-powered database interactions.
"""
import asyncio
import httpx
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(project_root / ".env")

ADK_URL = "http://localhost:8100"


async def run_database_analyst_demo():
    """Run interactive database analyst demo."""
    
    print("="*70)
    print("DATABASE ANALYST AGENT - Interactive Demo")
    print("="*70)
    print("\nThis agent can query databases using natural language!")
    print("It uses AI to convert your questions into SQL queries.\n")
    
    # Check if database exists
    db_path = project_root / "data" / "databases" / "sample.db"
    if not db_path.exists():
        print("⚠️  Sample database not found!")
        print(f"Expected location: {db_path}")
        print("\nPlease run: python scripts/setup_sample_database.py")
        return
    
    print(f"✓ Database found: {db_path}\n")
    
    # Check environment variables
    api_key = os.getenv('NVIDIA_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  No API key found!")
        print("Please set NVIDIA_API_KEY or OPENAI_API_KEY environment variable")
        return
    
    print("✓ API key configured\n")
    
    print("Note: This example requires the ADK server to be running.")
    print("Please start the server with: python run.py\n")
    
    # Initialize HTTP client
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=120.0) as client:
        # Load agent
        agent_id = "database-analyst"
        try:
            response = await client.get(f"/agents/{agent_id}")
            if response.status_code == 200:
                agent_data = response.json()
                agent = agent_data.get('agent', agent_data)
                print(f"✓ Agent loaded: {agent.get('name', agent_id)}\n")
            else:
                print(f"❌ Failed to load agent: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Failed to load agent: {e}")
            return
        
        print("="*70)
        print("EXAMPLE QUESTIONS YOU CAN ASK:")
        print("="*70)
        print("""
1. Simple Queries:
   - Who are the top 5 customers by spending?
   - Show me recent orders from the last 30 days
   - Which products are low on stock?

2. Analytical Queries:
   - What is the total revenue by product category?
   - Show me the monthly revenue trend
   - Which customers have never placed an order?

3. Complex Queries:
   - What's the average order value by country?
   - Show customer lifetime value distribution
   - Compare revenue across different product categories

4. Schema Exploration:
   - What tables are available?
   - Show me the database schema
   - What data do you have about customers?

Type 'quit' or 'exit' to end the conversation.
Type 'schema' to see the database schema.
Type 'examples' to see sample queries.
""")
        
        print("="*70)
        print()
        
        # Interactive loop
        conversation_id = "db-demo-session"
        
        await interactive_loop(client, agent_id, conversation_id)


async def interactive_loop(client: httpx.AsyncClient, agent_id: str, conversation_id: str):
    """Run the interactive query loop."""
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye! Thanks for using the Database Analyst Agent.")
                break
            
            # Handle special commands
            if user_input.lower() == 'schema':
                user_input = "Show me the complete database schema with all tables and columns"
            elif user_input.lower() == 'examples':
                user_input = "What are some example queries I can run on this database?"
            
            # Execute agent via REST API
            print("\nAgent: ", end="", flush=True)
            
            try:
                response = await client.post(
                    f"/agents/{agent_id}/run",
                    json={
                        "message": user_input,
                        "conversation_id": conversation_id,
                        "use_tools": True,
                        "max_tool_iterations": 5,
                        "mock_tools": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(result.get("response", "No response"))
                    
                    # Show tool usage if any
                    tool_calls = result.get("tool_calls_made", 0)
                    if tool_calls > 0:
                        print(f"\n[Used {tool_calls} tool call(s)]")
                else:
                    print(f"\n❌ Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"\n❌ Error: {e}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


async def run_automated_demo():
    """Run automated demo with predefined questions."""
    
    print("="*70)
    print("DATABASE ANALYST AGENT - Automated Demo")
    print("="*70)
    print()
    
    # Check database
    db_path = Path(__file__).parent.parent.parent / "data" / "databases" / "sample.db"
    if not db_path.exists():
        print("⚠️  Sample database not found!")
        print("Please run: python scripts/setup_sample_database.py")
        return
    
    print("Note: This example requires the ADK server to be running.")
    print("Please start the server with: python run.py\n")
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=120.0) as client:
        # Load agent
        agent_id = "database-analyst"
        try:
            response = await client.get(f"/agents/{agent_id}")
            if response.status_code != 200:
                print(f"❌ Failed to load agent: {response.status_code}")
                return
            agent_data = response.json()
            agent = agent_data.get('agent', agent_data)
            print(f"✓ Agent loaded: {agent.get('name', agent_id)}\n")
        except Exception as e:
            print(f"❌ Failed to load agent: {e}")
            return
        
        # Predefined questions
        questions = [
            "Show me the database schema",
            "Who are the top 5 customers by total spending?",
            "What is the total revenue by product category for completed orders?",
            "Which customers have never placed an order?",
            "Show me the monthly revenue trend for the last 6 months",
        ]
        
        conversation_id = "db-auto-demo"
        
        await run_questions(client, agent_id, conversation_id, questions)


async def run_questions(client: httpx.AsyncClient, agent_id: str, conversation_id: str, questions: list):
    """Run a list of questions through the agent."""
    for i, question in enumerate(questions, 1):
        print("="*70)
        print(f"QUESTION {i}/{len(questions)}")
        print("="*70)
        print(f"You: {question}\n")
        print("Agent: ", end="", flush=True)
        
        try:
            response = await client.post(
                f"/agents/{agent_id}/run",
                json={
                    "message": question,
                    "conversation_id": conversation_id,
                    "use_tools": True,
                    "max_tool_iterations": 5,
                    "mock_tools": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(result.get("response", "No response"))
                tool_calls = result.get("tool_calls_made", 0)
                if tool_calls > 0:
                    print(f"\n[Used {tool_calls} tool call(s)]")
            else:
                print(f"\n❌ Error: {response.status_code}")
            
            print()
            
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
        
        # Pause between questions
        if i < len(questions):
            await asyncio.sleep(1)
    
    print("="*70)
    print("Demo completed!")
    print("="*70)


async def test_direct_tool():
    """Test the SQL database tool directly."""
    
    print("="*70)
    print("DIRECT TOOL TEST")
    print("="*70)
    print()
    
    print("Note: Direct tool testing requires the ADK server to be running.")
    print("This example should use the REST API instead.\n")
    return
    
    # Load tool
    tool_id = "sql-database"
    try:
        tool = await tool_service.load_tool(tool_id)
        print(f"✓ Tool loaded: {tool.name}\n")
    except Exception as e:
        print(f"❌ Failed to load tool: {e}")
        return
    
    # Test 1: Get schema
    print("Test 1: Get Database Schema")
    print("-" * 70)
    result = await tool_service.execute_tool(
        tool_id=tool_id,
        parameters={
            "question": "show schema",
            "mode": "schema"
        }
    )
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        schema = result.get('schema', {})
        print(f"Database: {schema.get('database')}")
        print(f"Tables: {len(schema.get('tables', []))}")
        for table in schema.get('tables', [])[:2]:
            print(f"  - {table.get('name')}: {table.get('description')}")
    print()
    
    # Test 2: Direct SQL query
    print("Test 2: Direct SQL Query")
    print("-" * 70)
    result = await tool_service.execute_tool(
        tool_id=tool_id,
        parameters={
            "question": "SELECT name, email, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5",
            "mode": "sql",
            "limit": 5
        }
    )
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"SQL: {result.get('generated_sql')}")
        print(f"Rows: {result.get('row_count')}")
        print(f"Execution time: {result.get('execution_time')}s")
        print("\nResults:")
        for row in result.get('results', [])[:3]:
            print(f"  {row}")
    else:
        print(f"Error: {result.get('error')}")
    print()
    
    # Test 3: Natural language query
    print("Test 3: Natural Language Query")
    print("-" * 70)
    print("Question: What is the total revenue by product category?")
    result = await tool_service.execute_tool(
        tool_id=tool_id,
        parameters={
            "question": "What is the total revenue by product category?",
            "mode": "natural",
            "limit": 10
        }
    )
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Generated SQL: {result.get('generated_sql')}")
        print(f"Rows: {result.get('row_count')}")
        print(f"Execution time: {result.get('execution_time')}s")
        print("\nResults:")
        for row in result.get('results', []):
            print(f"  {row}")
    else:
        print(f"Error: {result.get('error')}")
    print()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Analyst Agent Demo')
    parser.add_argument(
        '--mode',
        choices=['interactive', 'auto', 'test'],
        default='interactive',
        help='Demo mode: interactive (default), auto, or test'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'interactive':
        asyncio.run(run_database_analyst_demo())
    elif args.mode == 'auto':
        asyncio.run(run_automated_demo())
    elif args.mode == 'test':
        asyncio.run(test_direct_tool())


if __name__ == '__main__':
    main()
