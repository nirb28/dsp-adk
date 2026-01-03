"""
Test agent execution via REST API with telemetry tracking.
Run the ADK server first: python run.py
"""
import asyncio
import httpx
import sys

ADK_URL = "http://localhost:8100"


async def test_api_telemetry():
    """Test agent execution via REST API."""
    print("=" * 60)
    print("Testing Agent Execution via REST API with Telemetry")
    print("=" * 60)
    print()
    print("Make sure:")
    print("1. ADK server is running: python run.py")
    print("2. Jaeger is running: docker ps | grep jaeger")
    print("3. OTEL_ENABLED=true in your .env")
    print()
    print("-" * 60)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        # Simple query to conversational assistant
        query = "Say 'Hello from telemetry test' and nothing else."
        
        print(f"\nSending query: {query}")
        print("Agent: conversational-assistant")
        print()
        
        try:
            response = await client.post(
                "/agents/conversational-assistant/run",
                json={
                    "message": query,
                    "use_tools": False,
                    "mock_tools": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✓ Agent executed successfully")
                print(f"  Response: {result.get('response', 'N/A')}")
                print(f"  Duration: {result.get('duration_seconds', 0):.2f}s")
                print(f"  Tokens: {result.get('usage', {}).get('total_tokens', 0)}")
                print()
                
                print("=" * 60)
                print("CHECK JAEGER NOW")
                print("=" * 60)
                print("1. Open http://localhost:16686")
                print("2. Select your service from dropdown")
                print("3. Click 'Find Traces'")
                print("4. Click on the most recent trace")
                print()
                print("You should see:")
                print("  ✓ Trace: agent_execution_conversational-assistant")
                print("  ✓ Span: agent_conversational-assistant_start")
                print("  ✓ Span: llm_call_iter_1")
                print("  ✓ Events: llm_request_payload, llm_response_payload")
                print()
                print("In the span details:")
                print("  - Click on 'llm_call_iter_1' span")
                print("  - Look for 'Events' section")
                print("  - Expand 'llm_request_payload' to see request")
                print("  - Expand 'llm_response_payload' to see response")
                print()
                
            else:
                print(f"✗ Failed: {response.status_code}")
                print(f"  Error: {response.text}")
                
        except httpx.ConnectError:
            print("✗ ERROR: Cannot connect to ADK server")
            print("  Make sure the server is running: python run.py")
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_api_telemetry())
