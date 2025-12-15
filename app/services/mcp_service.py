"""
MCP Server management service.
"""
import logging
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timezone

from ..config import get_settings
from ..models.mcp_servers import (
    MCPServerConfig, MCPServerResponse, MCPServerListResponse,
    MCPProtocol, MCPServerStatus
)
from ..models.auth import AuthenticatedUser
from .storage import StorageService

logger = logging.getLogger(__name__)


class MCPService:
    """Service for managing MCP server configurations."""
    
    def __init__(self):
        settings = get_settings()
        self.storage = StorageService(
            directory=settings.mcp_servers_dir,
            model_class=MCPServerConfig,
            file_extension="yaml"
        )
        # Track running server status
        self._server_status: Dict[str, MCPServerStatus] = {}
    
    def create_server(
        self,
        config: MCPServerConfig,
        user: Optional[AuthenticatedUser] = None
    ) -> MCPServerResponse:
        """Create a new MCP server configuration."""
        try:
            if self.storage.exists(config.id):
                return MCPServerResponse(
                    success=False,
                    message=f"MCP server with ID '{config.id}' already exists",
                    server=None
                )
            
            now = datetime.now(timezone.utc)
            config.created_at = now
            config.updated_at = now
            if user:
                config.created_by = user.user_id
            
            if self.storage.save(config):
                logger.info(f"Created MCP server '{config.id}'")
                return MCPServerResponse(
                    success=True,
                    message=f"MCP server '{config.name}' created successfully",
                    server=config
                )
            else:
                return MCPServerResponse(
                    success=False,
                    message="Failed to save MCP server configuration",
                    server=None
                )
                
        except Exception as e:
            logger.error(f"Error creating MCP server: {e}")
            return MCPServerResponse(
                success=False,
                message=f"Error creating MCP server: {str(e)}",
                server=None
            )
    
    def get_server(self, server_id: str) -> Optional[MCPServerConfig]:
        """Get an MCP server by ID."""
        return self.storage.load(server_id)
    
    def update_server(
        self,
        server_id: str,
        updates: dict,
        user: Optional[AuthenticatedUser] = None
    ) -> MCPServerResponse:
        """Update an existing MCP server configuration."""
        try:
            existing = self.storage.load(server_id)
            if not existing:
                return MCPServerResponse(
                    success=False,
                    message=f"MCP server '{server_id}' not found",
                    server=None
                )
            
            existing_data = existing.model_dump()
            existing_data.update(updates)
            existing_data["updated_at"] = datetime.now(timezone.utc)
            existing_data["id"] = server_id
            
            updated_server = MCPServerConfig(**existing_data)
            
            if self.storage.save(updated_server):
                logger.info(f"Updated MCP server '{server_id}'")
                return MCPServerResponse(
                    success=True,
                    message=f"MCP server '{server_id}' updated successfully",
                    server=updated_server
                )
            else:
                return MCPServerResponse(
                    success=False,
                    message="Failed to save updated MCP server",
                    server=None
                )
                
        except Exception as e:
            logger.error(f"Error updating MCP server: {e}")
            return MCPServerResponse(
                success=False,
                message=f"Error updating MCP server: {str(e)}",
                server=None
            )
    
    def delete_server(self, server_id: str) -> MCPServerResponse:
        """Delete an MCP server configuration."""
        try:
            existing = self.storage.load(server_id)
            if not existing:
                return MCPServerResponse(
                    success=False,
                    message=f"MCP server '{server_id}' not found",
                    server=None
                )
            
            # Stop server if running
            if server_id in self._server_status:
                del self._server_status[server_id]
            
            if self.storage.delete(server_id):
                logger.info(f"Deleted MCP server '{server_id}'")
                return MCPServerResponse(
                    success=True,
                    message=f"MCP server '{server_id}' deleted successfully",
                    server=existing
                )
            else:
                return MCPServerResponse(
                    success=False,
                    message="Failed to delete MCP server",
                    server=None
                )
                
        except Exception as e:
            logger.error(f"Error deleting MCP server: {e}")
            return MCPServerResponse(
                success=False,
                message=f"Error deleting MCP server: {str(e)}",
                server=None
            )
    
    def list_servers(
        self,
        protocol: Optional[MCPProtocol] = None,
        tags: Optional[List[str]] = None
    ) -> MCPServerListResponse:
        """List all MCP servers with optional filtering."""
        try:
            servers = self.storage.list_all()
            
            if protocol:
                servers = [s for s in servers if s.protocol == protocol]
            
            if tags:
                servers = [s for s in servers if any(tag in s.tags for tag in tags)]
            
            return MCPServerListResponse(
                success=True,
                servers=servers,
                total=len(servers)
            )
            
        except Exception as e:
            logger.error(f"Error listing MCP servers: {e}")
            return MCPServerListResponse(
                success=False,
                servers=[],
                total=0
            )
    
    def get_server_status(self, server_id: str) -> Optional[MCPServerStatus]:
        """Get runtime status of an MCP server."""
        return self._server_status.get(server_id)
    
    def get_all_server_status(self) -> Dict[str, MCPServerStatus]:
        """Get runtime status of all MCP servers."""
        return dict(self._server_status)
    
    def get_server_tools(self, server_id: str) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible tool schemas from MCP server."""
        server = self.storage.load(server_id)
        if not server:
            return []
        
        schemas = []
        for tool in server.tools:
            schema = {
                "type": "function",
                "function": {
                    "name": f"{server_id}_{tool.name}",
                    "description": tool.description or f"MCP tool: {tool.name}",
                    "parameters": tool.input_schema or {"type": "object", "properties": {}}
                }
            }
            schemas.append(schema)
        
        return schemas
    
    def check_user_access(
        self,
        server: MCPServerConfig,
        user: AuthenticatedUser
    ) -> Tuple[bool, Optional[str]]:
        """Check if a user has access to an MCP server."""
        if not server.jwt_required:
            return True, None
        
        if user.is_admin():
            return True, None
        
        if server.allowed_groups and not user.has_any_group(server.allowed_groups):
            return False, f"Required group membership: {server.allowed_groups}"
        
        if server.allowed_roles and not user.has_any_role(server.allowed_roles):
            return False, f"Required role: {server.allowed_roles}"
        
        return True, None


# Singleton
_mcp_service: Optional[MCPService] = None


def get_mcp_service() -> MCPService:
    """Get the MCP service singleton."""
    global _mcp_service
    if _mcp_service is None:
        _mcp_service = MCPService()
    return _mcp_service
