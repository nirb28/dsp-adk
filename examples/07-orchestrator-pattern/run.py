"""
Example 07: Multi-Agent Orchestration

This example demonstrates the orchestrator pattern where a central
agent coordinates multiple specialized agents for complex tasks.

Usage:
    python run.py
"""
import asyncio
import httpx

ADK_URL = "http://localhost:8100"


async def main():
    """Run the orchestrator pattern example."""
    print("=" * 60)
    print("Example 07: Multi-Agent Orchestration")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=60.0) as client:
        # 1. Show orchestrator pattern
        print("\n1. Orchestrator Pattern:")
        print("""
   ┌─────────────────────────────────────────────────────────────┐
   │                 Multi-Agent Orchestration                   │
   └─────────────────────────────────────────────────────────────┘
   
                         ┌────────────────────┐
                         │   ORCHESTRATOR     │
                         │                    │
                         │  workflow-         │
                         │  orchestrator      │
                         │                    │
                         │  Skills:           │
                         │  - task-decomp     │
                         └─────────┬──────────┘
                                   │
              ┌──────────┬─────────┼─────────┬──────────┐
              │          │         │         │          │
              ▼          ▼         ▼         ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
         │research│ │ code-  │ │ data-  │ │convers-│ │  ...   │
         │-agent  │ │assistant│ │analyst │ │ational │ │        │
         └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
         
   The orchestrator dynamically delegates to available agents
   based on the decomposed task requirements.
""")
        
        # 2. Check orchestrator
        print("2. Checking Workflow Orchestrator:")
        response = await client.get("/agents/workflow-orchestrator")
        if response.status_code == 200:
            agent = response.json()
            print(f"   ✓ {agent['name']}")
            print(f"   Capabilities: {agent.get('capabilities', [])}")
        
        # 3. Task decomposition
        print("\n3. Task Decomposition Example:")
        print("""
   Complex Task: "Research AI trends, analyze market data, 
                  and create an investment report"
   
   Orchestrator decomposes into:
   ┌──────────────────────────────────────────────────────────┐
   │ Subtask 1: Research AI Trends                           │
   │   Agent: research-agent                                  │
   │   Dependencies: none                                     │
   │   Can run: PARALLEL                                      │
   ├──────────────────────────────────────────────────────────┤
   │ Subtask 2: Gather Market Data                           │
   │   Agent: research-agent                                  │
   │   Dependencies: none                                     │
   │   Can run: PARALLEL                                      │
   ├──────────────────────────────────────────────────────────┤
   │ Subtask 3: Analyze Market Data                          │
   │   Agent: data-analyst                                    │
   │   Dependencies: [Subtask 2]                             │
   │   Can run: AFTER Subtask 2                              │
   ├──────────────────────────────────────────────────────────┤
   │ Subtask 4: Create Investment Report                     │
   │   Agent: conversational-assistant                        │
   │   Dependencies: [Subtask 1, Subtask 3]                  │
   │   Can run: AFTER Subtasks 1 and 3                       │
   └──────────────────────────────────────────────────────────┘
""")
        
        # 4. Execution timeline
        print("4. Execution Timeline:")
        print("""
   Time ────────────────────────────────────────────────────►
   
   T0   ┌─────────────────────┐  ┌─────────────────────┐
        │ Subtask 1: Research │  │ Subtask 2: Gather   │
        │ (research-agent)    │  │ (research-agent)    │
        └─────────┬───────────┘  └─────────┬───────────┘
                  │                        │
   T1             │              ┌─────────▼───────────┐
                  │              │ Subtask 3: Analyze  │
                  │              │ (data-analyst)      │
                  │              └─────────┬───────────┘
                  │                        │
   T2   ┌─────────▼────────────────────────▼───────────┐
        │        Subtask 4: Create Report              │
        │        (conversational-assistant)            │
        └──────────────────────────────────────────────┘
        
   Parallel execution of independent tasks reduces total time.
""")
        
        # 5. Error handling
        print("5. Error Handling & Retry:")
        print("""
   Configuration:
     retry_on_failure: true
     max_retries: 2
     timeout_seconds: 300
   
   If Subtask 2 fails:
   ├── Attempt 1: FAILED (API timeout)
   ├── Attempt 2: FAILED (Rate limit)
   └── Attempt 3: SUCCESS
   
   The orchestrator continues with dependent tasks after success.
   If all retries fail, the orchestrator reports the failure
   and any partial results.
""")
        
        # 6. Final aggregation
        print("6. Result Aggregation:")
        print("""
   The orchestrator combines all subtask results:
   
   Final Output:
   ┌──────────────────────────────────────────────────────────┐
   │                AI Investment Report                      │
   ├──────────────────────────────────────────────────────────┤
   │ 1. AI Trends (from Subtask 1)                           │
   │    - Generative AI growing 35% YoY                      │
   │    - Enterprise adoption accelerating                    │
   │                                                          │
   │ 2. Market Analysis (from Subtask 3)                     │
   │    - Total market: $150B by 2025                        │
   │    - Key players: OpenAI, Google, Microsoft             │
   │                                                          │
   │ 3. Investment Recommendations (from Subtask 4)          │
   │    - Consider diversified AI ETFs                       │
   │    - Monitor regulatory developments                    │
   └──────────────────────────────────────────────────────────┘
""")
        
        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
