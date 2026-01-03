"""
Test script for skill integration in agent execution.

This script validates that skills are properly applied to agents in different modes:
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
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.skill_service import get_skill_service
from app.services.agent_executor import get_agent_executor
from app.models.agents import AgentConfig, LLMConfig
from app.models.skills import SkillInstance, SkillApplicationMode


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_skill_loading():
    """Test that skills are loaded correctly."""
    print_section("TEST 1: Skill Loading")
    
    skill_service = get_skill_service()
    skills = skill_service.list_skills()
    
    print(f"✓ Loaded {len(skills)} skills:")
    for skill in skills:
        print(f"  - {skill.id}: {skill.name}")
        print(f"    Category: {skill.skill_category.value}")
        print(f"    Default modes: {[m.value for m in skill.default_application_modes]}")
        if skill.orchestration_steps:
            print(f"    Orchestration steps: {len(skill.orchestration_steps)}")
        if skill.examples:
            print(f"    Examples: {len(skill.examples)}")
        print()
    
    return len(skills) > 0


def test_system_prompt_extension():
    """Test applying skills as system prompt extensions."""
    print_section("TEST 2: System Prompt Extension")
    
    skill_service = get_skill_service()
    skill = skill_service.get_skill("code-generation")
    
    if not skill:
        print("✗ Skill 'code-generation' not found")
        return False
    
    base_prompt = "You are a helpful coding assistant."
    extended_prompt = skill_service.apply_skill_to_system_prompt(
        skill=skill,
        base_prompt=base_prompt,
        parameters={"language": "python"}
    )
    
    print(f"Base prompt length: {len(base_prompt)}")
    print(f"Extended prompt length: {len(extended_prompt)}")
    print(f"\nExtended prompt preview:")
    print("-" * 80)
    print(extended_prompt[:500] + "...")
    print("-" * 80)
    
    return len(extended_prompt) > len(base_prompt)


def test_few_shot_examples():
    """Test applying skills as few-shot examples."""
    print_section("TEST 3: Few-Shot Examples")
    
    skill_service = get_skill_service()
    skill = skill_service.get_skill("code-generation")
    
    if not skill:
        print("✗ Skill 'code-generation' not found")
        return False
    
    messages = [
        {"role": "system", "content": "You are a coding assistant."},
        {"role": "user", "content": "Write a function to sort a list"}
    ]
    
    print(f"Original messages: {len(messages)}")
    
    updated_messages = skill_service.apply_skill_as_few_shot_examples(
        skill=skill,
        messages=messages,
        parameters={}
    )
    
    print(f"Updated messages: {len(updated_messages)}")
    print(f"\nMessage structure:")
    for i, msg in enumerate(updated_messages):
        print(f"  {i+1}. {msg['role']}: {msg['content'][:60]}...")
    
    return len(updated_messages) > len(messages)


def test_orchestration_steps():
    """Test applying skills as orchestration steps."""
    print_section("TEST 4: Orchestration Steps")
    
    skill_service = get_skill_service()
    skill = skill_service.get_skill("task-decomposition")
    
    if not skill:
        print("✗ Skill 'task-decomposition' not found")
        return False
    
    messages = [
        {"role": "system", "content": "You are a planning assistant."}
    ]
    
    print(f"Original messages: {len(messages)}")
    print(f"Orchestration steps in skill: {len(skill.orchestration_steps)}")
    
    updated_messages = skill_service.apply_skill_as_orchestration(
        skill=skill,
        messages=messages,
        parameters={"max_depth": 3}
    )
    
    print(f"Updated messages: {len(updated_messages)}")
    print(f"\nOrchestration content preview:")
    print("-" * 80)
    for msg in updated_messages:
        if "Orchestration Steps" in msg.get("content", ""):
            print(msg["content"][:600] + "...")
            break
    print("-" * 80)
    
    return len(updated_messages) > len(messages)


def test_context_injection():
    """Test applying skills as context injection."""
    print_section("TEST 5: Context Injection")
    
    skill_service = get_skill_service()
    skill = skill_service.get_skill("research-methodology")
    
    if not skill:
        print("✗ Skill 'research-methodology' not found")
        return False
    
    messages = [
        {"role": "system", "content": "You are a research assistant."}
    ]
    
    print(f"Original messages: {len(messages)}")
    
    updated_messages = skill_service.apply_skill_as_context(
        skill=skill,
        messages=messages,
        parameters={
            "research_depth": "comprehensive",
            "source_types": "academic, peer-reviewed",
            "require_citations": "true"
        }
    )
    
    print(f"Updated messages: {len(updated_messages)}")
    print(f"\nContext injection preview:")
    print("-" * 80)
    for msg in updated_messages:
        if "Research Context" in msg.get("content", ""):
            print(msg["content"])
            break
    print("-" * 80)
    
    return len(updated_messages) > len(messages)


def test_multiple_skills():
    """Test applying multiple skills with different priorities."""
    print_section("TEST 6: Multiple Skills with Priorities")
    
    skill_service = get_skill_service()
    
    skill_instances = [
        SkillInstance(
            skill_id="research-methodology",
            application_modes=[SkillApplicationMode.CONTEXT_INJECTION],
            parameters={"research_depth": "standard"},
            priority=10,
            enabled=True
        ),
        SkillInstance(
            skill_id="information-synthesis",
            application_modes=[SkillApplicationMode.SYSTEM_PROMPT_EXTENSION],
            parameters={"output_structure": "hierarchical"},
            priority=5,
            enabled=True
        ),
        SkillInstance(
            skill_id="task-decomposition",
            application_modes=[SkillApplicationMode.ORCHESTRATION_STEP],
            parameters={"max_depth": 2},
            priority=0,
            enabled=True
        )
    ]
    
    base_prompt = "You are a research assistant."
    base_messages = []
    
    print(f"Applying {len(skill_instances)} skills...")
    print(f"Priorities: {[s.priority for s in skill_instances]}")
    
    final_prompt, final_messages = skill_service.load_and_apply_skills(
        skill_instances=skill_instances,
        system_prompt=base_prompt,
        messages=base_messages
    )
    
    print(f"\nResults:")
    print(f"  Final prompt length: {len(final_prompt)}")
    print(f"  Final messages count: {len(final_messages)}")
    print(f"\nMessage types:")
    for i, msg in enumerate(final_messages):
        content_preview = msg['content'][:80].replace('\n', ' ')
        print(f"  {i+1}. {msg['role']}: {content_preview}...")
    
    return len(final_messages) > 0 and len(final_prompt) > len(base_prompt)


async def test_agent_execution_with_skills():
    """Test full agent execution with skills applied."""
    print_section("TEST 7: Agent Execution with Skills")
    
    # Check for required environment variables
    if not os.getenv("LLM_PROVIDER") or not os.getenv("LLM_MODEL"):
        print("⚠ Skipping agent execution test - LLM environment variables not set")
        print("  Set LLM_PROVIDER, LLM_MODEL, LLM_ENDPOINT, and LLM_API_KEY_ENV to run this test")
        return True
    
    # Create test agent with skills
    agent = AgentConfig(
        id="test-agent-with-skills",
        name="Test Agent with Skills",
        description="Test agent for skill integration",
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "groq"),
            model=os.getenv("LLM_MODEL", "llama3-8b-8192"),
            endpoint=os.getenv("LLM_ENDPOINT"),
            api_key_env=os.getenv("LLM_API_KEY_ENV", "GROQ_API_KEY"),
            temperature=0.7,
            max_tokens=1024,
            system_prompt="You are a helpful assistant."
        ),
        skills=[
            SkillInstance(
                skill_id="code-generation",
                application_modes=[
                    SkillApplicationMode.SYSTEM_PROMPT_EXTENSION,
                    SkillApplicationMode.FEW_SHOT_EXAMPLES
                ],
                parameters={"language": "python"},
                priority=5,
                enabled=True
            )
        ]
    )
    
    executor = get_agent_executor()
    
    print(f"Agent: {agent.name}")
    print(f"Skills configured: {len(agent.skills)}")
    print(f"Test message: 'Write a function to reverse a string'")
    
    try:
        result = await executor.run(
            agent=agent,
            message="Write a function to reverse a string",
            use_tools=False,
            mock_tools=False
        )
        
        print(f"\n✓ Execution successful!")
        print(f"  Response length: {len(result['response'])}")
        print(f"  Duration: {result['duration_seconds']:.2f}s")
        print(f"  Tokens used: {result.get('usage', {}).get('total_tokens', 'N/A')}")
        print(f"\nResponse preview:")
        print("-" * 80)
        print(result['response'][:500] + "...")
        print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"✗ Execution failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  SKILL INTEGRATION TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Skill Loading", test_skill_loading),
        ("System Prompt Extension", test_system_prompt_extension),
        ("Few-Shot Examples", test_few_shot_examples),
        ("Orchestration Steps", test_orchestration_steps),
        ("Context Injection", test_context_injection),
        ("Multiple Skills", test_multiple_skills),
    ]
    
    results = {}
    
    # Run synchronous tests
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results[test_name] = False
    
    # Run async test
    try:
        results["Agent Execution"] = asyncio.run(test_agent_execution_with_skills())
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        results["Agent Execution"] = False
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
