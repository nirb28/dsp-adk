"""
Tool management service.
"""
import logging
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timezone

from ..config import get_settings
from ..models.tools import ToolConfig, ToolResponse, ToolListResponse, ToolType
from ..models.auth import AuthenticatedUser
from .storage import StorageService

logger = logging.getLogger(__name__)


class ToolService:
    """Service for managing tool configurations."""
    
    def __init__(self):
        settings = get_settings()
        self.storage = StorageService(
            directory=settings.tools_dir,
            model_class=ToolConfig,
            file_extension="yaml"
        )
    
    def create_tool(
        self,
        config: ToolConfig,
        user: Optional[AuthenticatedUser] = None
    ) -> ToolResponse:
        """Create a new tool configuration."""
        try:
            if self.storage.exists(config.id):
                return ToolResponse(
                    success=False,
                    message=f"Tool with ID '{config.id}' already exists",
                    tool=None
                )
            
            now = datetime.now(timezone.utc)
            config.created_at = now
            config.updated_at = now
            if user:
                config.created_by = user.user_id
            
            if self.storage.save(config):
                logger.info(f"Created tool '{config.id}'")
                return ToolResponse(
                    success=True,
                    message=f"Tool '{config.name}' created successfully",
                    tool=config
                )
            else:
                return ToolResponse(
                    success=False,
                    message="Failed to save tool configuration",
                    tool=None
                )
                
        except Exception as e:
            logger.error(f"Error creating tool: {e}")
            return ToolResponse(
                success=False,
                message=f"Error creating tool: {str(e)}",
                tool=None
            )
    
    def get_tool(self, tool_id: str) -> Optional[ToolConfig]:
        """Get a tool by ID."""
        return self.storage.load(tool_id)
    
    def update_tool(
        self,
        tool_id: str,
        updates: dict,
        user: Optional[AuthenticatedUser] = None
    ) -> ToolResponse:
        """Update an existing tool configuration."""
        try:
            existing = self.storage.load(tool_id)
            if not existing:
                return ToolResponse(
                    success=False,
                    message=f"Tool '{tool_id}' not found",
                    tool=None
                )
            
            existing_data = existing.model_dump()
            existing_data.update(updates)
            existing_data["updated_at"] = datetime.now(timezone.utc)
            existing_data["id"] = tool_id
            
            updated_tool = ToolConfig(**existing_data)
            
            if self.storage.save(updated_tool):
                logger.info(f"Updated tool '{tool_id}'")
                return ToolResponse(
                    success=True,
                    message=f"Tool '{tool_id}' updated successfully",
                    tool=updated_tool
                )
            else:
                return ToolResponse(
                    success=False,
                    message="Failed to save updated tool",
                    tool=None
                )
                
        except Exception as e:
            logger.error(f"Error updating tool: {e}")
            return ToolResponse(
                success=False,
                message=f"Error updating tool: {str(e)}",
                tool=None
            )
    
    def delete_tool(self, tool_id: str) -> ToolResponse:
        """Delete a tool configuration."""
        try:
            existing = self.storage.load(tool_id)
            if not existing:
                return ToolResponse(
                    success=False,
                    message=f"Tool '{tool_id}' not found",
                    tool=None
                )
            
            if self.storage.delete(tool_id):
                logger.info(f"Deleted tool '{tool_id}'")
                return ToolResponse(
                    success=True,
                    message=f"Tool '{tool_id}' deleted successfully",
                    tool=existing
                )
            else:
                return ToolResponse(
                    success=False,
                    message="Failed to delete tool",
                    tool=None
                )
                
        except Exception as e:
            logger.error(f"Error deleting tool: {e}")
            return ToolResponse(
                success=False,
                message=f"Error deleting tool: {str(e)}",
                tool=None
            )
    
    def list_tools(
        self,
        tool_type: Optional[ToolType] = None,
        tags: Optional[List[str]] = None
    ) -> ToolListResponse:
        """List all tools with optional filtering."""
        try:
            tools = self.storage.list_all()
            
            if tool_type:
                tools = [t for t in tools if t.type == tool_type]
            
            if tags:
                tools = [t for t in tools if any(tag in t.tags for tag in tags)]
            
            return ToolListResponse(
                success=True,
                tools=tools,
                total=len(tools)
            )
            
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return ToolListResponse(
                success=False,
                tools=[],
                total=0
            )
    
    def get_tool_schema(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get OpenAI-compatible tool schema for a tool."""
        tool = self.storage.load(tool_id)
        if not tool:
            return None
        
        # Build parameters schema
        properties = {}
        required = []
        
        for param in tool.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description or ""
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": tool.id,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def get_tools_schemas(self, tool_ids: List[str]) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible schemas for multiple tools."""
        schemas = []
        for tool_id in tool_ids:
            schema = self.get_tool_schema(tool_id)
            if schema:
                schemas.append(schema)
        return schemas
    
    def check_user_access(
        self,
        tool: ToolConfig,
        user: AuthenticatedUser
    ) -> Tuple[bool, Optional[str]]:
        """Check if a user has access to a tool."""
        if not tool.jwt_required:
            return True, None
        
        if user.is_admin():
            return True, None
        
        if tool.allowed_groups and not user.has_any_group(tool.allowed_groups):
            return False, f"Required group membership: {tool.allowed_groups}"
        
        if tool.allowed_roles and not user.has_any_role(tool.allowed_roles):
            return False, f"Required role: {tool.allowed_roles}"
        
        return True, None


# Singleton
_tool_service: Optional[ToolService] = None


def get_tool_service() -> ToolService:
    """Get the tool service singleton."""
    global _tool_service
    if _tool_service is None:
        _tool_service = ToolService()
    return _tool_service
