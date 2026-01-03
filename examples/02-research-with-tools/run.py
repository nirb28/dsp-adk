"""
Example 02: Research Agent with Tools

This example demonstrates how to use a research agent with multiple tools
to gather and synthesize information.

Usage:
    python run.py
"""
import asyncio
import httpx
import logging
import sys
ADK_URL = "http://localhost:8100"

# Configure logging to show debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# You can also configure specific loggers
logger = logging.getLogger(__name__)

def _extract_wrapped(payload: dict, key: str):
    """Extract wrapped payload like {"agent": {...}} / {"tool": {...}}."""
    if not isinstance(payload, dict):
        return None
    if key in payload and payload.get(key) is not None:
        return payload.get(key)
    return None


def _error_detail(response: httpx.Response) -> str:
    try:
        data = response.json()
        if isinstance(data, dict):
            return data.get("detail") or data.get("message") or response.text
    except Exception:
        pass
    return response.text


async def main():
    """Run the research with tools example."""
    print("=" * 60)
    print("Example 02: Research Agent with Tools")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        # 1. Check for research agent
        print("\n1. Loading research-agent...")
        response = await client.get("/agents/research-agent")
        if response.status_code == 200:
            payload = response.json()
            agent = _extract_wrapped(payload, "agent")
            if not agent:
                print("   Unexpected response shape from /agents/{id}")
                print(f"   Raw: {payload}")
                return
            print(f"   Found: {agent.get('name', 'N/A')}")
        else:
            print(f"   Failed to load agent: {response.status_code}")
            print(f"   Error: {_error_detail(response)}")
            return
        
        # 2. Check for required tools
        print("\n2. Checking required tools...")
        tools_needed = ['web-search', 'text-processor']
        tools_available = []
        
        for tool_id in tools_needed:
            response = await client.get(f"/tools/{tool_id}")
            if response.status_code == 200:
                payload = response.json()
                tool = _extract_wrapped(payload, "tool")
                if not tool:
                    print(f"   ✗ {tool_id}: Unexpected response shape")
                    continue
                tools_available.append(tool_id)
                description = tool.get('description') or ''
                print(f"   ✓ {tool.get('name', tool_id)}: {description[:50]}...")
            else:
                print(f"   ✗ {tool_id}: {response.status_code} - {_error_detail(response)}")
        
        # 3. Show tool configuration
        print("\n3. Tool Configurations:")
        
        # Web search config
        print("\n   web-search configuration:")
        print("   - num_results: 5 (number of search results)")
        print("   - Used for: Finding relevant web pages")
        
        # Text processor config  
        print("\n   text-processor configuration:")
        print("   - operation: summarize (default)")
        print("   - max_output_length: 500")
        print("   - Used for: Summarizing found information")
        
        # 4. Research agent configuration
        print("\n4. Research Agent Configuration:")
        print("   - research_depth: standard")
        print("   - source_types: [web]")
        print("   - output_format: summary")
        print("   - include_citations: true")
        print("   - max_sources: 5")
        
        # 5. Example workflow
        print("\n5. Example Workflow:")
        print("   User Query: 'What are the latest developments in quantum computing?'")
        print("")
        print("   Step 1: Agent receives query")
        print("   Step 2: Agent calls web-search tool")
        print("          → Returns 5 relevant articles")
        print("   Step 3: Agent calls text-processor on each result")
        print("          → Summarizes key points")
        print("   Step 4: Agent synthesizes information")
        print("          → Combines summaries with citations")
        print("   Step 5: Agent returns final response")
        print("          → Formatted summary with source links")
        
        # 6. Example prompts
        print("\n6. Example Research Questions:")
        questions = [
            "What are the latest developments in quantum computing?",
            "Compare renewable energy sources",
            "What is the current state of AI regulation?"
        ]
        for i, q in enumerate(questions, 1):
            print(f"   {i}. \"{q}\"")

        # 7. Run the agent
        print("\n7. Running the Agent:")
        query = "What are the latest developments in quantum computing? Provide sources."
        print(f"   Query: {query}")

        # Set mock_tools=True for demo (no real API keys needed)
        # Set mock_tools=False to use real tool execution (requires API configuration)
        run_request = {
            "message": query,
            # "context": {
            #     "research_depth": "standard",
            #     "source_types": ["web"],
            #     "include_citations": True,
            #     "max_sources": 2,
            # },
            "use_tools": True,
            "max_tool_iterations": 5,
            "mock_tools": False  # Change to False for real tool execution
        }

        response = await client.post(
            "/agents/research-agent/run",
            json=run_request
        )

        if response.status_code == 200:
            result = response.json()
            print("\n   Agent Response:")
            print(result.get("response", "No response"))
            print("\n   Metadata:")
            print(f"   - Model: {result.get('model', 'N/A')}")
            print(f"   - Provider: {result.get('provider', 'N/A')}")
            print(f"   - Duration: {result.get('duration_seconds', 0):.2f}s")
            print(f"   - Tool Calls: {result.get('tool_calls_made', 0)}")
            usage = result.get("usage") or {}
            if usage:
                print(f"   - Tokens: {usage.get('total_tokens', 'N/A')}")
        else:
            print(f"   Failed to run agent: {response.status_code}")
            print(f"   Error: {_error_detail(response)}")
         
        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
