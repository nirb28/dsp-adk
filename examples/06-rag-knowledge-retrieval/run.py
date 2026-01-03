"""
RAG Knowledge Retrieval Example

Demonstrates an AI agent that retrieves information from knowledge bases
using the RAG retrieval tool connected to dsp-rag service.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.agent_executor import AgentExecutor
from app.core.config import load_config


async def run_interactive_demo():
    """Run interactive knowledge assistant demo."""
    
    print("="*70)
    print("KNOWLEDGE ASSISTANT AGENT - Interactive Demo")
    print("="*70)
    print("\nThis agent retrieves information from knowledge bases using RAG!")
    print("It connects to dsp-rag service to search document collections.\n")
    
    # Check environment variables
    rag_endpoint = os.getenv('RAG_ENDPOINT', 'http://localhost:8000')
    print(f"RAG Endpoint: {rag_endpoint}")
    
    api_key = os.getenv('NVAPI_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  No API key found!")
        print("Please set NVAPI_KEY or OPENAI_API_KEY environment variable")
        return
    
    print("✓ API key configured\n")
    
    # Load configuration
    config = load_config()
    
    # Initialize agent executor
    executor = AgentExecutor(config)
    
    # Load agent
    agent_id = "knowledge-assistant"
    try:
        agent = await executor.load_agent(agent_id)
        print(f"✓ Agent loaded: {agent.name}\n")
    except Exception as e:
        print(f"❌ Failed to load agent: {e}")
        return
    
    print("="*70)
    print("EXAMPLE QUESTIONS:")
    print("="*70)
    print("""
1. Simple Queries:
   - What is machine learning?
   - How does authentication work?
   - Explain the deployment process

2. Specific Searches:
   - Find information about API endpoints
   - Search for configuration examples
   - Look up troubleshooting steps

3. Filtered Searches:
   - Find technical documentation about databases
   - Search customer support articles about billing
   - Get product specifications for laptops

4. Configuration-Specific:
   - Search in technical_docs: How to configure the system?
   - Search in customer_support: How do I reset my password?
   - Search in product_info: What are the laptop specifications?

Type 'quit' or 'exit' to end the conversation.
Type 'configs' to see available knowledge base configurations.
""")
    
    print("="*70)
    print()
    
    # Interactive loop
    conversation_id = "knowledge-demo-session"
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye! Thanks for using the Knowledge Assistant.")
                break
            
            # Handle special commands
            if user_input.lower() == 'configs':
                print("\nAvailable Knowledge Base Configurations:")
                print("  - default: Default knowledge base")
                print("  - technical_docs: Technical documentation")
                print("  - customer_support: Customer support articles")
                print("  - product_info: Product information and specs")
                print("\nTo use a specific config, mention it in your question:")
                print("  'Search in technical_docs: your question'\n")
                continue
            
            # Execute agent
            print("\nAgent: ", end="", flush=True)
            
            response = await executor.execute_agent(
                agent_id=agent_id,
                user_message=user_input,
                conversation_id=conversation_id,
                stream=True
            )
            
            # Handle streaming response
            full_response = ""
            tool_calls = []
            
            async for chunk in response:
                if chunk.get('type') == 'content':
                    content = chunk.get('content', '')
                    print(content, end="", flush=True)
                    full_response += content
                elif chunk.get('type') == 'tool_call':
                    tool_name = chunk.get('tool_name', 'unknown')
                    tool_calls.append(tool_name)
                    print(f"\n[Searching knowledge base...]", flush=True)
                elif chunk.get('type') == 'tool_result':
                    result = chunk.get('result', {})
                    if result.get('success'):
                        chunks_found = result.get('total_chunks', 0)
                        config_used = result.get('configuration_name', 'unknown')
                        print(f"[Found {chunks_found} relevant chunks in '{config_used}']", flush=True)
                elif chunk.get('type') == 'error':
                    print(f"\n❌ Error: {chunk.get('error', 'Unknown error')}")
            
            print("\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


async def run_automated_demo():
    """Run automated demo with predefined questions."""
    
    print("="*70)
    print("KNOWLEDGE ASSISTANT AGENT - Automated Demo")
    print("="*70)
    print()
    
    # Check RAG endpoint
    rag_endpoint = os.getenv('RAG_ENDPOINT', 'http://localhost:8000')
    print(f"RAG Endpoint: {rag_endpoint}\n")
    
    # Load configuration
    config = load_config()
    executor = AgentExecutor(config)
    
    # Load agent
    agent_id = "knowledge-assistant"
    try:
        agent = await executor.load_agent(agent_id)
        print(f"✓ Agent loaded: {agent.name}\n")
    except Exception as e:
        print(f"❌ Failed to load agent: {e}")
        return
    
    # Predefined questions
    questions = [
        "What is machine learning?",
        "How does authentication work in the system?",
        "Search for information about API configuration",
        "Find troubleshooting steps for deployment issues",
    ]
    
    conversation_id = "knowledge-auto-demo"
    
    for i, question in enumerate(questions, 1):
        print("="*70)
        print(f"QUESTION {i}/{len(questions)}")
        print("="*70)
        print(f"You: {question}\n")
        print("Agent: ", end="", flush=True)
        
        try:
            response = await executor.execute_agent(
                agent_id=agent_id,
                user_message=question,
                conversation_id=conversation_id,
                stream=True
            )
            
            # Collect response
            full_response = ""
            chunks_found = 0
            
            async for chunk in response:
                if chunk.get('type') == 'content':
                    content = chunk.get('content', '')
                    print(content, end="", flush=True)
                    full_response += content
                elif chunk.get('type') == 'tool_call':
                    print(f"\n[Searching knowledge base...]", flush=True)
                elif chunk.get('type') == 'tool_result':
                    result = chunk.get('result', {})
                    if result.get('success'):
                        chunks_found = result.get('total_chunks', 0)
                        print(f"[Found {chunks_found} relevant chunks]", flush=True)
            
            print("\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
        
        # Pause between questions
        if i < len(questions):
            await asyncio.sleep(1)
    
    print("="*70)
    print("Demo completed!")
    print("="*70)


async def test_rag_tool_directly():
    """Test RAG retrieval tool directly."""
    
    print("="*70)
    print("DIRECT RAG TOOL TEST")
    print("="*70)
    print()
    
    from app.services.tool_service import ToolService
    from app.core.config import load_config
    
    config = load_config()
    tool_service = ToolService(config)
    
    # Load tool
    tool_id = "rag-retrieval"
    try:
        tool = await tool_service.load_tool(tool_id)
        print(f"✓ Tool loaded: {tool.name}\n")
    except Exception as e:
        print(f"❌ Failed to load tool: {e}")
        return
    
    # Test 1: Basic retrieval
    print("Test 1: Basic Document Retrieval")
    print("-" * 70)
    
    result = await tool_service.execute_tool(
        tool_id=tool_id,
        parameters={
            "query": "What is machine learning?",
            "configuration_name": "default",
            "top_k": 5,
            "use_reranking": True
        }
    )
    
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Query: {result.get('query')}")
        print(f"Configuration: {result.get('configuration_name')}")
        print(f"Chunks found: {result.get('total_chunks')}")
        
        print("\nRetrieved chunks:")
        for i, chunk in enumerate(result.get('chunks', [])[:3], 1):
            print(f"\n  Chunk {i}:")
            print(f"    Score: {chunk.get('score', 0):.4f}")
            print(f"    Content: {chunk.get('content', '')[:200]}...")
            if chunk.get('metadata'):
                print(f"    Metadata: {chunk.get('metadata')}")
    else:
        print(f"Error: {result.get('error')}")
    
    print()
    
    # Test 2: With metadata filter
    print("Test 2: Retrieval with Metadata Filter")
    print("-" * 70)
    
    result = await tool_service.execute_tool(
        tool_id=tool_id,
        parameters={
            "query": "API configuration",
            "configuration_name": "technical_docs",
            "top_k": 3,
            "use_reranking": True,
            "metadata_filter": {"category": "api"}
        }
    )
    
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Chunks found: {result.get('total_chunks')}")
        print(f"Filter applied: category=api")
    else:
        print(f"Error: {result.get('error')}")
    
    print()
    
    # Test 3: Different configuration
    print("Test 3: Different Knowledge Base Configuration")
    print("-" * 70)
    
    result = await tool_service.execute_tool(
        tool_id=tool_id,
        parameters={
            "query": "How to reset password?",
            "configuration_name": "customer_support",
            "top_k": 5
        }
    )
    
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Configuration: {result.get('configuration_name')}")
        print(f"Chunks found: {result.get('total_chunks')}")
    else:
        print(f"Error: {result.get('error')}")
    
    print("\n" + "="*70)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG Knowledge Retrieval Demo')
    parser.add_argument(
        '--mode',
        choices=['interactive', 'auto', 'test'],
        default='interactive',
        help='Demo mode: interactive (default), auto, or test'
    )
    parser.add_argument(
        '--rag-endpoint',
        default='http://localhost:8000',
        help='RAG service endpoint (default: http://localhost:8000)'
    )
    
    args = parser.parse_args()
    
    # Set RAG endpoint environment variable
    os.environ['RAG_ENDPOINT'] = args.rag_endpoint
    
    if args.mode == 'interactive':
        asyncio.run(run_interactive_demo())
    elif args.mode == 'auto':
        asyncio.run(run_automated_demo())
    elif args.mode == 'test':
        asyncio.run(test_rag_tool_directly())


if __name__ == '__main__':
    main()
