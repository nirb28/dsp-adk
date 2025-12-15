"""
Graph/Pipeline management API endpoints.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.graphs import (
    GraphConfig, GraphResponse, GraphListResponse, GraphType,
    GraphNode, GraphEdge
)
from ..models.auth import AuthenticatedUser
from ..services.graph_service import get_graph_service, GraphService
from .dependencies import get_current_user, get_optional_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graphs", tags=["Graphs"])


def get_service() -> GraphService:
    """Get the graph service."""
    return get_graph_service()


@router.get("", response_model=GraphListResponse, summary="List all graphs")
async def list_graphs(
    graph_type: Optional[GraphType] = Query(default=None, description="Filter by graph type"),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags to filter by"),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: GraphService = Depends(get_service)
):
    """List all graph configurations with optional filtering."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    response = service.list_graphs(graph_type=graph_type, tags=tag_list)
    
    if user and response.graphs:
        accessible = []
        for graph in response.graphs:
            has_access, _ = service.check_user_access(graph, user)
            if has_access:
                accessible.append(graph)
        response.graphs = accessible
        response.total = len(accessible)
    
    return response


@router.get("/{graph_id}", response_model=GraphResponse, summary="Get graph by ID")
async def get_graph(
    graph_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: GraphService = Depends(get_service)
):
    """Get a specific graph configuration by ID."""
    graph = service.get_graph(graph_id)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph '{graph_id}' not found"
        )
    
    if graph.jwt_required and user:
        has_access, error = service.check_user_access(graph, user)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    elif graph.jwt_required and not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this graph"
        )
    
    return GraphResponse(success=True, message="Graph found", graph=graph)


@router.post("", response_model=GraphResponse, status_code=status.HTTP_201_CREATED, summary="Create graph")
async def create_graph(
    config: GraphConfig,
    user: AuthenticatedUser = Depends(get_current_user),
    service: GraphService = Depends(get_service)
):
    """Create a new graph configuration. Requires authentication."""
    response = service.create_graph(config, user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.put("/{graph_id}", response_model=GraphResponse, summary="Update graph")
async def update_graph(
    graph_id: str,
    updates: dict,
    user: AuthenticatedUser = Depends(get_current_user),
    service: GraphService = Depends(get_service)
):
    """Update an existing graph configuration."""
    existing = service.get_graph(graph_id)
    if existing:
        has_access, error = service.check_user_access(existing, user)
        if not has_access and not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
    
    response = service.update_graph(graph_id, updates, user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.delete("/{graph_id}", response_model=GraphResponse, summary="Delete graph")
async def delete_graph(
    graph_id: str,
    user: AuthenticatedUser = Depends(require_admin),
    service: GraphService = Depends(get_service)
):
    """Delete a graph configuration. Requires administrator access."""
    response = service.delete_graph(graph_id)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response


@router.post("/{graph_id}/nodes", response_model=GraphResponse, summary="Add node to graph")
async def add_node(
    graph_id: str,
    node: GraphNode,
    user: AuthenticatedUser = Depends(get_current_user),
    service: GraphService = Depends(get_service)
):
    """Add a node to an existing graph."""
    response = service.add_node(graph_id, node.model_dump(), user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.post("/{graph_id}/edges", response_model=GraphResponse, summary="Add edge to graph")
async def add_edge(
    graph_id: str,
    edge: GraphEdge,
    user: AuthenticatedUser = Depends(get_current_user),
    service: GraphService = Depends(get_service)
):
    """Add an edge to an existing graph."""
    response = service.add_edge(graph_id, edge.model_dump(), user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.get("/{graph_id}/nodes", response_model=List[GraphNode], summary="Get graph nodes")
async def get_nodes(
    graph_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: GraphService = Depends(get_service)
):
    """Get all nodes in a graph."""
    graph = service.get_graph(graph_id)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph '{graph_id}' not found"
        )
    return graph.nodes


@router.get("/{graph_id}/edges", response_model=List[GraphEdge], summary="Get graph edges")
async def get_edges(
    graph_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: GraphService = Depends(get_service)
):
    """Get all edges in a graph."""
    graph = service.get_graph(graph_id)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph '{graph_id}' not found"
        )
    return graph.edges
