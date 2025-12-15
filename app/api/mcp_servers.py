"""
MCP Server management API endpoints.
"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.mcp_servers import (
    MCPServerConfig, MCPServerResponse, MCPServerListResponse,
    MCPProtocol, MCPServerStatus
)
from ..models.auth import AuthenticatedUser
from ..services.mcp_service import get_mcp_service, MCPService
from .dependencies import get_current_user, get_optional_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp-servers", tags=["MCP Servers"])


def get_service() -> MCPService:
    """Get the MCP service."""
    return get_mcp_service()


@router.get("", response_model=MCPServerListResponse, summary="List all MCP servers")
async def list_servers(
    protocol: Optional[MCPProtocol] = Query(default=None, description="Filter by protocol"),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags to filter by"),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: MCPService = Depends(get_service)
):
    """List all MCP server configurations with optional filtering."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    response = service.list_servers(protocol=protocol, tags=tag_list)
    
    if user and response.servers:
        accessible = []
        for server in response.servers:
            has_access, _ = service.check_user_access(server, user)
            if has_access:
                accessible.append(server)
        response.servers = accessible
        response.total = len(accessible)
    
    return response


@router.get("/status", response_model=Dict[str, MCPServerStatus], summary="Get all server status")
async def get_all_status(
    user: AuthenticatedUser = Depends(get_current_user),
    service: MCPService = Depends(get_service)
):
    """Get runtime status of all MCP servers."""
    return service.get_all_server_status()


@router.get("/{server_id}", response_model=MCPServerResponse, summary="Get MCP server by ID")
async def get_server(
    server_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: MCPService = Depends(get_service)
):
    """Get a specific MCP server configuration by ID."""
    server = service.get_server(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_id}' not found"
        )
    
    if server.jwt_required and user:
        has_access, error = service.check_user_access(server, user)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    elif server.jwt_required and not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this MCP server"
        )
    
    return MCPServerResponse(success=True, message="MCP server found", server=server)


@router.get("/{server_id}/status", response_model=MCPServerStatus, summary="Get server status")
async def get_server_status(
    server_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    service: MCPService = Depends(get_service)
):
    """Get runtime status of an MCP server."""
    server_status = service.get_server_status(server_id)
    if not server_status:
        # Return default status if not tracked
        return MCPServerStatus(
            server_id=server_id,
            running=False,
            connected=False,
            tools_available=0,
            resources_available=0
        )
    return server_status


@router.get("/{server_id}/tools", response_model=List[Dict[str, Any]], summary="Get server tools")
async def get_server_tools(
    server_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: MCPService = Depends(get_service)
):
    """Get OpenAI-compatible tool schemas from an MCP server."""
    server = service.get_server(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_id}' not found"
        )
    
    return service.get_server_tools(server_id)


@router.post("", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED, summary="Create MCP server")
async def create_server(
    config: MCPServerConfig,
    user: AuthenticatedUser = Depends(get_current_user),
    service: MCPService = Depends(get_service)
):
    """Create a new MCP server configuration. Requires authentication."""
    response = service.create_server(config, user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.put("/{server_id}", response_model=MCPServerResponse, summary="Update MCP server")
async def update_server(
    server_id: str,
    updates: dict,
    user: AuthenticatedUser = Depends(get_current_user),
    service: MCPService = Depends(get_service)
):
    """Update an existing MCP server configuration."""
    existing = service.get_server(server_id)
    if existing:
        has_access, error = service.check_user_access(existing, user)
        if not has_access and not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    
    response = service.update_server(server_id, updates, user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.delete("/{server_id}", response_model=MCPServerResponse, summary="Delete MCP server")
async def delete_server(
    server_id: str,
    user: AuthenticatedUser = Depends(require_admin),
    service: MCPService = Depends(get_service)
):
    """Delete an MCP server configuration. Requires administrator access."""
    response = service.delete_server(server_id)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response
