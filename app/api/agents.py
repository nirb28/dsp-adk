"""
Agent management API endpoints.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from ..models.agents import (
    AgentConfig, AgentResponse, AgentListResponse,
    AgentStatus, AgentType, AgentRunRequest, AgentRunResponse
)
from ..models.auth import AuthenticatedUser
from ..services.agent_service import get_agent_service, AgentService
from ..services.agent_executor import get_agent_executor, AgentExecutor, AgentExecutionError
from .dependencies import get_current_user, get_optional_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])


def get_service() -> AgentService:
    """Get the agent service."""
    return get_agent_service()


@router.get("", response_model=AgentListResponse, summary="List all agents")
async def list_agents(
    status: Optional[AgentStatus] = Query(default=None, description="Filter by status"),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags to filter by"),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: AgentService = Depends(get_service)
):
    """
    List all agent configurations with optional filtering.
    Public endpoint, but returns only accessible agents for authenticated users.
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    response = service.list_agents(status=status, tags=tag_list)
    
    # Filter by user access if authenticated
    if user and response.agents:
        accessible = []
        for agent in response.agents:
            has_access, _ = service.check_user_access(agent, user)
            if has_access:
                accessible.append(agent)
        response.agents = accessible
        response.total = len(accessible)
    
    return response


@router.get("/{agent_id}", response_model=AgentResponse, summary="Get agent by ID")
async def get_agent(
    agent_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: AgentService = Depends(get_service)
):
    """Get a specific agent configuration by ID."""
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    # Check access if JWT required
    if agent.jwt_required and user:
        has_access, error = service.check_user_access(agent, user)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    elif agent.jwt_required and not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this agent"
        )
    
    return AgentResponse(success=True, message="Agent found", agent=agent)


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED, summary="Create agent")
async def create_agent(
    config: AgentConfig,
    user: AuthenticatedUser = Depends(get_current_user),
    service: AgentService = Depends(get_service)
):
    """
    Create a new agent configuration.
    Requires authentication.
    """
    response = service.create_agent(config, user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.put("/{agent_id}", response_model=AgentResponse, summary="Update agent")
async def update_agent(
    agent_id: str,
    updates: dict,
    user: AuthenticatedUser = Depends(get_current_user),
    service: AgentService = Depends(get_service)
):
    """
    Update an existing agent configuration.
    Requires authentication and access to the agent.
    """
    # Check existing agent access
    existing = service.get_agent(agent_id)
    if existing:
        has_access, error = service.check_user_access(existing, user)
        if not has_access and not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    
    response = service.update_agent(agent_id, updates, user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.delete("/{agent_id}", response_model=AgentResponse, summary="Delete agent")
async def delete_agent(
    agent_id: str,
    user: AuthenticatedUser = Depends(require_admin),
    service: AgentService = Depends(get_service)
):
    """
    Delete an agent configuration.
    Requires administrator access.
    """
    response = service.delete_agent(agent_id)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response


@router.post("/{agent_id}/tools/{tool_id}", response_model=AgentResponse, summary="Add tool to agent")
async def add_tool_to_agent(
    agent_id: str,
    tool_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    service: AgentService = Depends(get_service)
):
    """Add a tool to an agent's configuration."""
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    if tool_id not in agent.tools:
        agent.tools.append(tool_id)
        response = service.update_agent(agent_id, {"tools": agent.tools}, user)
        return response
    
    return AgentResponse(success=True, message="Tool already assigned", agent=agent)


@router.delete("/{agent_id}/tools/{tool_id}", response_model=AgentResponse, summary="Remove tool from agent")
async def remove_tool_from_agent(
    agent_id: str,
    tool_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    service: AgentService = Depends(get_service)
):
    """Remove a tool from an agent's configuration."""
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    if tool_id in agent.tools:
        agent.tools.remove(tool_id)
        response = service.update_agent(agent_id, {"tools": agent.tools}, user)
        return response
    
    return AgentResponse(success=True, message="Tool not assigned", agent=agent)


@router.post("/{agent_id}/mcp-servers/{server_id}", response_model=AgentResponse, summary="Add MCP server to agent")
async def add_mcp_server_to_agent(
    agent_id: str,
    server_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    service: AgentService = Depends(get_service)
):
    """Add an MCP server to an agent's configuration."""
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    if server_id not in agent.mcp_servers:
        agent.mcp_servers.append(server_id)
        response = service.update_agent(agent_id, {"mcp_servers": agent.mcp_servers}, user)
        return response
    
    return AgentResponse(success=True, message="MCP server already assigned", agent=agent)


@router.delete("/{agent_id}/mcp-servers/{server_id}", response_model=AgentResponse, summary="Remove MCP server from agent")
async def remove_mcp_server_from_agent(
    agent_id: str,
    server_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    service: AgentService = Depends(get_service)
):
    """Remove an MCP server from an agent's configuration."""
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    if server_id in agent.mcp_servers:
        agent.mcp_servers.remove(server_id)
        response = service.update_agent(agent_id, {"mcp_servers": agent.mcp_servers}, user)
        return response
    
    return AgentResponse(success=True, message="MCP server not assigned", agent=agent)


@router.post("/{agent_id}/run", response_model=AgentRunResponse, summary="Run agent")
async def run_agent(
    agent_id: str,
    request: AgentRunRequest,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: AgentService = Depends(get_service)
):
    """
    Execute an agent with a message and get a response.
    Supports optional context and conversation history.
    """
    # Get agent
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    # Check access
    if agent.jwt_required and user:
        has_access, error = service.check_user_access(agent, user)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    elif agent.jwt_required and not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this agent"
        )
    
    # Execute agent
    executor = get_agent_executor()
    try:
        kwargs = {}
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        if getattr(request, "session_id", None):
            kwargs["session_id"] = request.session_id
        
        result = await executor.run(
            agent=agent,
            message=request.message,
            context=request.context,
            history=request.history,
            user=user,
            use_tools=request.use_tools,
            max_tool_iterations=request.max_tool_iterations,
            mock_tools=request.mock_tools,
            **kwargs
        )
        
        return AgentRunResponse(**result)
        
    except AgentExecutionError as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{agent_id}/stream", summary="Stream agent response")
async def stream_agent(
    agent_id: str,
    request: AgentRunRequest,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: AgentService = Depends(get_service)
):
    """
    Execute an agent with streaming response.
    Returns Server-Sent Events (SSE) stream.
    """
    # Get agent
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    # Check access
    if agent.jwt_required and user:
        has_access, error = service.check_user_access(agent, user)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    elif agent.jwt_required and not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this agent"
        )
    
    # Stream agent response
    executor = get_agent_executor()
    
    async def generate():
        try:
            kwargs = {}
            if request.temperature is not None:
                kwargs["temperature"] = request.temperature
            if request.max_tokens is not None:
                kwargs["max_tokens"] = request.max_tokens
            if getattr(request, "session_id", None):
                kwargs["session_id"] = request.session_id
            
            async for chunk in executor.stream(
                agent=agent,
                message=request.message,
                context=request.context,
                history=request.history,
                user=user,
                **kwargs
            ):
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except AgentExecutionError as e:
            logger.error(f"Agent streaming error: {e}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
