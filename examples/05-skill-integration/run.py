"""
Example: Skill Integration

Demonstrates how to use skills with agents in different application modes:
- System prompt extension
- Few-shot examples
- Orchestration steps
- Context injection
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.models.agents import AgentConfig, LLMConfig
from app.models.skills import SkillInstance, SkillApplicationMode
from app.services.agent_executor import get_agent_executor


async def example_1_simple_skill_assignment():
    """Example 1: Simple skill assignment using skill IDs."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple Skill Assignment")
    print("="*80)
    
    agent = AgentConfig(
        id="simple-coding-agent",
        name="Simple Coding Agent",
        description="Agent with simple skill assignment",
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "groq"),
            model=os.getenv("LLM_MODEL", "llama3-8b-8192"),
            endpoint=os.getenv("LLM_ENDPOINT"),
            api_key_env=os.getenv("LLM_API_KEY_ENV", "GROQ_API_KEY"),
            temperature=0.7,
            max_tokens=1024,
            system_prompt="You are a helpful coding assistant."
        ),
        skills=["code-generation"]  # Simple skill ID
    )
    
    print(f"Agent: {agent.name}")
    print(f"Skills: {agent.skills}")
    print(f"\nSending message: 'Write a Python function to calculate factorial'")
    
    executor = get_agent_executor()
    result = await executor.run(
        agent=agent,
        message="Write a Python function to calculate factorial",
        use_tools=False
    )
    
    print(f"\n✓ Response received ({len(result['response'])} chars)")
    print(f"Duration: {result['duration_seconds']:.2f}s")
    print(f"\nResponse:\n{'-'*80}\n{result['response']}\n{'-'*80}")


async def example_2_system_prompt_extension():
    """Example 2: Using skills as system prompt extensions."""
    print("\n" + "="*80)
    print("EXAMPLE 2: System Prompt Extension")
    print("="*80)
    
    agent = AgentConfig(
        id="research-agent-prompt",
        name="Research Agent (Prompt Extension)",
        description="Agent using research methodology as prompt extension",
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "groq"),
            model=os.getenv("LLM_MODEL", "llama3-8b-8192"),
            endpoint=os.getenv("LLM_ENDPOINT"),
            api_key_env=os.getenv("LLM_API_KEY_ENV", "GROQ_API_KEY"),
            temperature=0.3,
            max_tokens=2048,
            system_prompt="You are a research assistant."
        ),
        skills=[
            SkillInstance(
                skill_id="research-methodology",
                application_modes=[SkillApplicationMode.SYSTEM_PROMPT_EXTENSION],
                parameters={
                    "research_depth": "standard",
                    "source_types": "academic, news",
                    "require_citations": True
                },
                enabled=True
            )
        ]
    )
    
    print(f"Agent: {agent.name}")
    print(f"Skill: research-methodology (system_prompt_extension)")
    print(f"\nSending message: 'What are the latest developments in quantum computing?'")
    
    executor = get_agent_executor()
    result = await executor.run(
        agent=agent,
        message="What are the latest developments in quantum computing?",
        use_tools=False
    )
    
    print(f"\n✓ Response received ({len(result['response'])} chars)")
    print(f"Duration: {result['duration_seconds']:.2f}s")
    print(f"\nResponse:\n{'-'*80}\n{result['response'][:500]}...\n{'-'*80}")


async def example_3_few_shot_examples():
    """Example 3: Using skills with few-shot examples."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Few-Shot Examples")
    print("="*80)
    
    agent = AgentConfig(
        id="coding-agent-examples",
        name="Coding Agent (Few-Shot)",
        description="Agent using code generation with few-shot examples",
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "groq"),
            model=os.getenv("LLM_MODEL", "llama3-8b-8192"),
            endpoint=os.getenv("LLM_ENDPOINT"),
            api_key_env=os.getenv("LLM_API_KEY_ENV", "GROQ_API_KEY"),
            temperature=0.7,
            max_tokens=1024,
            system_prompt="You are a Python coding expert."
        ),
        skills=[
            SkillInstance(
                skill_id="code-generation",
                application_modes=[
                    SkillApplicationMode.SYSTEM_PROMPT_EXTENSION,
                    SkillApplicationMode.FEW_SHOT_EXAMPLES
                ],
                parameters={"language": "python"},
                enabled=True
            )
        ]
    )
    
    print(f"Agent: {agent.name}")
    print(f"Skill: code-generation (system_prompt + few_shot_examples)")
    print(f"\nSending message: 'Create a function to check if a number is prime'")
    
    executor = get_agent_executor()
    result = await executor.run(
        agent=agent,
        message="Create a function to check if a number is prime",
        use_tools=False
    )
    
    print(f"\n✓ Response received ({len(result['response'])} chars)")
    print(f"Duration: {result['duration_seconds']:.2f}s")
    print(f"\nResponse:\n{'-'*80}\n{result['response']}\n{'-'*80}")


async def example_4_orchestration_steps():
    """Example 4: Using skills with orchestration steps."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Orchestration Steps")
    print("="*80)
    
    agent = AgentConfig(
        id="planning-agent",
        name="Planning Agent (Orchestration)",
        description="Agent using task decomposition with orchestration",
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "groq"),
            model=os.getenv("LLM_MODEL", "llama3-70b-8192"),
            endpoint=os.getenv("LLM_ENDPOINT"),
            api_key_env=os.getenv("LLM_API_KEY_ENV", "GROQ_API_KEY"),
            temperature=0.5,
            max_tokens=2048,
            system_prompt="You are a project planning expert."
        ),
        skills=[
            SkillInstance(
                skill_id="task-decomposition",
                application_modes=[SkillApplicationMode.ORCHESTRATION_STEP],
                parameters={
                    "max_depth": 3,
                    "output_format": "tree",
                    "include_estimates": True
                },
                enabled=True
            )
        ]
    )
    
    print(f"Agent: {agent.name}")
    print(f"Skill: task-decomposition (orchestration_step)")
    print(f"\nSending message: 'Plan a mobile app development project'")
    
    executor = get_agent_executor()
    result = await executor.run(
        agent=agent,
        message="Plan a mobile app development project for a food delivery service",
        use_tools=False
    )
    
    print(f"\n✓ Response received ({len(result['response'])} chars)")
    print(f"Duration: {result['duration_seconds']:.2f}s")
    print(f"\nResponse:\n{'-'*80}\n{result['response'][:800]}...\n{'-'*80}")


async def example_5_multiple_skills():
    """Example 5: Using multiple skills with different priorities."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Multiple Skills with Priorities")
    print("="*80)
    
    agent = AgentConfig(
        id="advanced-research-agent",
        name="Advanced Research Agent",
        description="Agent with multiple skills applied in priority order",
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "groq"),
            model=os.getenv("LLM_MODEL", "llama3-70b-8192"),
            endpoint=os.getenv("LLM_ENDPOINT"),
            api_key_env=os.getenv("LLM_API_KEY_ENV", "GROQ_API_KEY"),
            temperature=0.3,
            max_tokens=3072,
            system_prompt="You are an expert research analyst."
        ),
        skills=[
            SkillInstance(
                skill_id="research-methodology",
                application_modes=[
                    SkillApplicationMode.CONTEXT_INJECTION,
                    SkillApplicationMode.SYSTEM_PROMPT_EXTENSION
                ],
                parameters={
                    "research_depth": "comprehensive",
                    "source_types": "academic, peer-reviewed, industry reports",
                    "require_citations": True
                },
                priority=10,  # Applied first
                enabled=True
            ),
            SkillInstance(
                skill_id="information-synthesis",
                application_modes=[SkillApplicationMode.SYSTEM_PROMPT_EXTENSION],
                parameters={
                    "output_structure": "hierarchical",
                    "detail_level": "comprehensive",
                    "include_sources": True
                },
                priority=5,  # Applied second
                enabled=True
            ),
            SkillInstance(
                skill_id="task-decomposition",
                application_modes=[SkillApplicationMode.ORCHESTRATION_STEP],
                parameters={
                    "max_depth": 2,
                    "output_format": "tree"
                },
                priority=0,  # Applied last
                enabled=True
            )
        ]
    )
    
    print(f"Agent: {agent.name}")
    print(f"Skills: {len(agent.skills)} configured")
    for skill in agent.skills:
        print(f"  - {skill.skill_id} (priority: {skill.priority}, modes: {[m.value for m in skill.application_modes]})")
    
    print(f"\nSending message: 'Research the impact of AI on healthcare'")
    
    executor = get_agent_executor()
    result = await executor.run(
        agent=agent,
        message="Research the impact of artificial intelligence on healthcare delivery and patient outcomes",
        use_tools=False
    )
    
    print(f"\n✓ Response received ({len(result['response'])} chars)")
    print(f"Duration: {result['duration_seconds']:.2f}s")
    print(f"\nResponse:\n{'-'*80}\n{result['response'][:1000]}...\n{'-'*80}")


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("  SKILL INTEGRATION EXAMPLES")
    print("="*80)
    
    # Check for required environment variables
    if not os.getenv("LLM_PROVIDER") or not os.getenv("LLM_MODEL"):
        print("\n⚠ WARNING: LLM environment variables not set!")
        print("Please set the following environment variables:")
        print("  - LLM_PROVIDER (e.g., 'groq')")
        print("  - LLM_MODEL (e.g., 'llama3-8b-8192')")
        print("  - LLM_ENDPOINT (optional)")
        print("  - LLM_API_KEY_ENV (e.g., 'GROQ_API_KEY')")
        print("\nRunning with default values (may fail)...")
    
    examples = [
        ("Simple Skill Assignment", example_1_simple_skill_assignment),
        ("System Prompt Extension", example_2_system_prompt_extension),
        ("Few-Shot Examples", example_3_few_shot_examples),
        ("Orchestration Steps", example_4_orchestration_steps),
        ("Multiple Skills", example_5_multiple_skills),
    ]
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("  Examples completed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
