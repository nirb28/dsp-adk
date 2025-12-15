"""
Example 03: Code Review Pipeline

This example demonstrates how to use the code assistant with file operations
to build a code review pipeline.

Usage:
    python run.py
"""
import asyncio
import httpx

ADK_URL = "http://localhost:8100"


async def main():
    """Run the code review pipeline example."""
    print("=" * 60)
    print("Example 03: Code Review Pipeline")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        # 1. Load code-assistant agent
        print("\n1. Loading code-assistant agent...")
        response = await client.get("/agents/code-assistant")
        if response.status_code == 200:
            agent = response.json()
            print(f"   Found: {agent['name']}")
            print(f"   Capabilities: {agent.get('capabilities', [])}")
        else:
            print("   Agent not found.")
            return
        
        # 2. Load required tools
        print("\n2. Loading tools...")
        
        # File operations tool
        response = await client.get("/tools/file-operations")
        if response.status_code == 200:
            tool = response.json()
            print(f"   ✓ {tool['name']}")
            print(f"     Operations: read, write, list, exists, info")
        
        # Text processor tool
        response = await client.get("/tools/text-processor")
        if response.status_code == 200:
            tool = response.json()
            print(f"   ✓ {tool['name']}")
            print(f"     Can extract entities, keywords from code")
        
        # 3. Show code review workflow
        print("\n3. Code Review Workflow:")
        print("""
   ┌─────────────────────────────────────────────────┐
   │              Code Review Pipeline               │
   └─────────────────────────────────────────────────┘
   
   Step 1: Input
   ├── File path: "src/main.py"
   │   OR
   └── Code snippet directly
   
   Step 2: Read Code (file-operations tool)
   ├── Read file content
   ├── Check file size/encoding
   └── Return code as string
   
   Step 3: Analysis (code-assistant agent)
   ├── Syntax check
   ├── Style guide compliance (PEP8)
   ├── Security vulnerabilities
   ├── Performance issues
   └── Best practices
   
   Step 4: Generate Review
   ├── List of issues found
   ├── Severity levels
   ├── Suggested fixes with code
   └── Optional: Generate tests
""")
        
        # 4. Example review output
        print("4. Example Review Output:")
        print("""
   ┌─────────────────────────────────────────────────┐
   │ Code Review for: src/main.py                   │
   ├─────────────────────────────────────────────────┤
   │ Overall Score: 7/10                            │
   ├─────────────────────────────────────────────────┤
   │ Issues Found:                                   │
   │                                                 │
   │ [HIGH] Line 23: SQL Injection vulnerability    │
   │   → Use parameterized queries                  │
   │                                                 │
   │ [MEDIUM] Line 45: Missing error handling       │
   │   → Add try/except for file operations         │
   │                                                 │
   │ [LOW] Line 12: Variable naming (PEP8)          │
   │   → Use snake_case: myVar → my_var             │
   ├─────────────────────────────────────────────────┤
   │ Suggested Tests:                               │
   │   • test_database_query_injection              │
   │   • test_file_read_error_handling              │
   └─────────────────────────────────────────────────┘
""")
        
        # 5. Configuration options
        print("5. Configuration Options:")
        print("   code-assistant config:")
        print("     - languages: [python, javascript, typescript]")
        print("     - style_guide: PEP8")
        print("     - security_check: true")
        print("     - include_tests: true")
        print("")
        print("   file-operations config:")
        print("     - base_path: ./src")
        print("     - allowed_extensions: [.py, .js, .ts]")
        print("     - max_file_size: 1MB")
        
        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
