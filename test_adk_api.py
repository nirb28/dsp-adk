"""
Test script for ADK API endpoints.
Run this script to verify the ADK platform is working correctly.

Usage:
    python test_adk_api.py [--jwt-url URL] [--adk-url URL]
"""
import argparse
import requests
import json
import sys


def get_jwt_token(jwt_url: str, username: str = "admin", password: str = "password") -> str:
    """Get JWT token from the JWT service."""
    try:
        response = requests.post(
            f"{jwt_url}/token",
            json={"username": username, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"Failed to get JWT token: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error connecting to JWT service: {e}")
        return None


def test_health(base_url: str) -> bool:
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_list_agents(base_url: str, token: str = None) -> bool:
    """Test listing agents."""
    print("\n=== Testing List Agents ===")
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(f"{base_url}/agents", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total agents: {data.get('total', 0)}")
        for agent in data.get("agents", []):
            print(f"  - {agent['id']}: {agent['name']} ({agent['type']})")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_list_tools(base_url: str, token: str = None) -> bool:
    """Test listing tools."""
    print("\n=== Testing List Tools ===")
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(f"{base_url}/tools", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total tools: {data.get('total', 0)}")
        for tool in data.get("tools", []):
            print(f"  - {tool['id']}: {tool['name']} ({tool['type']})")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_list_mcp_servers(base_url: str, token: str = None) -> bool:
    """Test listing MCP servers."""
    print("\n=== Testing List MCP Servers ===")
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(f"{base_url}/mcp-servers", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total servers: {data.get('total', 0)}")
        for server in data.get("servers", []):
            print(f"  - {server['id']}: {server['name']} ({server['protocol']})")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_list_graphs(base_url: str, token: str = None) -> bool:
    """Test listing graphs."""
    print("\n=== Testing List Graphs ===")
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(f"{base_url}/graphs", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total graphs: {data.get('total', 0)}")
        for graph in data.get("graphs", []):
            print(f"  - {graph['id']}: {graph['name']} ({graph['type']})")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_create_agent(base_url: str, token: str) -> bool:
    """Test creating an agent."""
    print("\n=== Testing Create Agent ===")
    if not token:
        print("Skipping - no JWT token available")
        return True
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        agent_data = {
            "id": "test-agent-001",
            "name": "Test Agent",
            "description": "A test agent created by the test script",
            "type": "conversational",
            "status": "draft",
            "llm": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2048
            },
            "capabilities": ["tool_calling", "multi_turn"],
            "tools": [],
            "mcp_servers": [],
            "jwt_required": False,
            "tags": ["test"]
        }
        
        response = requests.post(
            f"{base_url}/agents",
            json=agent_data,
            headers=headers,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [200, 201, 400]  # 400 if already exists
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_get_tool_schema(base_url: str, tool_id: str = "calculator") -> bool:
    """Test getting tool schema."""
    print(f"\n=== Testing Get Tool Schema ({tool_id}) ===")
    try:
        response = requests.get(f"{base_url}/tools/{tool_id}/schema", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Schema: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [200, 404]
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test ADK API endpoints")
    parser.add_argument("--jwt-url", default="http://localhost:5000", help="JWT service URL")
    parser.add_argument("--adk-url", default="http://localhost:8100", help="ADK service URL")
    parser.add_argument("--skip-jwt", action="store_true", help="Skip JWT authentication tests")
    args = parser.parse_args()
    
    print("=" * 60)
    print("ADK API Test Script")
    print("=" * 60)
    print(f"JWT Service: {args.jwt_url}")
    print(f"ADK Service: {args.adk_url}")
    
    # Get JWT token
    token = None
    if not args.skip_jwt:
        print("\n--- Getting JWT Token ---")
        token = get_jwt_token(args.jwt_url)
        if token:
            print(f"Got token: {token[:50]}...")
        else:
            print("No token available - some tests will be skipped")
    
    # Run tests
    results = []
    results.append(("Health", test_health(args.adk_url)))
    results.append(("List Agents", test_list_agents(args.adk_url, token)))
    results.append(("List Tools", test_list_tools(args.adk_url, token)))
    results.append(("List MCP Servers", test_list_mcp_servers(args.adk_url, token)))
    results.append(("List Graphs", test_list_graphs(args.adk_url, token)))
    results.append(("Get Tool Schema", test_get_tool_schema(args.adk_url)))
    
    if token:
        results.append(("Create Agent", test_create_agent(args.adk_url, token)))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
