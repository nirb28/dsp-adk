"""
Agent management service.
"""
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timezone

from ..config import get_settings
from ..models.agents import AgentConfig, AgentResponse, AgentListResponse, AgentStatus
from ..models.auth import AuthenticatedUser
from .storage import StorageService

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing agent configurations."""
    
    def __init__(self):
        settings = get_settings()
        self.storage = StorageService(
            directory=settings.agents_dir,
            model_class=AgentConfig,
            file_extension="yaml"
        )
        self.verbose_logging = settings.verbose_logging
    
    def create_agent(
        self,
        config: AgentConfig,
        user: Optional[AuthenticatedUser] = None
    ) -> AgentResponse:
        """Create a new agent configuration."""
        try:
            logger.debug(f"[AGENT_CREATE] Creating agent: {config.id}, type={config.agent_type}")
            # Check if agent already exists
            if self.storage.exists(config.id):
                logger.warning(f"[AGENT_CREATE] Agent '{config.id}' already exists")
                return AgentResponse(
                    success=False,
                    message=f"Agent with ID '{config.id}' already exists",
                    agent=None
                )
            
            # Set timestamps and creator
            now = datetime.now(timezone.utc)
            config.created_at = now
            config.updated_at = now
            if user:
                config.created_by = user.user_id
            
            # Save agent
            if self.storage.save(config):
                logger.info(f"[AGENT_CREATE] Created agent '{config.id}' by {user.user_id if user else 'system'}")
                return AgentResponse(
                    success=True,
                    message=f"Agent '{config.name}' created successfully",
                    agent=config
                )
            else:
                return AgentResponse(
                    success=False,
                    message="Failed to save agent configuration",
                    agent=None
                )
                
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return AgentResponse(
                success=False,
                message=f"Error creating agent: {str(e)}",
                agent=None
            )
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get an agent by ID."""
        logger.debug(f"[AGENT_LOAD] Loading agent: {agent_id}")
        agent = self.storage.load(agent_id)
        if agent:
            logger.debug(f"[AGENT_LOAD] Agent '{agent_id}' loaded: type={agent.agent_type}, status={agent.status}, tools={len(agent.tools) if agent.tools else 0}")
            if self.verbose_logging:
                logger.info(f"[AGENT_LOAD:VERBOSE] Full agent config: {agent.model_dump_json(indent=2)}")
        else:
            logger.warning(f"[AGENT_LOAD] Agent '{agent_id}' not found")
        return agent
    
    def update_agent(
        self,
        agent_id: str,
        updates: dict,
        user: Optional[AuthenticatedUser] = None
    ) -> AgentResponse:
        """Update an existing agent configuration."""
        try:
            existing = self.storage.load(agent_id)
            if not existing:
                return AgentResponse(
                    success=False,
                    message=f"Agent '{agent_id}' not found",
                    agent=None
                )
            
            # Apply updates
            existing_data = existing.model_dump()
            existing_data.update(updates)
            existing_data["updated_at"] = datetime.now(timezone.utc)
            existing_data["id"] = agent_id  # Preserve ID
            
            updated_agent = AgentConfig(**existing_data)
            
            if self.storage.save(updated_agent):
                logger.info(f"Updated agent '{agent_id}' by {user.user_id if user else 'system'}")
                return AgentResponse(
                    success=True,
                    message=f"Agent '{agent_id}' updated successfully",
                    agent=updated_agent
                )
            else:
                return AgentResponse(
                    success=False,
                    message="Failed to save updated agent",
                    agent=None
                )
                
        except Exception as e:
            logger.error(f"Error updating agent: {e}")
            return AgentResponse(
                success=False,
                message=f"Error updating agent: {str(e)}",
                agent=None
            )
    
    def delete_agent(self, agent_id: str) -> AgentResponse:
        """Delete an agent configuration."""
        try:
            existing = self.storage.load(agent_id)
            if not existing:
                return AgentResponse(
                    success=False,
                    message=f"Agent '{agent_id}' not found",
                    agent=None
                )
            
            if self.storage.delete(agent_id):
                logger.info(f"Deleted agent '{agent_id}'")
                return AgentResponse(
                    success=True,
                    message=f"Agent '{agent_id}' deleted successfully",
                    agent=existing
                )
            else:
                return AgentResponse(
                    success=False,
                    message="Failed to delete agent",
                    agent=None
                )
                
        except Exception as e:
            logger.error(f"Error deleting agent: {e}")
            return AgentResponse(
                success=False,
                message=f"Error deleting agent: {str(e)}",
                agent=None
            )
    
    def list_agents(
        self,
        status: Optional[AgentStatus] = None,
        tags: Optional[List[str]] = None
    ) -> AgentListResponse:
        """List all agents with optional filtering."""
        try:
            logger.debug(f"[AGENT_LIST] Listing agents: status={status}, tags={tags}")
            all_agents = self.storage.list_all()
            logger.debug(f"[AGENT_LIST] Loaded {len(all_agents)} agents from storage")
            
            # Apply filters
            filtered_agents = all_agents
            if status:
                filtered_agents = [a for a in filtered_agents if a.status == status]
                logger.debug(f"[AGENT_LIST] After status filter: {len(filtered_agents)} agents")
            if tags:
                filtered_agents = [
                    a for a in filtered_agents
                    if any(tag in a.tags for tag in tags)
                ]
                logger.debug(f"[AGENT_LIST] After tag filter: {len(filtered_agents)} agents")
            
            return AgentListResponse(
                success=True,
                agents=filtered_agents,
                total=len(filtered_agents)
            )
            
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return AgentListResponse(
                success=False,
                agents=[],
                total=0
            )
    
    def get_agents_by_tool(self, tool_id: str) -> List[AgentConfig]:
        """Get all agents that use a specific tool."""
        agents = self.storage.list_all()
        return [a for a in agents if tool_id in a.tools]
    
    def get_agents_by_mcp_server(self, server_id: str) -> List[AgentConfig]:
        """Get all agents that use a specific MCP server."""
        agents = self.storage.list_all()
        return [a for a in agents if server_id in a.mcp_servers]
    
    def get_agents_by_graph(self, graph_id: str) -> List[AgentConfig]:
        """Get all agents that use a specific graph."""
        agents = self.storage.list_all()
        return [a for a in agents if a.graph_id == graph_id]
    
    def check_user_access(
        self,
        agent: AgentConfig,
        user: AuthenticatedUser
    ) -> Tuple[bool, Optional[str]]:
        """Check if user has access to an agent."""
        logger.debug(f"[AGENT_ACCESS] Checking access for user '{user.user_id}' to agent '{agent.id}'")
        if not agent.jwt_required:
            logger.debug(f"[AGENT_ACCESS] Agent '{agent.id}' does not require JWT, access granted")
            return True, None
        
        if user.is_admin():
            return True, None
        
        # Check groups
        if agent.allowed_groups and not user.has_any_group(agent.allowed_groups):
            return False, f"Required group membership: {agent.allowed_groups}"
        
        # Check roles
        if agent.allowed_roles and not user.has_any_role(agent.allowed_roles):
            return False, f"Required role: {agent.allowed_roles}"
        
        return True, None


# Singleton instance
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get the agent service singleton."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
