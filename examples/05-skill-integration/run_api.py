"""
Example: Skill Integration

Demonstrates how to use skills with agents in different application modes:
- System prompt extension
- Few-shot examples
- Orchestration steps
- Context injection

This example uses the ADK REST API to create and execute agents with skills.
"""
import asyncio
import httpx
import hashlib
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

ADK_URL = "http://localhost:8100"
JWT_URL = "http://localhost:5000"


async def get_jwt_token(username: str = "admin", password: str = "password") -> str:
    """Get JWT token from the JWT service."""
    print(f"\n🔐 Authenticating with JWT service...")
    print(f"   Username: {username}")
    
    # Hash the password (SHA-256 as used in users.yaml)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    async with httpx.AsyncClient(base_url=JWT_URL, timeout=30.0) as client:
        try:
            response = await client.post(
                "/token",
                json={
                    "username": username,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                print(f"   ✓ Authentication successful")
                return token
            else:
                print(f"   ✗ Authentication failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ✗ Error connecting to JWT service: {e}")
            print(f"   Make sure JWT service is running at {JWT_URL}")
            return None




async def example_1_simple_skill_assignment(client: httpx.AsyncClient):
    """Example 1: Simple skill assignment using skill IDs."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple Skill Assignment")
    print("="*80)
    
    agent_config = {
        "id": "simple-coding-agent",
        "name": "Simple Coding Agent",
        "description": "Agent with simple skill assignment",
        "llm": {
            "provider": os.getenv("LLM_PROVIDER", "nvidia"),
            "model": os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
            "endpoint": os.getenv("LLM_ENDPOINT", "https://integrate.api.nvidia.com/v1"),
            "api_key": os.getenv("LLM_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 1024,
            "system_prompt": "You are a helpful coding assistant."
        },
        "skills": ["code-generation"],  # Simple skill ID
        "jwt_required": False
    }
    
    print(f"Agent: {agent_config['name']}")
    print(f"Skills: {agent_config['skills']}")
    
    # Delete existing agent if it exists
    await client.delete(f"/agents/{agent_config['id']}")
    
    # Create agent
    response = await client.post("/agents", json=agent_config)
    if response.status_code not in [200, 201]:
        print(f"✗ Failed to create agent: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print(f"✓ Agent created successfully")
    
    # Execute agent
    print(f"\nSending message: 'Write a Python function to calculate factorial'")
    
    execution_request = {
        "message": "Write a Python function to calculate factorial",
        "use_tools": False
    }
    
    response = await client.post(f"/agents/{agent_config['id']}/run", json=execution_request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Response received ({len(result['response'])} chars)")
        print(f"Duration: {result.get('duration_seconds', 0):.2f}s")
        print(f"\nResponse:\n{'-'*80}\n{result['response']}\n{'-'*80}")
    else:
        print(f"✗ Execution failed: {response.status_code}")
        print(f"Response: {response.text}")


async def example_2_system_prompt_extension(client: httpx.AsyncClient):
    """Example 2: Using skills as system prompt extensions."""
    print("\n" + "="*80)
    print("EXAMPLE 2: System Prompt Extension")
    print("="*80)
    
    agent_config = {
        "id": "research-agent-prompt",
        "name": "Research Agent (Prompt Extension)",
        "description": "Agent using research methodology as prompt extension",
        "llm": {
            "provider": os.getenv("LLM_PROVIDER", "nvidia"),
            "model": os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
            "endpoint": os.getenv("LLM_ENDPOINT", "https://integrate.api.nvidia.com/v1"),
            "api_key": os.getenv("LLM_API_KEY"),
            "temperature": 0.3,
            "max_tokens": 2048,
            "system_prompt": "You are a research assistant."
        },
        "skills": [
            {
                "skill_id": "research-methodology",
                "application_modes": ["system_prompt_extension"],
                "parameters": {
                    "research_depth": "standard",
                    "source_types": "academic, news",
                    "require_citations": True
                },
                "enabled": True
            }
        ],
        "jwt_required": False
    }
    
    print(f"Agent: {agent_config['name']}")
    print(f"Skill: research-methodology (system_prompt_extension)")
    
    await client.delete(f"/agents/{agent_config['id']}")
    
    response = await client.post("/agents", json=agent_config)
    if response.status_code not in [200, 201]:
        print(f"✗ Failed to create agent: {response.status_code}")
        return
    
    print(f"✓ Agent created successfully")
    print(f"\nSending message: 'What are the latest developments in quantum computing?'")
    
    execution_request = {
        "message": "What are the latest developments in quantum computing?",
        "use_tools": False
    }
    
    response = await client.post(f"/agents/{agent_config['id']}/run", json=execution_request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Response received ({len(result['response'])} chars)")
        print(f"Duration: {result.get('duration_seconds', 0):.2f}s")
        print(f"\nResponse:\n{'-'*80}\n{result['response'][:500]}...\n{'-'*80}")
    else:
        print(f"✗ Execution failed: {response.status_code}")


async def example_3_few_shot_examples(client: httpx.AsyncClient):
    """Example 3: Using skills with few-shot examples."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Few-Shot Examples")
    print("="*80)
    
    agent_config = {
        "id": "coding-agent-examples",
        "name": "Coding Agent (Few-Shot)",
        "description": "Agent using code generation with few-shot examples",
        "llm": {
            "provider": os.getenv("LLM_PROVIDER", "nvidia"),
            "model": os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
            "endpoint": os.getenv("LLM_ENDPOINT", "https://integrate.api.nvidia.com/v1"),
            "api_key": os.getenv("LLM_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 1024,
            "system_prompt": "You are a Python coding expert."
        },
        "skills": [
            {
                "skill_id": "code-generation",
                "application_modes": ["system_prompt_extension", "few_shot_examples"],
                "parameters": {"language": "python"},
                "enabled": True
            }
        ],
        "jwt_required": False
    }
    
    print(f"Agent: {agent_config['name']}")
    print(f"Skill: code-generation (system_prompt + few_shot_examples)")
    
    await client.delete(f"/agents/{agent_config['id']}")
    
    response = await client.post("/agents", json=agent_config)
    if response.status_code not in [200, 201]:
        print(f"✗ Failed to create agent: {response.status_code}")
        return
    
    print(f"✓ Agent created successfully")
    print(f"\nSending message: 'Create a function to check if a number is prime'")
    
    execution_request = {
        "message": "Create a function to check if a number is prime",
        "use_tools": False
    }
    
    response = await client.post(f"/agents/{agent_config['id']}/run", json=execution_request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Response received ({len(result['response'])} chars)")
        print(f"Duration: {result.get('duration_seconds', 0):.2f}s")
        print(f"\nResponse:\n{'-'*80}\n{result['response']}\n{'-'*80}")
    else:
        print(f"✗ Execution failed: {response.status_code}")


async def example_4_orchestration_steps(client: httpx.AsyncClient):
    """Example 4: Using skills with orchestration steps."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Orchestration Steps")
    print("="*80)
    
    agent_config = {
        "id": "planning-agent",
        "name": "Planning Agent (Orchestration)",
        "description": "Agent using task decomposition with orchestration",
        "llm": {
            "provider": os.getenv("LLM_PROVIDER", "nvidia"),
            "model": os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
            "endpoint": os.getenv("LLM_ENDPOINT", "https://integrate.api.nvidia.com/v1"),
            "api_key": os.getenv("LLM_API_KEY"),
            "temperature": 0.5,
            "max_tokens": 2048,
            "system_prompt": "You are a project planning expert."
        },
        "skills": [
            {
                "skill_id": "task-decomposition",
                "application_modes": ["orchestration_step"],
                "parameters": {
                    "max_depth": 3,
                    "output_format": "tree",
                    "include_estimates": True
                },
                "enabled": True
            }
        ],
        "jwt_required": False
    }
    
    print(f"Agent: {agent_config['name']}")
    print(f"Skill: task-decomposition (orchestration_step)")
    
    await client.delete(f"/agents/{agent_config['id']}")
    
    response = await client.post("/agents", json=agent_config)
    if response.status_code not in [200, 201]:
        print(f"✗ Failed to create agent: {response.status_code}")
        return
    
    print(f"✓ Agent created successfully")
    print(f"\nSending message: 'Plan a mobile app development project'")
    
    execution_request = {
        "message": "Plan a mobile app development project for a food delivery service",
        "use_tools": False
    }
    
    response = await client.post(f"/agents/{agent_config['id']}/run", json=execution_request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Response received ({len(result['response'])} chars)")
        print(f"Duration: {result.get('duration_seconds', 0):.2f}s")
        print(f"\nResponse:\n{'-'*80}\n{result['response'][:800]}...\n{'-'*80}")
    else:
        print(f"✗ Execution failed: {response.status_code}")


async def example_5_multiple_skills(client: httpx.AsyncClient):
    """Example 5: Using multiple skills with different priorities."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Multiple Skills with Priorities")
    print("="*80)
    
    agent_config = {
        "id": "advanced-research-agent",
        "name": "Advanced Research Agent",
        "description": "Agent with multiple skills applied in priority order",
        "llm": {
            "provider": os.getenv("LLM_PROVIDER", "nvidia"),
            "model": os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
            "endpoint": os.getenv("LLM_ENDPOINT", "https://integrate.api.nvidia.com/v1"),
            "api_key": os.getenv("LLM_API_KEY"),
            "temperature": 0.3,
            "max_tokens": 3072,
            "system_prompt": "You are an expert research analyst."
        },
        "skills": [
            {
                "skill_id": "research-methodology",
                "application_modes": ["context_injection", "system_prompt_extension"],
                "parameters": {
                    "research_depth": "comprehensive",
                    "source_types": "academic, peer-reviewed, industry reports",
                    "require_citations": True
                },
                "priority": 10,
                "enabled": True
            },
            {
                "skill_id": "information-synthesis",
                "application_modes": ["system_prompt_extension"],
                "parameters": {
                    "output_structure": "hierarchical",
                    "detail_level": "comprehensive",
                    "include_sources": True
                },
                "priority": 5,
                "enabled": True
            },
            {
                "skill_id": "task-decomposition",
                "application_modes": ["orchestration_step"],
                "parameters": {
                    "max_depth": 2,
                    "output_format": "tree"
                },
                "priority": 0,
                "enabled": True
            }
        ],
        "jwt_required": False
    }
    
    print(f"Agent: {agent_config['name']}")
    print(f"Skills: {len(agent_config['skills'])} configured")
    for skill in agent_config['skills']:
        print(f"  - {skill['skill_id']} (priority: {skill['priority']}, modes: {skill['application_modes']})")
    
    await client.delete(f"/agents/{agent_config['id']}")
    
    response = await client.post("/agents", json=agent_config)
    if response.status_code not in [200, 201]:
        print(f"✗ Failed to create agent: {response.status_code}")
        return
    
    print(f"✓ Agent created successfully")
    print(f"\nSending message: 'Research the impact of AI on healthcare'")
    
    execution_request = {
        "message": "Research the impact of artificial intelligence on healthcare delivery and patient outcomes",
        "use_tools": False
    }
    
    response = await client.post(f"/agents/{agent_config['id']}/run", json=execution_request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Response received ({len(result['response'])} chars)")
        print(f"Duration: {result.get('duration_seconds', 0):.2f}s")
        print(f"\nResponse:\n{'-'*80}\n{result['response'][:1000]}...\n{'-'*80}")
    else:
        print(f"✗ Execution failed: {response.status_code}")


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("  SKILL INTEGRATION EXAMPLES (REST API)")
    print("="*80)
    
    # Check for required environment variables
    if not os.getenv("LLM_API_KEY"):
        print("\n⚠ WARNING: LLM_API_KEY not set!")
        print("Please set LLM_API_KEY in your .env file")
        print("\nRunning with default values (may fail)...")
    
    print(f"\nADK Server: {ADK_URL}")
    print(f"LLM Provider: {os.getenv('LLM_PROVIDER', 'nvidia')}")
    print(f"LLM Model: {os.getenv('LLM_MODEL', 'openai/gpt-oss-120b')}")
    
    # Get JWT token
    jwt_token = await get_jwt_token()
    if not jwt_token:
        print("\n❌ Failed to get JWT token. Exiting.")
        return
    
    # Set up headers with JWT token
    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }
    
    examples = [
        ("Simple Skill Assignment", example_1_simple_skill_assignment),
        ("System Prompt Extension", example_2_system_prompt_extension),
        ("Few-Shot Examples", example_3_few_shot_examples),
        ("Orchestration Steps", example_4_orchestration_steps),
        ("Multiple Skills", example_5_multiple_skills),
    ]
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=120.0, headers=headers) as client:
        # Check if ADK server is running
        try:
            response = await client.get("/health")
            if response.status_code != 200:
                print(f"\n✗ ADK server not responding properly at {ADK_URL}")
                print("Please make sure the ADK server is running: python run.py")
                return
        except Exception as e:
            print(f"\n✗ Cannot connect to ADK server at {ADK_URL}")
            print(f"Error: {e}")
            print("Please make sure the ADK server is running: python run.py")
            return
        
        print(f"✓ Connected to ADK server\n")
        
        for name, example_func in examples:
            try:
                await example_func(client)
            except Exception as e:
                print(f"\n✗ Example '{name}' failed: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "="*80)
    print("  Examples completed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
