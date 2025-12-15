"""
API routes for the ADK platform.
"""
from .agents import router as agents_router
from .tools import router as tools_router
from .mcp_servers import router as mcp_servers_router
from .graphs import router as graphs_router
from .adapters import router as adapters_router
from .telemetry import router as telemetry_router
from .repository import router as repository_router

__all__ = [
    "agents_router",
    "tools_router",
    "mcp_servers_router",
    "graphs_router",
    "adapters_router",
    "telemetry_router",
    "repository_router",
]
