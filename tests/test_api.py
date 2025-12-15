"""
API endpoint tests for the ADK platform.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health and info endpoints."""
    
    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Agent Development Kit (ADK)"
        assert "endpoints" in data
    
    def test_health(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_config(self, client):
        """Test config endpoint."""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "storage_path" in data


class TestAgentsAPI:
    """Tests for agents API endpoints."""
    
    def test_list_agents(self, client):
        """Test listing agents."""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total" in data
    
    def test_get_agent_not_found(self, client):
        """Test getting non-existent agent."""
        response = client.get("/agents/non-existent-agent")
        assert response.status_code == 404


class TestToolsAPI:
    """Tests for tools API endpoints."""
    
    def test_list_tools(self, client):
        """Test listing tools."""
        response = client.get("/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "total" in data
    
    def test_get_tool_not_found(self, client):
        """Test getting non-existent tool."""
        response = client.get("/tools/non-existent-tool")
        assert response.status_code == 404


class TestMCPServersAPI:
    """Tests for MCP servers API endpoints."""
    
    def test_list_mcp_servers(self, client):
        """Test listing MCP servers."""
        response = client.get("/mcp-servers")
        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        assert "total" in data
    
    def test_get_mcp_server_not_found(self, client):
        """Test getting non-existent MCP server."""
        response = client.get("/mcp-servers/non-existent-server")
        assert response.status_code == 404


class TestGraphsAPI:
    """Tests for graphs API endpoints."""
    
    def test_list_graphs(self, client):
        """Test listing graphs."""
        response = client.get("/graphs")
        assert response.status_code == 200
        data = response.json()
        assert "graphs" in data
        assert "total" in data
    
    def test_get_graph_not_found(self, client):
        """Test getting non-existent graph."""
        response = client.get("/graphs/non-existent-graph")
        assert response.status_code == 404


class TestAuthentication:
    """Tests for authentication."""
    
    def test_create_agent_requires_auth(self, client):
        """Test that creating agent requires authentication."""
        response = client.post(
            "/agents",
            json={
                "id": "test-agent",
                "name": "Test Agent",
                "llm": {
                    "provider": "openai",
                    "model": "gpt-4"
                }
            }
        )
        assert response.status_code == 401
    
    def test_create_tool_requires_auth(self, client):
        """Test that creating tool requires authentication."""
        response = client.post(
            "/tools",
            json={
                "id": "test-tool",
                "name": "Test Tool",
                "description": "A test tool"
            }
        )
        assert response.status_code == 401
