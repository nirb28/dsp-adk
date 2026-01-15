"""
Hello World LangGraph example

This script:
1) Loads a minimal LangGraph and agent from YAML
2) Deploys them to ADK via REST (/graphs, /agents)
3) Runs the agent via REST (/agents/{id}/run)
4) Prints the response and shows the graph path

Usage:
    python run_from_yaml.py

Environment:
- ADK_URL:       ADK base URL (default http://localhost:8100)
- JWT_URL:       JWT service URL (default http://localhost:5000)
- LLM_PROVIDER:  e.g., openai | nvidia | groq (default openai)
- LLM_MODEL:     model name (default gpt-4.1-mini)
- LLM_ENDPOINT:  provider endpoint (default OpenAI endpoint)
- LLM_API_KEY:   provider API key (required unless mock tools used)
"""
import asyncio
import hashlib
import os
import sys
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.storage import resolve_env_variables

# Load environment variables
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

ADK_URL = os.getenv("ADK_URL", "http://localhost:8100")
JWT_URL = os.getenv("JWT_URL", "http://localhost:5000")


def resolve_env(data):
    return resolve_env_variables(data)


def print_step(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def describe_graph_path(graph_config: dict):
    print("Graph path (expected execution order):")
    edges = graph_config.get("edges", [])
    for edge in edges:
        if edge.get("source") and edge.get("target"):
            print(f"  {edge['source']} -> {edge['target']}")


async def get_jwt_token(username: str = "admin", password: str = "password") -> str | None:
    print_step("Authenticating with JWT service")
    try:
        async with httpx.AsyncClient(base_url=JWT_URL, timeout=15.0) as client:
            resp = await client.post("/token", json={"username": username, "password": password})
            if resp.status_code == 200:
                token = resp.json().get("access_token")
                print("✓ Authenticated")
                return token
            print(f"✗ Auth failed: {resp.status_code} {resp.text}")
    except Exception as exc:  # noqa: BLE001
        print(f"✗ JWT service error: {exc}")
    return None


async def main():
    print_step("Hello World LangGraph (YAML -> ADK -> REST run)")

    token = await get_jwt_token()
    if not token:
        return
    headers = {"Authorization": f"Bearer {token}"}

    graph_path = Path(__file__).parent / "graph.yaml"
    agent_path = Path(__file__).parent / "agent.yaml"

    async with httpx.AsyncClient(base_url=ADK_URL, headers=headers, timeout=60.0) as client:
        # Load graph YAML
        print_step("1) Load graph YAML")
        try:
            raw_graph_text = graph_path.read_text(encoding="utf-8")
            graph_config = resolve_env(yaml.safe_load(raw_graph_text))
            print(f"Graph ID: {graph_config['id']}")
            describe_graph_path(graph_config)
        except Exception as exc:
            print("✗ Failed to load/resolve graph YAML:")
            print(f"  File: {graph_path}")
            print(f"  Error: {exc}")
            return

        # Load agent YAML
        print_step("2) Load agent YAML")
        try:
            raw_agent_text = agent_path.read_text(encoding="utf-8")
            agent_config = resolve_env(yaml.safe_load(raw_agent_text))
        except Exception as exc:
            print("✗ Failed to load/resolve agent YAML:")
            print(f"  File: {agent_path}")
            print(f"  Error: {exc}")
            return
        print(f"Agent ID: {agent_config.get('id')} (graph_id={agent_config.get('graph_id')})")

        # Validate resolved LLM fields from .env
        llm = agent_config.get("llm", {}) or {}
        print("Resolved LLM configuration (post .env resolution):")
        print(f"  provider: {llm.get('provider')}")
        print(f"  model:    {llm.get('model')}")
        print(f"  endpoint: {llm.get('endpoint')}")
        api_key_present = bool(llm.get('api_key'))
        print(f"  api_key set: {api_key_present}")
        if not llm.get("endpoint") or not api_key_present or not llm.get("model"):
            print("✗ Missing LLM configuration after resolving .env.")
            print("  Ensure .env exports LLM_PROVIDER, LLM_MODEL, LLM_ENDPOINT, LLM_API_KEY.")
            return

        # Deploy graph
        print_step("3) Deploy graph to ADK (/graphs)")
        try:
            await client.delete(f"/graphs/{graph_config['id']}")
            resp = await client.post("/graphs", json=graph_config)
            if resp.status_code not in (200, 201):
                print(f"✗ Create graph failed: {resp.status_code}")
                print(f"Response: {resp.text}")
                return
        except Exception as exc:
            print("✗ Error calling ADK /graphs endpoint:")
            print(f"  Error: {exc}")
            return
        print("✓ Graph created")

        # Deploy agent
        print_step("4) Deploy agent to ADK (/agents)")
        try:
            await client.delete(f"/agents/{agent_config['id']}")
            resp = await client.post("/agents", json=agent_config)
            if resp.status_code not in (200, 201):
                print(f"✗ Create agent failed: {resp.status_code}")
                print(f"Response: {resp.text}")
                return
        except Exception as exc:
            print("✗ Error calling ADK /agents endpoint:")
            print(f"  Error: {exc}")
            return
        print("✓ Agent created")

        # Run agent (which runs the LangGraph)
        print_step("5) Run agent via REST (/agents/{id}/run)")
        message = "Hello LangGraph"
        print(f"Request message: {message}")
        run_req = {"message": message, "use_tools": False}
        try:
            resp = await client.post(f"/agents/{agent_config['id']}/run", json=run_req)
            if resp.status_code != 200:
                print(f"✗ Run failed: {resp.status_code}")
                print(f"Response: {resp.text}")
                return
            result = resp.json()
        except Exception as exc:
            print("✗ Error calling ADK /agents/{id}/run endpoint:")
            print(f"  Error: {exc}")
            return
        print("\nGraph steps (expected): START -> greeter -> END")
        print("Agent reply:")
        print(result.get("response", "<no response>"))
        if result.get("usage"):
            print(f"Usage: {result['usage']}")

    print_step("Done")


if __name__ == "__main__":
    asyncio.run(main())
