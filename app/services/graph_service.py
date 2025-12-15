"""
Graph/Pipeline management service.
Supports LangGraph and extensible pipeline technologies.
"""
import logging
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timezone

from ..config import get_settings
from ..models.graphs import (
    GraphConfig, GraphResponse, GraphListResponse, GraphType,
    GraphExecutionRequest, GraphExecutionResponse
)
from ..models.auth import AuthenticatedUser
from .storage import StorageService

logger = logging.getLogger(__name__)


class GraphService:
    """Service for managing graph/pipeline configurations."""
    
    def __init__(self):
        settings = get_settings()
        self.storage = StorageService(
            directory=settings.graphs_dir,
            model_class=GraphConfig,
            file_extension="yaml"
        )
    
    def create_graph(
        self,
        config: GraphConfig,
        user: Optional[AuthenticatedUser] = None
    ) -> GraphResponse:
        """Create a new graph configuration."""
        try:
            if self.storage.exists(config.id):
                return GraphResponse(
                    success=False,
                    message=f"Graph with ID '{config.id}' already exists",
                    graph=None
                )
            
            # Validate graph structure
            validation_error = self._validate_graph(config)
            if validation_error:
                return GraphResponse(
                    success=False,
                    message=validation_error,
                    graph=None
                )
            
            now = datetime.now(timezone.utc)
            config.created_at = now
            config.updated_at = now
            if user:
                config.created_by = user.user_id
            
            if self.storage.save(config):
                logger.info(f"Created graph '{config.id}'")
                return GraphResponse(
                    success=True,
                    message=f"Graph '{config.name}' created successfully",
                    graph=config
                )
            else:
                return GraphResponse(
                    success=False,
                    message="Failed to save graph configuration",
                    graph=None
                )
                
        except Exception as e:
            logger.error(f"Error creating graph: {e}")
            return GraphResponse(
                success=False,
                message=f"Error creating graph: {str(e)}",
                graph=None
            )
    
    def _validate_graph(self, config: GraphConfig) -> Optional[str]:
        """Validate graph structure."""
        if not config.nodes:
            return "Graph must have at least one node"
        
        node_ids = {node.id for node in config.nodes}
        
        # Check entry point
        if config.entry_point and config.entry_point not in node_ids:
            return f"Entry point '{config.entry_point}' not found in nodes"
        
        # Check edges reference valid nodes
        for edge in config.edges:
            if edge.source not in node_ids:
                return f"Edge source '{edge.source}' not found in nodes"
            if edge.target not in node_ids:
                return f"Edge target '{edge.target}' not found in nodes"
        
        return None
    
    def get_graph(self, graph_id: str) -> Optional[GraphConfig]:
        """Get a graph by ID."""
        return self.storage.load(graph_id)
    
    def update_graph(
        self,
        graph_id: str,
        updates: dict,
        user: Optional[AuthenticatedUser] = None
    ) -> GraphResponse:
        """Update an existing graph configuration."""
        try:
            existing = self.storage.load(graph_id)
            if not existing:
                return GraphResponse(
                    success=False,
                    message=f"Graph '{graph_id}' not found",
                    graph=None
                )
            
            existing_data = existing.model_dump()
            existing_data.update(updates)
            existing_data["updated_at"] = datetime.now(timezone.utc)
            existing_data["id"] = graph_id
            
            updated_graph = GraphConfig(**existing_data)
            
            # Validate updated graph
            validation_error = self._validate_graph(updated_graph)
            if validation_error:
                return GraphResponse(
                    success=False,
                    message=validation_error,
                    graph=None
                )
            
            if self.storage.save(updated_graph):
                logger.info(f"Updated graph '{graph_id}'")
                return GraphResponse(
                    success=True,
                    message=f"Graph '{graph_id}' updated successfully",
                    graph=updated_graph
                )
            else:
                return GraphResponse(
                    success=False,
                    message="Failed to save updated graph",
                    graph=None
                )
                
        except Exception as e:
            logger.error(f"Error updating graph: {e}")
            return GraphResponse(
                success=False,
                message=f"Error updating graph: {str(e)}",
                graph=None
            )
    
    def delete_graph(self, graph_id: str) -> GraphResponse:
        """Delete a graph configuration."""
        try:
            existing = self.storage.load(graph_id)
            if not existing:
                return GraphResponse(
                    success=False,
                    message=f"Graph '{graph_id}' not found",
                    graph=None
                )
            
            if self.storage.delete(graph_id):
                logger.info(f"Deleted graph '{graph_id}'")
                return GraphResponse(
                    success=True,
                    message=f"Graph '{graph_id}' deleted successfully",
                    graph=existing
                )
            else:
                return GraphResponse(
                    success=False,
                    message="Failed to delete graph",
                    graph=None
                )
                
        except Exception as e:
            logger.error(f"Error deleting graph: {e}")
            return GraphResponse(
                success=False,
                message=f"Error deleting graph: {str(e)}",
                graph=None
            )
    
    def list_graphs(
        self,
        graph_type: Optional[GraphType] = None,
        tags: Optional[List[str]] = None
    ) -> GraphListResponse:
        """List all graphs with optional filtering."""
        try:
            graphs = self.storage.list_all()
            
            if graph_type:
                graphs = [g for g in graphs if g.type == graph_type]
            
            if tags:
                graphs = [g for g in graphs if any(tag in g.tags for tag in tags)]
            
            return GraphListResponse(
                success=True,
                graphs=graphs,
                total=len(graphs)
            )
            
        except Exception as e:
            logger.error(f"Error listing graphs: {e}")
            return GraphListResponse(
                success=False,
                graphs=[],
                total=0
            )
    
    def add_node(
        self,
        graph_id: str,
        node: dict,
        user: Optional[AuthenticatedUser] = None
    ) -> GraphResponse:
        """Add a node to an existing graph."""
        graph = self.storage.load(graph_id)
        if not graph:
            return GraphResponse(
                success=False,
                message=f"Graph '{graph_id}' not found",
                graph=None
            )
        
        from ..models.graphs import GraphNode
        new_node = GraphNode(**node)
        
        # Check for duplicate node ID
        if any(n.id == new_node.id for n in graph.nodes):
            return GraphResponse(
                success=False,
                message=f"Node with ID '{new_node.id}' already exists",
                graph=None
            )
        
        graph.nodes.append(new_node)
        graph.updated_at = datetime.now(timezone.utc)
        
        if self.storage.save(graph):
            return GraphResponse(
                success=True,
                message=f"Node '{new_node.id}' added to graph",
                graph=graph
            )
        return GraphResponse(
            success=False,
            message="Failed to save graph",
            graph=None
        )
    
    def add_edge(
        self,
        graph_id: str,
        edge: dict,
        user: Optional[AuthenticatedUser] = None
    ) -> GraphResponse:
        """Add an edge to an existing graph."""
        graph = self.storage.load(graph_id)
        if not graph:
            return GraphResponse(
                success=False,
                message=f"Graph '{graph_id}' not found",
                graph=None
            )
        
        from ..models.graphs import GraphEdge
        new_edge = GraphEdge(**edge)
        
        # Validate source and target exist
        node_ids = {n.id for n in graph.nodes}
        if new_edge.source not in node_ids:
            return GraphResponse(
                success=False,
                message=f"Source node '{new_edge.source}' not found",
                graph=None
            )
        if new_edge.target not in node_ids:
            return GraphResponse(
                success=False,
                message=f"Target node '{new_edge.target}' not found",
                graph=None
            )
        
        graph.edges.append(new_edge)
        graph.updated_at = datetime.now(timezone.utc)
        
        if self.storage.save(graph):
            return GraphResponse(
                success=True,
                message=f"Edge '{new_edge.id}' added to graph",
                graph=graph
            )
        return GraphResponse(
            success=False,
            message="Failed to save graph",
            graph=None
        )
    
    def check_user_access(
        self,
        graph: GraphConfig,
        user: AuthenticatedUser
    ) -> Tuple[bool, Optional[str]]:
        """Check if a user has access to a graph."""
        if not graph.jwt_required:
            return True, None
        
        if user.is_admin():
            return True, None
        
        if graph.allowed_groups and not user.has_any_group(graph.allowed_groups):
            return False, f"Required group membership: {graph.allowed_groups}"
        
        if graph.allowed_roles and not user.has_any_role(graph.allowed_roles):
            return False, f"Required role: {graph.allowed_roles}"
        
        return True, None


# Singleton
_graph_service: Optional[GraphService] = None


def get_graph_service() -> GraphService:
    """Get the graph service singleton."""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service
