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
            payload = response.json()
            # API returns an AgentResponse wrapper: {success, message, agent}
            agent = payload.get("agent") if isinstance(payload, dict) else None
            if not agent:
                print("   Unexpected response shape from ADK API")
                print(f"   Response JSON: {payload}")
                return
            print(f"   Found agent: {agent.get('name', 'N/A')}")
            print(f"   Description: {agent.get('description', 'N/A')}")
        else:
            print(f"   Request failed: {response.status_code}")
            try:
                print(f"   Response JSON: {response.json()}")
            except Exception:
                print(f"   Response text: {response.text}")
            print("   Agent not found (or not accessible). Please ensure generic agents are loaded.")
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
        
        # 4. Run the agent with a sample question
        print("\n4. Running the Agent:")
        sample_question = "What is the capital of France?"
        print(f"   Question: {sample_question}")
        
        run_request = {
            "message": sample_question
        }
        
        response = await client.post(
            f"/agents/conversational-assistant/run",
            json=run_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n   Agent Response:")
            print(f"   {result.get('response', 'No response')}")
            print(f"\n   Metadata:")
            print(f"   - Model: {result.get('model', 'N/A')}")
            print(f"   - Provider: {result.get('provider', 'N/A')}")
            print(f"   - Duration: {result.get('duration_seconds', 0):.2f}s")
            if 'usage' in result:
                usage = result['usage']
                print(f"   - Tokens: {usage.get('total_tokens', 'N/A')}")
        else:
            print(f"   Failed to run agent: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', response.text)}")
            except:
                print(f"   Error: {response.text}")
        
        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
