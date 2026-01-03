"""
Example 03: Tool Execution Demo

This example demonstrates real vs mock tool execution with different tool types.

Usage:
    python run.py
"""
import asyncio
import httpx

ADK_URL = "http://localhost:8100"


async def main():
    """Run the tool execution demo."""
    print("=" * 70)
    print("Example 03: Tool Execution Demo")
    print("=" * 70)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        
        # Demo 1: Mock Tool Execution
        print("\n" + "=" * 70)
        print("DEMO 1: Mock Tool Execution (No API Keys Required)")
        print("=" * 70)
        
        print("\nRunning agent with mock_tools=True...")
        print("This uses predefined mock responses for demonstration.\n")
        
        mock_request = {
            "message": "Search for information about Python programming and summarize it",
            "use_tools": True,
            "mock_tools": True,
            "max_tool_iterations": 3
        }
        
        response = await client.post("/agents/research-agent/run", json=mock_request)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Agent Response:")
            print(f"  {result.get('response', 'No response')[:200]}...")
            print(f"\n✓ Metadata:")
            print(f"  - Tool Calls Made: {result.get('tool_calls_made', 0)}")
            print(f"  - Duration: {result.get('duration_seconds', 0):.2f}s")
            print(f"  - Tokens Used: {result.get('usage', {}).get('total_tokens', 'N/A')}")
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Error: {response.text}")
        
        # Demo 2: Real Tool Execution (if configured)
        print("\n" + "=" * 70)
        print("DEMO 2: Real Tool Execution (Requires Configuration)")
        print("=" * 70)
        
        print("\nNote: Real execution requires:")
        print("  - API endpoints configured in tool YAML files")
        print("  - Environment variables set (API keys, endpoints)")
        print("  - Network access to external APIs")
        
        print("\nAttempting real execution with mock_tools=False...")
        print("(This will use mock fallback if APIs are not configured)\n")
        
        real_request = {
            "message": "What is the weather like today?",
            "use_tools": True,
            "mock_tools": False,
            "max_tool_iterations": 2
        }
        
        response = await client.post("/agents/research-agent/run", json=real_request)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Agent Response:")
            print(f"  {result.get('response', 'No response')[:200]}...")
            print(f"\n✓ Metadata:")
            print(f"  - Tool Calls Made: {result.get('tool_calls_made', 0)}")
            print(f"  - Duration: {result.get('duration_seconds', 0):.2f}s")
        else:
            print(f"✗ Failed: {response.status_code}")
        
        # Demo 3: Python Tool Execution
        print("\n" + "=" * 70)
        print("DEMO 3: Python Tool Execution")
        print("=" * 70)
        
        print("\nChecking for Python text utilities tool...")
        
        response = await client.get("/tools/python-text-utils")
        if response.status_code == 200:
            payload = response.json()
            tool = payload.get("tool")
            if tool:
                print(f"✓ Found: {tool.get('name')}")
                print(f"  Type: {tool.get('tool_type')}")
                print(f"  Operations: summarize, count_words, extract_keywords")
                
                # Test the Python tool
                print("\nTesting Python tool with real execution...")
                
                python_request = {
                    "message": "Analyze this text: 'Python is a powerful programming language. It is widely used for web development, data science, and automation. Python has a simple syntax that makes it easy to learn.'",
                    "use_tools": True,
                    "mock_tools": False,
                    "max_tool_iterations": 2
                }
                
                # Note: This requires an agent configured to use python-text-utils
                print("  (Requires agent with python-text-utils tool)")
            else:
                print("✗ Tool not found in response")
        else:
            print(f"✗ Tool not available: {response.status_code}")
            print("  To use Python tools:")
            print("  1. Create Python functions in tools/ directory")
            print("  2. Configure tool YAML with module and function")
            print("  3. Add tool to agent's tools list")
        
        # Demo 4: Disabled Tools
        print("\n" + "=" * 70)
        print("DEMO 4: Disabled Tools")
        print("=" * 70)
        
        print("\nRunning agent with use_tools=False...")
        print("Agent will respond without calling any tools.\n")
        
        no_tools_request = {
            "message": "What is Python?",
            "use_tools": False
        }
        
        response = await client.post("/agents/research-agent/run", json=no_tools_request)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Agent Response:")
            print(f"  {result.get('response', 'No response')[:200]}...")
            print(f"\n✓ Metadata:")
            print(f"  - Tool Calls Made: {result.get('tool_calls_made', 0)}")
            print(f"  - Duration: {result.get('duration_seconds', 0):.2f}s")
        else:
            print(f"✗ Failed: {response.status_code}")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        print("\nTool Execution Modes:")
        print("  1. Mock Mode (mock_tools=true)")
        print("     - No external dependencies")
        print("     - Predefined responses")
        print("     - Perfect for testing and demos")
        
        print("\n  2. Real Mode (mock_tools=false)")
        print("     - Calls actual APIs/functions")
        print("     - Requires configuration")
        print("     - Production-ready execution")
        
        print("\n  3. Disabled (use_tools=false)")
        print("     - No tool calls")
        print("     - Direct LLM response only")
        print("     - Fastest execution")
        
        print("\nSupported Tool Types:")
        print("  ✓ API Tools - HTTP requests to external APIs")
        print("  ✓ Python Tools - Direct Python function calls")
        print("  ✓ Shell Tools - Execute shell commands")
        print("  ⏳ MCP Tools - Model Context Protocol (coming soon)")
        
        print("\nNext Steps:")
        print("  1. Configure API endpoints in tool YAML files")
        print("  2. Set environment variables for API keys")
        print("  3. Create custom Python tools in tools/ directory")
        print("  4. Test with mock_tools=true first")
        print("  5. Enable real execution with mock_tools=false")
        
        print("\n" + "=" * 70)
        print("Example complete!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
