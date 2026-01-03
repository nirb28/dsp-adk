"""
Test agent execution with full telemetry tracking.
"""
import asyncio
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, str(Path(__file__).parent))

from app.services.agent_executor import get_agent_executor
from app.core.base import get_registry


async def test_agent_with_telemetry():
    """Test full agent execution with telemetry."""
    print("=" * 60)
    print("Testing Agent Execution with Telemetry")
    print("=" * 60)
    
    # Load registry
    registry = get_registry()
    
    # Get a simple agent (conversational-assistant has no tools/skills)
    agent = registry.get("conversational-assistant")
    if not agent:
        print("❌ ERROR: conversational-assistant not found")
        print("Available agents:", list(registry._components.keys()))
        return
    
    print(f"✓ Loaded agent: {agent.name}")
    print(f"  Provider: {agent.llm.provider}")
    print(f"  Model: {agent.llm.model}")
    print()
    
    # Get executor
    executor = get_agent_executor()
    
    # Simple test query
    test_message = "Say 'Hello from ADK telemetry test' and nothing else."
    print(f"Query: {test_message}")
    print()
    
    try:
        print("Executing agent (watch for [TELEMETRY] logs)...")
        print("-" * 60)
        
        result = await executor.run(
            agent=agent,
            message=test_message,
            use_tools=False,
            mock_tools=False
        )
        
        print("-" * 60)
        print()
        print("=" * 60)
        print("RESULT")
        print("=" * 60)
        print(f"Response: {result['response']}")
        print(f"Duration: {result['duration_seconds']:.2f}s")
        print(f"Tokens: {result['usage'].get('total_tokens', 0)}")
        print()
        
        print("=" * 60)
        print("CHECK JAEGER NOW")
        print("=" * 60)
        print("1. Open http://localhost:16686")
        print("2. Select service from dropdown (check your OTEL_SERVICE_NAME)")
        print("3. Click 'Find Traces'")
        print("4. Click on the most recent trace")
        print()
        print("You should see:")
        print("  - agent_conversational-assistant_start (main span)")
        print("  - llm_call_iter_1 (LLM request)")
        print("  - Events with request/response payloads")
        print()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_agent_with_telemetry())
