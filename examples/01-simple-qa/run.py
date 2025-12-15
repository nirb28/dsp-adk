"""
Example 01: Simple Q&A Agent

This example demonstrates the simplest use case - a basic conversational
agent that answers questions using only its built-in knowledge.

Usage:
    python run.py
"""
import asyncio
import httpx

ADK_URL = "http://localhost:8100"


async def main():
    """Run the simple Q&A example."""
    print("=" * 60)
    print("Example 01: Simple Q&A Agent")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        # 1. Check if the conversational-assistant agent exists
        print("\n1. Checking for conversational-assistant agent...")
        response = await client.get("/agents/conversational-assistant")
        if response.status_code == 200:
            agent = response.json()
            print(f"   Found agent: {agent['name']}")
            print(f"   Description: {agent['description']}")
        else:
            print("   Agent not found. Please ensure generic agents are loaded.")
            return
        
        # 2. Get agent configuration
        print("\n2. Agent Configuration:")
        if 'llm' in agent:
            print(f"   Provider: {agent['llm'].get('provider', 'N/A')}")
            print(f"   Model: {agent['llm'].get('model', 'N/A')}")
            print(f"   Temperature: {agent['llm'].get('temperature', 'N/A')}")
        
        # 3. Show configurable parameters
        print("\n3. Configurable Parameters:")
        if 'config_schema' in agent and agent['config_schema']:
            for param, details in agent['config_schema'].get('properties', {}).items():
                print(f"   - {param}: {details.get('description', 'No description')}")
                if 'default' in details:
                    print(f"     Default: {details['default']}")
        
        # 4. Example usage
        print("\n4. Example Usage:")
        print("   In a real application, you would:")
        print("   - Initialize the agent with your LLM configuration")
        print("   - Send user messages to the agent")
        print("   - Receive responses from the agent")
        
        example_prompts = [
            "What is the capital of France?",
            "Explain quantum computing in simple terms",
            "What are the benefits of exercise?"
        ]
        
        print("\n   Example prompts you could send:")
        for i, prompt in enumerate(example_prompts, 1):
            print(f"   {i}. \"{prompt}\"")
        
        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
