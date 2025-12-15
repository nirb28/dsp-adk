"""
Example 02: Research Agent with Tools

This example demonstrates how to use a research agent with multiple tools
to gather and synthesize information.

Usage:
    python run.py
"""
import asyncio
import httpx

ADK_URL = "http://localhost:8100"


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
            agent = response.json()
            print(f"   Found: {agent['name']}")
        else:
            print("   Agent not found. Please ensure generic agents are loaded.")
            return
        
        # 2. Check for required tools
        print("\n2. Checking required tools...")
        tools_needed = ['web-search', 'text-processor']
        tools_available = []
        
        for tool_id in tools_needed:
            response = await client.get(f"/tools/{tool_id}")
            if response.status_code == 200:
                tool = response.json()
                tools_available.append(tool_id)
                print(f"   ✓ {tool['name']}: {tool['description'][:50]}...")
            else:
                print(f"   ✗ {tool_id}: Not found")
        
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
        
        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
