"""
Tool management API endpoints.
"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from pydantic import BaseModel, Field

from ..models.tools import (
    ToolConfig, ToolResponse, ToolListResponse, ToolType
)
from ..models.auth import AuthenticatedUser
from ..services.tool_service import get_tool_service, ToolService
from ..services.agent_executor import AgentExecutor
from .dependencies import get_current_user, get_optional_user, require_admin

logger = logging.getLogger(__name__)


class ToolExecuteRequest(BaseModel):
    """Request model for tool execution."""
    arguments: Dict[str, Any] = Field(..., description="Tool arguments")
    mock: bool = Field(default=False, description="Use mock execution instead of real execution")


class ToolExecuteResponse(BaseModel):
    """Response model for tool execution."""
    success: bool
    tool_id: str
    result: Dict[str, Any]
    error: Optional[str] = None

router = APIRouter(prefix="/tools", tags=["Tools"])


def get_service() -> ToolService:
    """Get the tool service."""
    return get_tool_service()


@router.get("", response_model=ToolListResponse, summary="List all tools")
async def list_tools(
    tool_type: Optional[ToolType] = Query(default=None, description="Filter by tool type"),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags to filter by"),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: ToolService = Depends(get_service)
):
    """List all tool configurations with optional filtering."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    response = service.list_tools(tool_type=tool_type, tags=tag_list)
    
    # Filter by user access if authenticated
    if user and response.tools:
        accessible = []
        for tool in response.tools:
            has_access, _ = service.check_user_access(tool, user)
            if has_access:
                accessible.append(tool)
        response.tools = accessible
        response.total = len(accessible)
    
    return response


@router.get("/schemas", response_model=List[Dict[str, Any]], summary="Get tool schemas")
async def get_tool_schemas(
    tool_ids: str = Query(..., description="Comma-separated tool IDs"),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: ToolService = Depends(get_service)
):
    """Get OpenAI-compatible tool schemas for specified tools."""
    ids = [t.strip() for t in tool_ids.split(",")]
    return service.get_tools_schemas(ids)


@router.get("/{tool_id}", response_model=ToolResponse, summary="Get tool by ID")
async def get_tool(
    tool_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: ToolService = Depends(get_service)
):
    """Get a specific tool configuration by ID."""
    tool = service.get_tool(tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_id}' not found"
        )
    
    if tool.jwt_required and user:
        has_access, error = service.check_user_access(tool, user)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    elif tool.jwt_required and not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this tool"
        )
    
    return ToolResponse(success=True, message="Tool found", tool=tool)


@router.get("/{tool_id}/schema", response_model=Dict[str, Any], summary="Get tool schema")
async def get_tool_schema(
    tool_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: ToolService = Depends(get_service)
):
    """Get OpenAI-compatible tool schema for a specific tool."""
    schema = service.get_tool_schema(tool_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_id}' not found"
        )
    return schema


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED, summary="Create tool")
async def create_tool(
    config: ToolConfig,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: ToolService = Depends(get_service)
):
    """Create a new tool configuration. Authentication optional."""
    response = service.create_tool(config, user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.put("/{tool_id}", response_model=ToolResponse, summary="Update tool")
async def update_tool(
    tool_id: str,
    updates: dict,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: ToolService = Depends(get_service)
):
    """Update an existing tool configuration. Authentication optional."""
    existing = service.get_tool(tool_id)
    if existing and user:
        has_access, error = service.check_user_access(existing, user)
        if not has_access and not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    
    response = service.update_tool(tool_id, updates, user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.delete("/{tool_id}", response_model=ToolResponse, summary="Delete tool")
async def delete_tool(
    tool_id: str,
    user: AuthenticatedUser = Depends(require_admin),
    service: ToolService = Depends(get_service)
):
    """Delete a tool configuration. Requires administrator access."""
    response = service.delete_tool(tool_id)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response


@router.post("/{tool_id}/execute", response_model=ToolExecuteResponse, summary="Execute tool")
async def execute_tool(
    tool_id: str,
    request: ToolExecuteRequest,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: ToolService = Depends(get_service)
):
    """
    Execute a tool with given arguments.
    
    This endpoint allows direct tool execution for testing and debugging.
    The tool will be executed with the provided arguments and return the result.
    
    Args:
        tool_id: ID of the tool to execute
        request: Tool execution request with arguments and mock flag
        user: Optional authenticated user (required if tool has jwt_required=true)
        
    Returns:
        Tool execution result or error
    """
    import json
    
    # Get tool configuration
    tool = service.get_tool(tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_id}' not found"
        )
    
    # Check authentication if required
    if tool.jwt_required and not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this tool"
        )
    
    if tool.jwt_required and user:
        has_access, error = service.check_user_access(tool, user)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    
    # Execute tool
    try:
        executor = AgentExecutor()
        result_json_str = await executor._execute_tool(tool, request.arguments, mock=request.mock)
        result_data = json.loads(result_json_str)
        
        # Check if result contains an error
        if isinstance(result_data, dict) and "error" in result_data:
            return ToolExecuteResponse(
                success=False,
                tool_id=tool_id,
                result=result_data,
                error=result_data["error"]
            )
        
        return ToolExecuteResponse(
            success=True,
            tool_id=tool_id,
            result=result_data,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error executing tool '{tool_id}': {e}", exc_info=True)
        return ToolExecuteResponse(
            success=False,
            tool_id=tool_id,
            result={},
            error=str(e)
        )
