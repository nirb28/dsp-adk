"""
Example 05: Simple Sequential Graph (YAML-based)

This example demonstrates loading graph and agent configurations from YAML files
and executing them through the ADK.

Usage:
    python run_from_yaml.py
"""
import asyncio
import httpx
import hashlib
import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.storage import resolve_env_variables

# Load environment variables
env_path = project_root / '.env'
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


async def main():
    """Run the simple graph example using YAML configurations."""
    print("=" * 60)
    print("Example 05: Simple Sequential Graph (YAML-based)")
    print("=" * 60)
    
    # Get JWT token
    jwt_token = await get_jwt_token()
    if not jwt_token:
        print("\n❌ Failed to get JWT token. Exiting.")
        return
    
    # Set up headers with JWT token
    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }
    
    async with httpx.AsyncClient(base_url=ADK_URL, timeout=120.0, headers=headers) as client:
        # 1. Load graph configuration from YAML
        print("\n1. Loading Graph Configuration from YAML:")
        graph_file = Path(__file__).parent / "graph.yaml"
        
        if not graph_file.exists():
            print(f"   ✗ Graph file not found: {graph_file}")
            return
        
        with open(graph_file, 'r') as f:
            graph_config = yaml.safe_load(f)
        
        # Resolve environment variables in graph config
        graph_config = resolve_env_variables(graph_config)
        
        print(f"   Graph ID: {graph_config['id']}")
        print(f"   Graph Name: {graph_config['name']}")
        print(f"   Nodes: {len(graph_config['nodes'])}")
        print(f"   Edges: {len(graph_config['edges'])}")
        
        # 2. Load example configuration from YAML
        print("\n2. Loading Example Configuration from YAML:")
        config_file = Path(__file__).parent / "config.yaml"
        
        if not config_file.exists():
            print(f"   ✗ Config file not found: {config_file}")
            return
        
        with open(config_file, 'r') as f:
            example_config = yaml.safe_load(f)
        
        # Resolve environment variables in example config
        example_config = resolve_env_variables(example_config)
        
        print(f"   Example ID: {example_config['id']}")
        print(f"   Example Name: {example_config['name']}")
        print(f"   Difficulty: {example_config['difficulty']}")
        
        # 3. Create the graph
        print("\n3. Creating Graph in ADK:")
        
        # Delete existing graph first
        delete_response = await client.delete(f"/graphs/{graph_config['id']}")
        if delete_response.status_code in [200, 204]:
            print(f"   ✓ Deleted existing graph")
        
        response = await client.post("/graphs", json=graph_config)
        if response.status_code in [200, 201]:
            print(f"   ✓ Graph created successfully")
        elif response.status_code == 422:
            print(f"   ✗ Validation error: {response.text}")
            return
        else:
            print(f"   ✗ Failed to create graph: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        # 4. Create an agent that uses the graph
        print("\n4. Creating Agent with Graph from YAML:")
        
        # Get LLM configuration from environment and resolve any ${VAR} references
        llm_provider = resolve_env_variables(os.getenv("LLM_PROVIDER", "openai"))
        llm_model = resolve_env_variables(os.getenv("LLM_MODEL", ""))
        llm_endpoint = resolve_env_variables(os.getenv("LLM_ENDPOINT", ""))
        llm_api_key = resolve_env_variables(os.getenv("LLM_API_KEY", ""))
        
        # If using NVIDIA provider, use NVIDIA-specific settings
        if llm_provider == "nvidia":
            llm_model = llm_model or resolve_env_variables(os.getenv("NVIDIA_LLM_MODEL", "meta/llama-3.1-8b-instruct"))
            llm_endpoint = llm_endpoint or resolve_env_variables(os.getenv("NVIDIA_ENDPOINT", "https://integrate.api.nvidia.com/v1"))
            llm_api_key = llm_api_key or resolve_env_variables(os.getenv("NVIDIA_API_KEY", ""))
        elif llm_provider == "openai":
            # Azure OpenAI fallback when not explicitly set
            llm_endpoint = llm_endpoint or resolve_env_variables(os.getenv("AZURE_ENDPOINT", ""))
            llm_api_key = llm_api_key or resolve_env_variables(os.getenv("AZURE_API_KEY", ""))
            llm_model = llm_model or "gpt-4.1"
        
        # Final fallbacks if still missing
        if not llm_endpoint:
            llm_endpoint = resolve_env_variables(os.getenv("AZURE_ENDPOINT", "")) or \
                           resolve_env_variables(os.getenv("NVIDIA_ENDPOINT", ""))
        if not llm_model:
            llm_model = "gpt-4.1"
        
        # Fallback to other API keys if not set
        if not llm_api_key:
            llm_api_key = resolve_env_variables(os.getenv("AZURE_API_KEY", "")) or \
                         resolve_env_variables(os.getenv("NVIDIA_API_KEY", "")) or \
                         resolve_env_variables(os.getenv("GROQ_API_KEY", ""))
        
        if not llm_api_key or not llm_model or not llm_endpoint:
            print("   ✗ Missing LLM configuration:")
            if not llm_api_key:
                print("      - API key not found")
            if not llm_model:
                print("      - Model not specified")
            if not llm_endpoint:
                print("      - Endpoint not specified")
            return
        
        agent_id = f"{example_config['id']}-agent"
        agent_config = {
            "id": agent_id,
            "name": f"{example_config['name']} Agent",
            "description": example_config.get('description', 'Agent from YAML configuration'),
            "agent_type": "conversational",
            "llm": {
                "provider": llm_provider,
                "model": llm_model,
                "endpoint": llm_endpoint,
                "api_key": llm_api_key,
                "temperature": 0.7,
                "max_tokens": 2048
            },
            "graph_id": graph_config['id'],
            "jwt_required": False,
            "tags": example_config.get('tags', [])
        }
        
        # Delete existing agent
        delete_response = await client.delete(f"/agents/{agent_id}")
        if delete_response.status_code in [200, 204]:
            print(f"   ✓ Deleted existing agent")
        
        # Create agent
        response = await client.post("/agents", json=agent_config)
        if response.status_code in [200, 201]:
            print(f"   ✓ Agent created successfully")
            print(f"   Agent ID: {agent_id}")
        else:
            print(f"   ✗ Failed to create agent: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        # 5. Execute the agent with example prompts
        print("\n5. Executing Agent with Example Prompts:")
        
        example_prompts = example_config.get('example_prompts', [
            "Research and summarize the history of the internet"
        ])
        
        for i, prompt in enumerate(example_prompts[:1], 1):  # Run first prompt only
            print(f"\n   Prompt {i}: {prompt}")
            print("   " + "-" * 56)
            
            execution_request = {
                "message": prompt,
                "use_tools": True
            }
            
            response = await client.post(f"/agents/{agent_id}/run", json=execution_request)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'response' in result:
                    print("\n   📝 Agent Response:")
                    print("   " + "-" * 56)
                    # Print response with proper wrapping
                    response_text = result['response']
                    for line in response_text.split('\n'):
                        print(f"   {line}")
                
                if 'tool_calls' in result and result['tool_calls']:
                    print("\n   🔧 Tools Used:")
                    for tool_call in result['tool_calls']:
                        print(f"      - {tool_call.get('tool_name', 'Unknown')}")
            else:
                print(f"\n   ✗ Execution failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        print("\n" + "=" * 60)
        print("✓ YAML-based graph execution complete!")
        print("=" * 60)
        print(f"\nConfiguration files used:")
        print(f"  - Graph: {graph_file}")
        print(f"  - Config: {config_file}")


if __name__ == "__main__":
    asyncio.run(main())
