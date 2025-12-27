"""
Manifest Integration Service.

Provides integration with Control Tower manifests for configuration management.
Allows ADK to load agent, tool, and graph configurations from CT manifests.
"""
import logging
import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)


class ManifestModuleConfig(BaseModel):
    """Configuration for a module from a manifest."""
    module_type: str
    name: str
    version: str = "1.0.0"
    status: str = "enabled"
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    cross_references: Dict[str, Any] = Field(default_factory=dict)


class ManifestConfig(BaseModel):
    """Configuration loaded from Control Tower manifest."""
    project_id: str
    project_name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    environment: str = "development"
    modules: List[ManifestModuleConfig] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ManifestIntegrationService:
    """
    Service for integrating with Control Tower manifests.
    
    Provides functionality to:
    - Fetch manifests from Control Tower
    - Extract ADK-specific configurations
    - Apply manifest overrides to local configurations
    - Sync configuration changes back to CT
    """
    
    def __init__(
        self,
        control_tower_url: str = "http://localhost:8000",
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        self.control_tower_url = control_tower_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._cached_manifests: Dict[str, ManifestConfig] = {}
        self._last_sync: Optional[datetime] = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Control Tower API requests."""
        headers = {"Content-Type": "application/json"}
        if self.client_id:
            headers["X-DSPAI-Client-ID"] = self.client_id
        if self.client_secret:
            headers["X-DSPAI-Client-Secret"] = self.client_secret
        return headers
    
    async def fetch_manifest(
        self,
        project_id: str,
        resolve_env: bool = True
    ) -> Optional[ManifestConfig]:
        """
        Fetch a manifest from Control Tower.
        
        Args:
            project_id: The project ID to fetch
            resolve_env: Whether to resolve environment variables
            
        Returns:
            ManifestConfig if found, None otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.control_tower_url}/manifests/{project_id}"
                params = {"resolve_env": str(resolve_env).lower()}
                
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    manifest = ManifestConfig(**data)
                    self._cached_manifests[project_id] = manifest
                    self._last_sync = datetime.utcnow()
                    logger.info(f"Fetched manifest: {project_id}")
                    return manifest
                elif response.status_code == 404:
                    logger.warning(f"Manifest not found: {project_id}")
                    return None
                else:
                    logger.error(f"Failed to fetch manifest: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching manifest {project_id}: {e}")
            return None
    
    async def list_manifests(self) -> List[Dict[str, Any]]:
        """List all available manifests from Control Tower."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.control_tower_url}/manifests",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("manifests", [])
                return []
                
        except Exception as e:
            logger.error(f"Error listing manifests: {e}")
            return []
    
    def get_cached_manifest(self, project_id: str) -> Optional[ManifestConfig]:
        """Get a cached manifest if available."""
        return self._cached_manifests.get(project_id)
    
    def extract_adk_agents(self, manifest: ManifestConfig) -> List[ManifestModuleConfig]:
        """Extract ADK agent modules from a manifest."""
        return [m for m in manifest.modules if m.module_type == "adk_agent"]
    
    def extract_adk_tools(self, manifest: ManifestConfig) -> List[ManifestModuleConfig]:
        """Extract ADK tool modules from a manifest."""
        return [m for m in manifest.modules if m.module_type == "adk_tool"]
    
    def extract_adk_graphs(self, manifest: ManifestConfig) -> List[ManifestModuleConfig]:
        """Extract ADK graph modules from a manifest."""
        return [m for m in manifest.modules if m.module_type == "adk_graph"]
    
    def extract_adk_capabilities(self, manifest: ManifestConfig) -> List[ManifestModuleConfig]:
        """Extract ADK capability modules from a manifest."""
        return [m for m in manifest.modules if m.module_type == "adk_capability"]
    
    def extract_all_adk_modules(self, manifest: ManifestConfig) -> Dict[str, List[ManifestModuleConfig]]:
        """Extract all ADK modules from a manifest, organized by type."""
        return {
            "agents": self.extract_adk_agents(manifest),
            "tools": self.extract_adk_tools(manifest),
            "graphs": self.extract_adk_graphs(manifest),
            "capabilities": self.extract_adk_capabilities(manifest)
        }
    
    def get_module_by_name(
        self,
        manifest: ManifestConfig,
        module_name: str
    ) -> Optional[ManifestModuleConfig]:
        """Get a specific module by name from a manifest."""
        for module in manifest.modules:
            if module.name == module_name:
                return module
        return None
    
    def resolve_cross_references(
        self,
        manifest: ManifestConfig,
        module: ManifestModuleConfig
    ) -> Dict[str, ManifestModuleConfig]:
        """
        Resolve cross-references for a module.
        
        Returns a dict mapping reference name to the referenced module.
        """
        resolved = {}
        for ref_name, ref_config in module.cross_references.items():
            ref_module_name = ref_config.get("module_name")
            if ref_module_name:
                ref_module = self.get_module_by_name(manifest, ref_module_name)
                if ref_module:
                    resolved[ref_name] = ref_module
                elif ref_config.get("required", True):
                    logger.warning(
                        f"Required cross-reference '{ref_name}' -> '{ref_module_name}' "
                        f"not found for module '{module.name}'"
                    )
        return resolved
    
    def build_agent_config_from_manifest(
        self,
        module: ManifestModuleConfig,
        base_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build an agent configuration from a manifest module.
        
        Merges manifest config with optional base config.
        """
        config = base_config.copy() if base_config else {}
        module_config = module.config
        
        # Map manifest fields to agent config fields
        config["id"] = module_config.get("agent_id", module.name)
        config["name"] = module.name
        config["description"] = module.description
        
        # LLM overrides
        if module_config.get("llm_override"):
            config["llm"] = {**config.get("llm", {}), **module_config["llm_override"]}
        
        if module_config.get("system_prompt_override"):
            config.setdefault("llm", {})["system_prompt"] = module_config["system_prompt_override"]
        
        # Tools and capabilities
        config["tools"] = module_config.get("tools", [])
        config["capabilities"] = module_config.get("capabilities", [])
        
        # Memory settings
        if module_config.get("memory_enabled"):
            config["memory"] = {
                "enabled": True,
                "type": module_config.get("memory_type", "session")
            }
        
        return config
    
    def build_tool_config_from_manifest(
        self,
        module: ManifestModuleConfig,
        base_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build a tool configuration from a manifest module."""
        config = base_config.copy() if base_config else {}
        module_config = module.config
        
        config["id"] = module_config.get("tool_id", module.name)
        config["name"] = module.name
        config["description"] = module.description
        config["tool_type"] = module_config.get("tool_type", "function")
        config["timeout"] = module_config.get("timeout", 30)
        config["retry_count"] = module_config.get("retry_count", 0)
        
        # Merge any config overrides
        if module_config.get("config_overrides"):
            config.update(module_config["config_overrides"])
        
        return config
    
    def build_graph_config_from_manifest(
        self,
        module: ManifestModuleConfig,
        base_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build a graph configuration from a manifest module."""
        config = base_config.copy() if base_config else {}
        module_config = module.config
        
        config["id"] = module_config.get("graph_id", module.name)
        config["name"] = module.name
        config["description"] = module.description
        config["type"] = module_config.get("graph_type", "langgraph")
        config["max_iterations"] = module_config.get("max_iterations", 10)
        config["timeout_seconds"] = module_config.get("timeout_seconds", 300)
        config["enable_checkpointing"] = module_config.get("enable_checkpointing", False)
        
        return config
    
    async def sync_from_manifest(
        self,
        project_id: str,
        agent_service: Any = None,
        tool_service: Any = None,
        graph_service: Any = None
    ) -> Dict[str, Any]:
        """
        Sync ADK configurations from a Control Tower manifest.
        
        Creates or updates agents, tools, and graphs based on manifest.
        
        Returns a summary of sync operations.
        """
        manifest = await self.fetch_manifest(project_id)
        if not manifest:
            return {"success": False, "error": f"Manifest not found: {project_id}"}
        
        results = {
            "success": True,
            "project_id": project_id,
            "agents_synced": [],
            "tools_synced": [],
            "graphs_synced": [],
            "errors": []
        }
        
        # Sync agents
        if agent_service:
            for agent_module in self.extract_adk_agents(manifest):
                try:
                    agent_config = self.build_agent_config_from_manifest(agent_module)
                    # Create or update agent
                    results["agents_synced"].append(agent_module.name)
                except Exception as e:
                    results["errors"].append(f"Agent {agent_module.name}: {str(e)}")
        
        # Sync tools
        if tool_service:
            for tool_module in self.extract_adk_tools(manifest):
                try:
                    tool_config = self.build_tool_config_from_manifest(tool_module)
                    results["tools_synced"].append(tool_module.name)
                except Exception as e:
                    results["errors"].append(f"Tool {tool_module.name}: {str(e)}")
        
        # Sync graphs
        if graph_service:
            for graph_module in self.extract_adk_graphs(manifest):
                try:
                    graph_config = self.build_graph_config_from_manifest(graph_module)
                    results["graphs_synced"].append(graph_module.name)
                except Exception as e:
                    results["errors"].append(f"Graph {graph_module.name}: {str(e)}")
        
        if results["errors"]:
            results["success"] = False
        
        return results
    
    def get_service_discovery_info(self, manifest: ManifestConfig) -> Dict[str, Any]:
        """
        Get service discovery information from manifest.
        
        Returns URLs and connection info for related services.
        """
        services = {}
        
        for module in manifest.modules:
            if module.module_type == "jwt_config":
                services["jwt"] = {
                    "name": module.name,
                    "url": module.config.get("service_url"),
                    "enabled": module.status == "enabled"
                }
            elif module.module_type == "rag_service":
                services["rag"] = {
                    "name": module.name,
                    "url": module.config.get("service_url"),
                    "configuration": module.config.get("configuration_name"),
                    "enabled": module.status == "enabled"
                }
            elif module.module_type == "monitoring":
                services["monitoring"] = {
                    "name": module.name,
                    "dashboard_url": module.config.get("dashboard_url"),
                    "enabled": module.status == "enabled"
                }
        
        return services


# Global instance
_manifest_service: Optional[ManifestIntegrationService] = None


def get_manifest_service() -> ManifestIntegrationService:
    """Get the global manifest integration service."""
    global _manifest_service
    if _manifest_service is None:
        _manifest_service = ManifestIntegrationService()
    return _manifest_service


def configure_manifest_service(
    control_tower_url: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
):
    """Configure the global manifest integration service."""
    global _manifest_service
    _manifest_service = ManifestIntegrationService(
        control_tower_url=control_tower_url,
        client_id=client_id,
        client_secret=client_secret
    )
