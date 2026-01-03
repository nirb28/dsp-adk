"""
Test script to verify tool call telemetry is working.
This uses the text-processor tool which should be called by the LLM.
"""
import asyncio
import sys
from app.services.agent_service import AgentService
from app.services.agent_executor import get_agent_executor

async def test_tool_telemetry():
    """Test that tool calls are properly captured in telemetry."""
    
    print("=" * 80)
    print("Testing Tool Call Telemetry")
    print("=" * 80)
    
    # Get services
    agent_service = AgentService()
    executor = get_agent_executor()
    
    # Load the research agent
    agent = agent_service.get_agent("research-agent")
    if not agent:
        print("ERROR: Could not load research-agent")
        return
    
    print(f"\n✓ Loaded agent: {agent.name}")
    print(f"  Tools: {agent.tools}")
    print(f"  LLM: {agent.llm.provider}/{agent.llm.model}")
    
    # Create a query that WILL use the text-processor tool
    message = """
    Please process the following text and summarize it in 3 bullet points:
    
    "Quantum computing represents a paradigm shift in computational capabilities. 
    Unlike classical computers that use bits (0 or 1), quantum computers use qubits 
    that can exist in superposition states. This allows them to solve certain problems 
    exponentially faster than classical computers. Recent developments include 
    error correction breakthroughs, increased qubit counts, and commercial applications 
    in cryptography, drug discovery, and optimization problems."
    
    Use the text-processor tool with operation="summarize" to process this text.
    """
    
    print(f"\n📝 Query: {message[:100]}...")
    print(f"\n🔧 Expected: LLM should call text-processor tool")
    print(f"⏳ Executing agent...\n")
    
    try:
        # Execute with tools enabled
        result = await executor.run(
            agent=agent,
            message=message,
            use_tools=True,
            max_tool_iterations=3,
            mock_tools=True  # Use mock responses for testing
        )
        
        print("=" * 80)
        print("EXECUTION RESULT")
        print("=" * 80)
        print(f"✓ Success: {result['success']}")
        print(f"✓ Tool calls made: {result.get('tool_calls_made', 0)}")
        print(f"✓ Total tokens: {result['usage'].get('total_tokens', 0)}")
        print(f"✓ Duration: {result['duration_seconds']:.2f}s")
        print(f"\n📄 Response preview:")
        print(result['response'][:500])
        print("...")
        
        if result.get('tool_calls_made', 0) > 0:
            print("\n" + "=" * 80)
            print("✅ SUCCESS: Tool calls were made!")
            print("=" * 80)
            print("\nNow check Jaeger UI at http://localhost:16686")
            print("You should see:")
            print("  1. agent_research-agent_start span with adk.input_data")
            print("  2. llm_call_iter_1 span with:")
            print("     - Event: llm_request_payload (tools_available)")
            print("     - Event: llm_response_payload (tool_calls_summary)")
            print("     - Event: tool_calls_detected")
            print("  3. tool_text-processor span with:")
            print("     - adk.input_data (full arguments)")
            print("     - Event: tool_result_payload")
            print("     - adk.output_data (result metadata)")
            print("  4. llm_call_iter_2 span (final response)")
        else:
            print("\n" + "=" * 80)
            print("⚠️  WARNING: No tool calls were made")
            print("=" * 80)
            print("\nThe LLM chose not to use tools. This can happen if:")
            print("  1. The LLM thinks it can answer without tools")
            print("  2. The system prompt doesn't encourage tool use")
            print("  3. The query isn't explicit enough about using tools")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_tool_telemetry())
