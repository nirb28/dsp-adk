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
import yaml
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


def resolve_env_vars(data):
    """Recursively resolve environment variable references in data structure."""
    if isinstance(data, dict):
        return {k: resolve_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Handle ${VAR_NAME} or ${VAR_NAME:default} syntax
        if data.startswith("${") and "}" in data:
            var_part = data[2:data.index("}")]
            if ":" in var_part:
                var_name, default = var_part.split(":", 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(var_part, data)
        return data
    else:
        return data


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
        graph_config = resolve_env_vars(graph_config)
        
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
        example_config = resolve_env_vars(example_config)
        
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
        
        # Get LLM configuration from environment
        llm_provider = os.getenv("LLM_PROVIDER", "nvidia")
        llm_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        llm_endpoint = os.getenv("LLM_ENDPOINT") or os.getenv("NVIDIA_ENDPOINT", "https://integrate.api.nvidia.com/v1")
        
        # Resolve LLM_API_KEY
        llm_api_key_raw = os.getenv("LLM_API_KEY", "")
        if llm_api_key_raw.startswith("${") and llm_api_key_raw.endswith("}"):
            var_name = llm_api_key_raw[2:-1]
            llm_api_key = os.getenv(var_name)
        else:
            llm_api_key = llm_api_key_raw
        
        if not llm_api_key:
            llm_api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("GROQ_API_KEY")
        
        if not llm_api_key:
            print("   ✗ No LLM API key found")
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
