"""
Example: Running ADK with Debug Logging Enabled

This example demonstrates how to enable debug logging to see detailed
execution flow for agents, tools, and skills.

Usage:
    # Run with debug logging
    python debug-mode-example.py
    
    # Or set environment variable
    export LOG_LEVEL=DEBUG
    python debug-mode-example.py
"""
import asyncio
import logging
import sys
import httpx

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

ADK_URL = "http://localhost:8100"


def _extract_wrapped(payload: dict, key: str):
    """Extract wrapped payload like {"agent": {...}} / {"tool": {...}}."""
    if not isinstance(payload, dict):
        return None
    if key in payload and payload.get(key) is not None:
        return payload.get(key)
    return None


async def main():
    """Run agent with debug logging enabled."""
    print("=" * 80)
    print("Debug Mode Example: Detailed Execution Flow Logging")
    print("=" * 80)
    print("\nDebug logging is enabled. You will see detailed execution flow with markers:")
    print("  [AGENT_EXEC]  - Agent execution flow")
    print("  [TOOL_EXEC]   - Tool execution flow")
    print("  [TOOL_LOAD]   - Tool loading operations")
    print("  [AGENT_LOAD]  - Agent loading operations")
    print("  [SKILL_LOAD]  - Skill loading operations")
    print("  [REPO_LOAD]   - Repository asset loading")
    print("=" * 80)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        # 1. Load agent (you'll see [AGENT_LOAD] logs)
        print("\n1. Loading research-agent...")
        response = await client.get("/agents/research-agent")
        
        if response.status_code == 200:
            payload = response.json()
            agent = _extract_wrapped(payload, "agent")
            if agent:
                print(f"   ✓ Loaded: {agent.get('name', 'N/A')}")
            else:
                print("   ✗ Failed to load agent")
                return
        else:
            print(f"   ✗ Agent not found: {response.status_code}")
            return
        
        # 2. Run agent with tools (you'll see detailed execution logs)
        print("\n2. Running agent with tools...")
        print("   Watch for execution flow markers in the logs above:")
        print("   - Agent initialization")
        print("   - Tool loading")
        print("   - LLM calls")
        print("   - Tool execution")
        print("   - Response generation")
        
        run_request = {
            "message": "What are the latest developments in quantum computing?",
            "context": {
                "research_depth": "standard",
                "max_sources": 3
            },
            "use_tools": True,
            "max_tool_iterations": 3,
            "mock_tools": True  # Use mock for demo
        }
        
        response = await client.post(
            "/agents/research-agent/run",
            json=run_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n   ✓ Agent execution completed")
            print(f"   - Duration: {result.get('duration_seconds', 0):.2f}s")
            print(f"   - Tool calls: {result.get('tool_calls_made', 0)}")
            print(f"   - Tokens: {result.get('usage', {}).get('total_tokens', 'N/A')}")
            print(f"\n   Response preview: {result.get('response', '')[:200]}...")
        else:
            print(f"   ✗ Agent execution failed: {response.status_code}")
            print(f"   Error: {response.text}")
        
        print("\n" + "=" * 80)
        print("Debug Mode Example Complete!")
        print("=" * 80)
        print("\nReview the logs above to see the detailed execution flow.")
        print("Look for markers like [AGENT_EXEC], [TOOL_EXEC], etc.")


if __name__ == "__main__":
    asyncio.run(main())
