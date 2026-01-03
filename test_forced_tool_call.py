"""
Force a tool call to verify telemetry captures it properly.
Uses a very explicit instruction to ensure the LLM calls the tool.
"""
import asyncio
import json
from app.services.agent_service import AgentService
from app.services.agent_executor import get_agent_executor

async def main():
    print("\n" + "="*80)
    print("FORCED TOOL CALL TEST - Verifying Telemetry")
    print("="*80)
    
    agent_service = AgentService()
    executor = get_agent_executor()
    
    agent = agent_service.get_agent("research-agent")
    if not agent:
        print("❌ Could not load research-agent")
        return
    
    print(f"\n✓ Agent: {agent.name}")
    print(f"✓ Tools available: {agent.tools}")
    
    # Very explicit instruction to use the tool
    message = """
    IMPORTANT: You MUST use the text-processor tool to complete this task.
    
    Call the text-processor tool with these exact parameters:
    - text: "Quantum computing is revolutionizing technology"
    - operation: "summarize"
    
    Do not answer without calling the tool first.
    """
    
    print(f"\n📝 Message: Explicit instruction to call text-processor")
    print(f"🔧 Mock tools: ENABLED (for testing)")
    print(f"⏳ Executing...\n")
    
    try:
        result = await executor.run(
            agent=agent,
            message=message,
            use_tools=True,
            max_tool_iterations=5,
            mock_tools=True
        )
        
        print("="*80)
        print("RESULT")
        print("="*80)
        print(f"Success: {result['success']}")
        print(f"Tool calls: {result.get('tool_calls_made', 0)}")
        print(f"Tokens: {result['usage'].get('total_tokens', 0)}")
        print(f"Duration: {result['duration_seconds']:.2f}s")
        
        if result.get('tool_calls_made', 0) > 0:
            print("\n✅ TOOL CALL SUCCESSFUL!")
            print("\n📊 Check Jaeger UI: http://localhost:16686")
            print("\nLook for trace with these spans:")
            print("  1. agent_research-agent_start")
            print("     └─ adk.input_data: Full request")
            print("     └─ adk.output_data: Response metadata")
            print("\n  2. llm_call_iter_1")
            print("     └─ Event: llm_request_payload")
            print("        └─ tools_available: [\"httpbin-test\", \"text-processor\"]")
            print("     └─ Event: llm_response_payload")
            print("        └─ has_tool_calls: true")
            print("        └─ tool_calls_count: 1")
            print("        └─ tool_calls_summary: [{\"id\":\"...\",\"function\":\"text-processor\",\"args_preview\":\"...\"}]")
            print("     └─ Event: tool_calls_detected")
            print("        └─ tool_names: [\"text-processor\"]")
            print("\n  3. tool_text-processor")
            print("     └─ adk.input_data: {\"text\":\"...\",\"operation\":\"summarize\"}")
            print("     └─ Event: tool_result_payload")
            print("        └─ result_preview: {\"result\":\"...\"}")
            print("     └─ adk.output_data: {\"result_length\":123}")
            print("\n  4. llm_call_iter_2")
            print("     └─ Final response without tool calls")
            
            print("\n" + "="*80)
            print("Response preview:")
            print("="*80)
            print(result['response'][:800])
            if len(result['response']) > 800:
                print("...")
        else:
            print("\n⚠️  No tool calls made - LLM ignored instruction")
            print("\nThis might happen if:")
            print("  - LLM doesn't support tool calling well")
            print("  - System prompt conflicts with instruction")
            print("  - Model is too small/weak for tool use")
            print("\nResponse:")
            print(result['response'][:500])
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
