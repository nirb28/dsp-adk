"""
Example 06: Conditional Graph with Branching

This example demonstrates conditional routing in graphs based on
classification results.

Usage:
    python run.py
"""
import asyncio
import httpx

ADK_URL = "http://localhost:8100"


async def main():
    """Run the conditional graph example."""
    print("=" * 60)
    print("Example 06: Conditional Graph with Branching")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        # 1. Show graph structure
        print("\n1. Graph Structure:")
        print("""
   ┌─────────────────────────────────────────────────────────────┐
   │              Customer Support Router Graph                  │
   │                     (Conditional)                           │
   └─────────────────────────────────────────────────────────────┘
   
                          ┌─────────┐
                          │  START  │
                          └────┬────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   classify   │
                        │              │
                        │ conversational│
                        │  -assistant   │
                        └──────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
     category ==        category ==       default
     'technical'        'research'
              │                │                │
              ▼                ▼                ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │  technical-  │  │  research-   │  │   general-   │
   │   support    │  │   support    │  │   support    │
   │              │  │              │  │              │
   │ code-        │  │ research-    │  │ conversational│
   │ assistant    │  │ agent        │  │ -assistant   │
   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                            ▼
                       ┌─────────┐
                       │   END   │
                       └─────────┘
""")
        
        # 2. Check required agents
        print("2. Required Agents:")
        agents = ['conversational-assistant', 'code-assistant', 'research-agent']
        for agent_id in agents:
            response = await client.get(f"/agents/{agent_id}")
            if response.status_code == 200:
                agent = response.json()
                print(f"   ✓ {agent['name']}")
            else:
                print(f"   ✗ {agent_id} not found")
        
        # 3. Classification logic
        print("\n3. Classification Logic:")
        print("""
   The classify node analyzes the request and outputs a category:
   
   Input: "How do I fix this Python error?"
   → Output: "technical"
   
   Input: "What are the best practices for microservices?"
   → Output: "research"
   
   Input: "What's your refund policy?"
   → Output: "general"
""")
        
        # 4. Conditional edges
        print("4. Conditional Edge Definitions:")
        print("""
   Edge 1: classify → technical-support
     condition: state.category == 'technical'
     
   Edge 2: classify → research-support
     condition: state.category == 'research'
     
   Edge 3: classify → general-support
     condition: default (fallback)
""")
        
        # 5. Example flows
        print("5. Example Execution Flows:")
        print("""
   Example A: Technical Request
   ─────────────────────────────
   User: "How do I fix this Python IndexError?"
   
   START → classify
     Category: "technical"
   classify → technical-support (condition matched)
     code-assistant handles the request
     Provides debugging help with code examples
   technical-support → END
   
   
   Example B: Research Request
   ───────────────────────────
   User: "Compare REST vs GraphQL for my use case"
   
   START → classify
     Category: "research"
   classify → research-support (condition matched)
     research-agent gathers information
     Provides comparison with sources
   research-support → END
   
   
   Example C: General Request
   ──────────────────────────
   User: "How do I reset my password?"
   
   START → classify
     Category: "general"
   classify → general-support (default)
     conversational-assistant handles inquiry
     Provides account help
   general-support → END
""")
        
        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
