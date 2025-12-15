"""
Example 05: Simple Sequential Graph

This example demonstrates a simple sequential graph that chains
multiple agents together.

Usage:
    python run.py
"""
import asyncio
import httpx

ADK_URL = "http://localhost:8100"


async def main():
    """Run the simple graph example."""
    print("=" * 60)
    print("Example 05: Simple Sequential Graph")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        # 1. Show graph structure
        print("\n1. Graph Structure:")
        print("""
   ┌─────────────────────────────────────────────────────────┐
   │           Research and Summarize Graph                  │
   │                  (Sequential)                           │
   └─────────────────────────────────────────────────────────┘
   
       ┌─────────┐      ┌──────────────┐      ┌───────────┐
       │  START  │ ──── │   research   │ ──── │ summarize │ ──── END
       └─────────┘      │              │      │           │
                        │ research-    │      │ convers-  │
                        │ agent        │      │ ational-  │
                        │              │      │ assistant │
                        └──────────────┘      └───────────┘
""")
        
        # 2. Check agents
        print("2. Required Agents:")
        agents = ['research-agent', 'conversational-assistant']
        for agent_id in agents:
            response = await client.get(f"/agents/{agent_id}")
            if response.status_code == 200:
                agent = response.json()
                print(f"   ✓ {agent['name']}")
            else:
                print(f"   ✗ {agent_id} not found")
        
        # 3. State flow
        print("\n3. State Flow:")
        print("""
   Initial State:
   {
     "topic": "history of the internet"
   }
   
   After research node:
   {
     "topic": "history of the internet",
     "research_results": "ARPANET was developed in 1969..."
   }
   
   After summarize node (Final):
   {
     "topic": "history of the internet",
     "research_results": "ARPANET was developed in 1969...",
     "summary": "Key points about internet history:\\n1. ..."
   }
""")
        
        # 4. Node configurations
        print("4. Node Configurations:")
        print("""
   research node:
     agent: research-agent
     config:
       research_depth: quick
       max_sources: 3
     input_mapping:
       query: "$.topic"  # Maps state.topic to agent input
     output_mapping:
       research_results: "$.response"  # Maps agent output to state
       
   summarize node:
     agent: conversational-assistant
     config:
       verbosity: concise
     input_mapping:
       prompt: "Summarize: {{ research_results }}"
     output_mapping:
       summary: "$.response"
""")
        
        # 5. Example execution
        print("5. Example Execution:")
        print("""
   Input:  "Research and summarize the history of the internet"
   
   Step 1: START → research
           Topic extracted: "history of the internet"
           
   Step 2: research node executes
           research-agent queries sources
           Finds 3 relevant articles
           Returns detailed findings
           
   Step 3: research → summarize
           State updated with research_results
           
   Step 4: summarize node executes
           conversational-assistant receives findings
           Creates concise bullet-point summary
           
   Step 5: summarize → END
           Final summary returned to user
""")
        
        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
