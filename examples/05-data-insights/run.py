"""
Data Insights Agent Example

Demonstrates an AI agent that combines database querying and visualization
to provide comprehensive data insights.
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


async def run_interactive_demo():
    """Run interactive data insights demo."""
    
    print("="*70)
    print("DATA INSIGHTS AGENT - Interactive Demo")
    print("="*70)
    print("\nThis agent combines database querying and visualization!")
    print("Ask questions and get both data AND charts.\n")
    
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
    
    # Check visualization directory
    viz_dir = project_root / "data" / "visualizations"
    viz_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Visualizations will be saved to: {viz_dir}\n")
    
    print("Note: This example requires the ADK server to be running.")
    print("Please start the server with: python run.py\n")
    
    # Initialize HTTP client
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=120.0) as client:
        # Load agent
        agent_id = "data-insights"
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
            print(f"❌ Failed to connect to ADK server: {e}")
            print("Make sure the server is running on http://localhost:8100")
            return
        
        print("="*70)
        print("EXAMPLE QUESTIONS:")
        print("="*70)
        print("""
1. Data + Visualization Requests:
   - Show me the top 5 customers by spending with a bar chart
   - Create a pie chart of revenue by product category
   - Visualize the monthly revenue trend as a line chart
   - Show customer distribution by country with a bar chart

2. Complex Analysis:
   - Compare revenue across product categories and visualize it
   - Show me the relationship between order count and revenue
   - Analyze customer spending patterns with visualizations
   - Create a chart showing order status distribution

3. Multi-step Analysis:
   - What are the top selling categories? Show me a chart.
   - Which countries have the most customers? Visualize this.
   - How has revenue changed over time? Create a trend chart.

Type 'quit' or 'exit' to end the conversation.
Type 'viz' to open the visualizations folder.
""")
        
        print("="*70)
        print()
        
        # Interactive loop
        conversation_id = "insights-demo-session"
        
        await interactive_loop(client, agent_id, conversation_id, viz_dir)


async def interactive_loop(client: httpx.AsyncClient, agent_id: str, conversation_id: str, viz_dir: Path):
    """Run the interactive query loop."""
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye! Check the visualizations folder for your charts.")
                print(f"Location: {viz_dir}")
                break
            
            # Handle special commands
            if user_input.lower() == 'viz':
                import subprocess
                if sys.platform == 'win32':
                    subprocess.run(['explorer', str(viz_dir)])
                elif sys.platform == 'darwin':
                    subprocess.run(['open', str(viz_dir)])
                else:
                    subprocess.run(['xdg-open', str(viz_dir)])
                print(f"Opened: {viz_dir}\n")
                continue
            
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
    print("DATA INSIGHTS AGENT - Automated Demo")
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
        agent_id = "data-insights"
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
        
        # Predefined questions that combine querying and visualization
        questions = [
            "Show me the top 5 customers by spending and create a bar chart",
            "What is the revenue by product category? Create a pie chart to visualize it.",
            "Visualize the monthly revenue trend with a line chart",
            "Show me the distribution of order statuses with a bar chart",
        ]
        
        conversation_id = "insights-auto-demo"
        
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
    
    # Show visualizations directory
    viz_dir = Path(__file__).parent.parent.parent / "data" / "visualizations"
    print(f"\nVisualizations saved to: {viz_dir}")
    print("Open this folder to view the charts.")


async def test_tools_separately():
    """Test database and visualization tools separately."""
    
    print("="*70)
    print("TOOL TESTING - Database + Visualization")
    print("="*70)
    print()
    
    print("Note: Direct tool testing requires the ADK server to be running.")
    print("This example uses the REST API to test tools.\n")
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=120.0) as client:
        # Test 1: Query database via REST API
        print("Test 1: Query Database")
        print("-" * 70)
        
        try:
            response = await client.post(
                "/tools/sql-database/execute",
                json={
                    "question": "SELECT product_category, SUM(amount) as total_revenue FROM orders WHERE status='completed' GROUP BY product_category ORDER BY total_revenue DESC",
                    "mode": "sql",
                    "limit": 10
                }
            )
            
            if response.status_code == 200:
                sql_result = response.json()
                if sql_result.get('success'):
                    print(f"✓ Query successful")
                    print(f"  Rows: {sql_result.get('row_count')}")
                    print(f"  Data:")
                    for row in sql_result.get('results', [])[:5]:
                        print(f"    {row}")
                else:
                    print(f"❌ Query failed: {sql_result.get('error')}")
            else:
                print(f"❌ API Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*70)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Data Insights Agent Demo')
    parser.add_argument(
        '--mode',
        choices=['interactive', 'auto', 'test'],
        default='interactive',
        help='Demo mode: interactive (default), auto, or test'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'interactive':
        asyncio.run(run_interactive_demo())
    elif args.mode == 'auto':
        asyncio.run(run_automated_demo())
    elif args.mode == 'test':
        asyncio.run(test_tools_separately())


if __name__ == '__main__':
    main()
