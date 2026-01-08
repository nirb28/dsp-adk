"""
RAG Knowledge Retrieval Example

Demonstrates an AI agent that retrieves information from knowledge bases
using the RAG retrieval tool connected to dsp-rag service.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

import httpx


async def run_interactive_demo():
    """Run interactive knowledge assistant demo."""
    
    print("="*70)
    print("KNOWLEDGE ASSISTANT AGENT - Interactive Demo")
    print("="*70)
    print("\nThis agent retrieves information from knowledge bases using RAG!")
    print("It connects to dsp-rag service to search document collections.\n")
    
    # Check environment variables
    rag_endpoint = os.getenv('RAG_ENDPOINT', 'http://localhost:9000')
    print(f"RAG Endpoint: {rag_endpoint}")
    
    api_key = os.getenv('LLM_API_KEY')
    if not api_key:
        print("⚠️  No API key found!")
        print("Please set LLM_API_KEY environment variable")
        return
    
    print("✓ API key configured\n")
    
    # ADK API endpoint
    adk_endpoint = os.getenv('ADK_ENDPOINT', 'http://localhost:8100')
    agent_id = "knowledge-assistant-agent"
    
    # Verify agent exists
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{adk_endpoint}/agents/{agent_id}")
            if response.status_code == 404:
                print(f"❌ Agent '{agent_id}' not found")
                # List available agents
                list_response = await client.get(f"{adk_endpoint}/agents")
                if list_response.status_code == 200:
                    agents_data = list_response.json()
                    print("\nAvailable agents:")
                    for agent in agents_data.get('agents', []):
                        print(f"  - {agent['id']}: {agent['name']}")
                return
            response.raise_for_status()
            agent_data = response.json()
            print(f"✓ Agent loaded: {agent_data['agent']['name']}\n")
        except httpx.HTTPError as e:
            print(f"❌ Error connecting to ADK API: {e}")
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
            
            try:
                # Call ADK agent execution API
                async with httpx.AsyncClient(timeout=60.0) as client:
                    payload = {
                        "message": user_input,
                        "stream": False,
                        "use_tools": True
                    }
                    
                    response = await client.post(
                        f"{adk_endpoint}/agents/{agent_id}/run",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(result.get('response', '[No response]'), flush=True)
                    else:
                        print(f"❌ API Error {response.status_code}: {response.text}")
                    
            except httpx.TimeoutException:
                print("\n❌ Request timed out. The LLM is taking too long to respond.")
            except Exception as e:
                print(f"\n❌ Error during execution: {e}")
            
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
    rag_endpoint = os.getenv('RAG_ENDPOINT', 'http://localhost:9000')
    print(f"RAG Endpoint: {rag_endpoint}\n")
    
    # ADK API endpoint
    adk_endpoint = os.getenv('ADK_ENDPOINT', 'http://localhost:8100')
    agent_id = "knowledge-assistant-agent"
    
    # Verify agent exists
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{adk_endpoint}/agents/{agent_id}")
            response.raise_for_status()
            agent_data = response.json()
            print(f"✓ Agent loaded: {agent_data['agent']['name']}\n")
        except httpx.HTTPError as e:
            print(f"❌ Error: {e}")
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
            # Call ADK agent execution API
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "message": question,
                    "stream": False,
                    "use_tools": True
                }
                
                response = await client.post(
                    f"{adk_endpoint}/agents/{agent_id}/run",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(result.get('response', '[No response]'), flush=True)
                else:
                    print(f"❌ API Error {response.status_code}: {response.text}")
            
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
    
    # ADK API endpoint
    adk_endpoint = os.getenv('ADK_ENDPOINT', 'http://localhost:8100')
    tool_id = "rag-retrieval"
    
    # Verify tool exists
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{adk_endpoint}/tools/{tool_id}")
            response.raise_for_status()
            tool_data = response.json()
            print(f"✓ Tool loaded: {tool_data['tool']['name']}\n")
        except httpx.HTTPError as e:
            print(f"❌ Error: {e}")
            return
    
    # Test 1: Basic retrieval
    print("Test 1: Basic Document Retrieval")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{adk_endpoint}/tools/{tool_id}/execute",
            json={
                "arguments": {
                    "query": "What is machine learning?",
                    "configuration_name": "batch_ml_ai_basics_test",
                    "k": 5,
                    "use_reranking": True
                }
            }
        )
        response.raise_for_status()
        result = json.loads(response.text)
    
    if 'error' in result:
        print(f"Error: {result.get('error')}")
    elif 'documents' in result:
        print(f"Query: {result.get('query')}")
        print(f"Configuration: {result.get('configuration_name')}")
        print(f"Documents found: {result.get('total_found', len(result['documents']))}")
        
        print("\nRetrieved documents:")
        for i, doc in enumerate(result.get('documents', [])[:3], 1):
            print(f"\n  Document {i}:")
            content = doc.get('page_content', doc.get('content', ''))
            print(f"    Content: {content[:200]}...")
            if doc.get('metadata'):
                print(f"    Metadata: {doc.get('metadata')}")
    else:
        print(f"Unexpected result format: {result}")
    
    print()
    
    # Test 2: With metadata filter
    print("Test 2: Retrieval with Metadata Filter")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{adk_endpoint}/tools/{tool_id}/execute",
            json={
                "arguments": {
                    "query": "API configuration",
                    "configuration_name": "batch_ml_ai_basics_test",
                    "k": 3,
                    "use_reranking": True,
                    "filter": {"category": "api"}
                }
            }
        )
        response.raise_for_status()
        result = json.loads(response.text)
    
    if 'error' in result:
        print(f"Error: {result.get('error')}")
    elif 'documents' in result:
        print(f"Documents found: {result.get('total_found', len(result['documents']))}")
        print(f"Filter applied: category=api")
    else:
        print(f"Unexpected result: {result}")
    
    print()
    
    # Test 3: Different configuration
    print("Test 3: Different Knowledge Base Configuration")
    print("-" * 70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{adk_endpoint}/tools/{tool_id}/execute",
            json={
                "arguments": {
                    "query": "How to reset password?",
                    "configuration_name": "batch_ml_ai_basics_test",
                    "k": 5
                }
            }
        )
        response.raise_for_status()
        result = json.loads(response.text)
    
    if 'error' in result:
        print(f"Error: {result.get('error')}")
    elif 'documents' in result:
        print(f"Configuration: {result.get('configuration_name')}")
        print(f"Documents found: {result.get('total_found', len(result['documents']))}")
    else:
        print(f"Unexpected result: {result}")
    
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
        default='http://localhost:9000',
        help='RAG service endpoint (default: http://localhost:9000)'
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
