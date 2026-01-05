"""
Example 05: Simple Sequential Graph

This example demonstrates a simple sequential graph that chains
multiple agents together.

Usage:
    python run.py
"""
import asyncio
import httpx
import json
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


async def main():
    """Run the simple graph example."""
    print("=" * 60)
    print("Example 05: Simple Sequential Graph")
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
        
        # 2. Create the graph configuration
        print("\n2. Creating Graph Configuration:")
        graph_config = {
            "id": "research-summarize-graph",
            "name": "Research and Summarize",
            "description": "Research a topic and create a concise summary",
            "type": "langgraph",
            "nodes": [
                {
                    "id": "research",
                    "name": "Research Node",
                    "type": "agent",
                    "agent_id": "research-agent",
                    "config": {
                        "research_depth": "quick",
                        "max_sources": 3
                    }
                },
                {
                    "id": "summarize",
                    "name": "Summarize Node",
                    "type": "agent",
                    "agent_id": "conversational-assistant",
                    "config": {
                        "verbosity": "concise"
                    }
                }
            ],
            "edges": [
                {
                    "id": "start_to_research",
                    "source": "START",
                    "target": "research",
                    "type": "normal"
                },
                {
                    "id": "research_to_summarize",
                    "source": "research",
                    "target": "summarize",
                    "type": "normal"
                },
                {
                    "id": "summarize_to_end",
                    "source": "summarize",
                    "target": "END",
                    "type": "normal"
                }
            ],
            "entry_point": "research",
            "jwt_required": False
        }
        
        print(f"   Graph ID: {graph_config['id']}")
        print(f"   Graph Name: {graph_config['name']}")
        print(f"   Nodes: {len(graph_config['nodes'])}")
        print(f"   Edges: {len(graph_config['edges'])}")
        
        # 3. Create/update the graph
        print("\n3. Creating Graph in ADK:")
        response = await client.post("/graphs", json=graph_config)
        if response.status_code in [200, 201]:
            print(f"   ✓ Graph created successfully")
        elif response.status_code == 422:
            print(f"   ✗ Validation error: {response.text}")
            return
        elif response.status_code == 401:
            print(f"   ! Authentication required - graph may already exist, continuing...")
        else:
            print(f"   ! Status {response.status_code} - graph may already exist, continuing...")
        
        # 4. Create an agent that uses the graph
        print("\n4. Creating Agent with Graph Capability:")
        
        # Get LLM configuration from environment variables
        llm_provider = os.getenv("LLM_PROVIDER", "nvidia")
        llm_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        llm_endpoint = os.getenv("LLM_ENDPOINT") or os.getenv("NVIDIA_ENDPOINT", "https://integrate.api.nvidia.com/v1")
        
        # Resolve LLM_API_KEY which might reference another variable like ${NVIDIA_API_KEY}
        llm_api_key_raw = os.getenv("LLM_API_KEY", "")
        if llm_api_key_raw.startswith("${") and llm_api_key_raw.endswith("}"):
            # Extract variable name from ${VARIABLE_NAME}
            var_name = llm_api_key_raw[2:-1]
            llm_api_key = os.getenv(var_name)
        else:
            llm_api_key = llm_api_key_raw
        
        # Fallback to direct API key variables if LLM_API_KEY is not set
        if not llm_api_key:
            llm_api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not llm_api_key:
            print("   ✗ No LLM API key found in environment variables")
            print("   Please set LLM_API_KEY, NVIDIA_API_KEY, GROQ_API_KEY, or OPENAI_API_KEY")
            return
        
        print(f"   LLM Provider: {llm_provider}")
        print(f"   LLM Model: {llm_model}")
        print(f"   LLM Endpoint: {llm_endpoint}")
        print(f"   API Key: {'*' * 10}{llm_api_key[-4:] if len(llm_api_key) > 4 else '****'}")
        
        agent_config = {
            "id": "simple-graph-agent",
            "name": "Simple Graph Agent",
            "description": "Agent that executes the research and summarize graph",
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
            "jwt_required": False
        }
        
        # Try to delete existing agent first to ensure clean state
        delete_response = await client.delete(f"/agents/{agent_config['id']}")
        if delete_response.status_code in [200, 204]:
            print(f"   ✓ Deleted existing agent")
        
        # Create the agent
        response = await client.post("/agents", json=agent_config)
        if response.status_code in [200, 201]:
            print(f"   ✓ Agent created successfully")
            agent_data = response.json()
            if 'agent' in agent_data:
                created_agent = agent_data['agent']
                print(f"   Configured with: {created_agent.get('llm', {}).get('provider')} / {created_agent.get('llm', {}).get('model')}")
        elif response.status_code == 422:
            print(f"   ✗ Validation error: {response.text}")
            return
        elif response.status_code == 401:
            print(f"   ! Authentication required")
            return
        else:
            print(f"   ✗ Failed to create agent: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        # 5. Execute the agent (which runs the graph)
        print("\n5. Executing Agent (runs the graph):")
        topic = "history of the internet"
        print(f"   Topic: {topic}")
        
        execution_request = {
            "message": f"Research and summarize: {topic}",
            "use_tools": True
        }
        
        print("\n   Sending execution request...")
        response = await client.post(f"/agents/{agent_config['id']}/run", json=execution_request)
        
        if response.status_code == 200:
            result = response.json()
            print("\n6. Execution Results:")
            print("=" * 60)
            
            if 'response' in result:
                print("\n� Agent Response:")
                print("-" * 60)
                print(result['response'])
            
            if 'tool_calls' in result and result['tool_calls']:
                print("\n� Tools Used:")
                print("-" * 60)
                for tool_call in result['tool_calls']:
                    print(f"   - {tool_call.get('tool_name', 'Unknown')}")
            
            print("\n" + "=" * 60)
            print("✓ Graph execution complete!")
            print("=" * 60)
        else:
            print(f"\n✗ Execution failed: {response.status_code}")
            print(f"   Response: {response.text}")


if __name__ == "__main__":
    asyncio.run(main())
