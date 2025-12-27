"""
ADK Core Base Classes.

Provides unified base classes and interfaces for all ADK components
including agents, tools, skills, capabilities, graphs, and adapters.

This establishes standardization across the platform for:
- Lifecycle management (initialize, validate, execute, shutdown)
- Metadata and versioning
- Security and access control
- Observability (logging, metrics, tracing)
- Configuration validation
"""
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Type, TypeVar, Generic, Callable, Set
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='ADKComponentConfig')


class ComponentType(str, Enum):
    """Types of ADK components."""
    AGENT = "agent"
    TOOL = "tool"
    SKILL = "skill"
    CAPABILITY = "capability"
    GRAPH = "graph"
    ADAPTER = "adapter"
    MCP_SERVER = "mcp_server"
    WORKFLOW = "workflow"
    PLUGIN = "plugin"


class ComponentStatus(str, Enum):
    """Lifecycle status of a component."""
    DRAFT = "draft"
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"
    ARCHIVED = "archived"


class ADKComponentConfig(BaseModel):
    """
    Base configuration for all ADK components.
    
    All component configurations (AgentConfig, ToolConfig, etc.) should
    inherit from this class to ensure consistent metadata and validation.
    """
    # Identity
    id: str = Field(..., description="Unique component identifier")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(default=None, description="Component description")
    
    # Type and Version
    component_type: ComponentType = Field(..., description="Type of component")
    version: str = Field(default="1.0.0", description="Semantic version")
    
    # Status
    enabled: bool = Field(default=True, description="Whether component is enabled")
    status: ComponentStatus = Field(default=ComponentStatus.DRAFT)
    
    # Categorization
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    category: Optional[str] = Field(default=None, description="Category/group")
    
    # Security
    jwt_required: bool = Field(default=True, description="Require JWT authentication")
    allowed_groups: List[str] = Field(default_factory=list, description="Allowed JWT groups")
    allowed_roles: List[str] = Field(default_factory=list, description="Allowed JWT roles")
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list, description="Component dependencies")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator user ID")
    
    class Config:
        extra = "allow"
        use_enum_values = True
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate component ID format."""
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        # Allow alphanumeric, hyphens, underscores
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("ID must be alphanumeric with hyphens/underscores only")
        return v
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)
    
    def set_created(self, user_id: Optional[str] = None):
        """Set creation metadata."""
        now = datetime.now(timezone.utc)
        self.created_at = now
        self.updated_at = now
        if user_id:
            self.created_by = user_id


class LifecycleMixin:
    """
    Mixin providing standard lifecycle management.
    
    Lifecycle: draft -> initializing -> ready -> active -> shutdown
    """
    
    _status: ComponentStatus = ComponentStatus.DRAFT
    _initialized_at: Optional[datetime] = None
    _shutdown_at: Optional[datetime] = None
    _error: Optional[str] = None
    _error_count: int = 0
    
    @property
    def status(self) -> ComponentStatus:
        return self._status
    
    @property
    def is_ready(self) -> bool:
        return self._status in (ComponentStatus.READY, ComponentStatus.ACTIVE)
    
    @property
    def is_active(self) -> bool:
        return self._status == ComponentStatus.ACTIVE
    
    @property
    def last_error(self) -> Optional[str]:
        return self._error
    
    async def initialize(self) -> bool:
        """
        Initialize the component.
        
        Returns True if successful, False otherwise.
        """
        if self._status == ComponentStatus.ACTIVE:
            return True
        
        try:
            self._status = ComponentStatus.INITIALIZING
            self._error = None
            
            await self._on_initialize()
            
            self._status = ComponentStatus.READY
            self._initialized_at = datetime.now(timezone.utc)
            logger.info(f"Component initialized: {getattr(self, 'name', 'unknown')}")
            return True
            
        except Exception as e:
            self._status = ComponentStatus.ERROR
            self._error = str(e)
            self._error_count += 1
            logger.error(f"Failed to initialize component: {e}")
            return False
    
    async def _on_initialize(self):
        """Override in subclass for custom initialization."""
        pass
    
    async def activate(self) -> bool:
        """Activate the component for use."""
        if self._status != ComponentStatus.READY:
            if not await self.initialize():
                return False
        
        try:
            await self._on_activate()
            self._status = ComponentStatus.ACTIVE
            return True
        except Exception as e:
            self._error = str(e)
            self._error_count += 1
            return False
    
    async def _on_activate(self):
        """Override in subclass for custom activation."""
        pass
    
    async def pause(self):
        """Pause the component."""
        if self._status == ComponentStatus.ACTIVE:
            await self._on_pause()
            self._status = ComponentStatus.PAUSED
    
    async def _on_pause(self):
        """Override in subclass for custom pause handling."""
        pass
    
    async def resume(self):
        """Resume a paused component."""
        if self._status == ComponentStatus.PAUSED:
            await self._on_resume()
            self._status = ComponentStatus.ACTIVE
    
    async def _on_resume(self):
        """Override in subclass for custom resume handling."""
        pass
    
    async def shutdown(self):
        """Shutdown the component."""
        try:
            await self._on_shutdown()
            self._status = ComponentStatus.SHUTDOWN
            self._shutdown_at = datetime.now(timezone.utc)
            logger.info(f"Component shutdown: {getattr(self, 'name', 'unknown')}")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self._error = str(e)
    
    async def _on_shutdown(self):
        """Override in subclass for custom shutdown."""
        pass
    
    async def reset(self):
        """Reset component to initial state."""
        await self.shutdown()
        self._status = ComponentStatus.DRAFT
        self._error = None
        self._error_count = 0
        await self._on_reset()
    
    async def _on_reset(self):
        """Override in subclass for custom reset handling."""
        pass


class ValidationMixin:
    """
    Mixin providing validation capabilities.
    """
    
    _validation_errors: List[str] = []
    _validation_warnings: List[str] = []
    
    def validate(self) -> bool:
        """
        Validate the component configuration.
        
        Returns True if valid, False otherwise.
        """
        self._validation_errors = []
        self._validation_warnings = []
        
        try:
            self._do_validate()
            return len(self._validation_errors) == 0
        except Exception as e:
            self._validation_errors.append(str(e))
            return False
    
    def _do_validate(self):
        """Override in subclass to add custom validation."""
        pass
    
    def add_validation_error(self, error: str):
        """Add a validation error."""
        self._validation_errors.append(error)
    
    def add_validation_warning(self, warning: str):
        """Add a validation warning."""
        self._validation_warnings.append(warning)
    
    @property
    def validation_errors(self) -> List[str]:
        return self._validation_errors.copy()
    
    @property
    def validation_warnings(self) -> List[str]:
        return self._validation_warnings.copy()
    
    @property
    def is_valid(self) -> bool:
        return len(self._validation_errors) == 0


class SecurityMixin:
    """
    Mixin providing security and access control.
    """
    
    def check_access(
        self,
        user_id: Optional[str] = None,
        groups: Optional[List[str]] = None,
        roles: Optional[List[str]] = None,
        is_admin: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Check if access is allowed.
        
        Returns (allowed, reason) tuple.
        """
        config = getattr(self, 'config', None)
        if not config:
            return True, None
        
        # Check if JWT is required
        if not getattr(config, 'jwt_required', True):
            return True, None
        
        # Admins always have access
        if is_admin:
            return True, None
        
        # Check groups
        allowed_groups = getattr(config, 'allowed_groups', [])
        if allowed_groups:
            groups = groups or []
            if not any(g in allowed_groups for g in groups):
                return False, f"Required group: {allowed_groups}"
        
        # Check roles
        allowed_roles = getattr(config, 'allowed_roles', [])
        if allowed_roles:
            roles = roles or []
            if not any(r in allowed_roles for r in roles):
                return False, f"Required role: {allowed_roles}"
        
        return True, None
    
    def has_permission(self, permission: str, user_permissions: List[str]) -> bool:
        """Check if a specific permission is granted."""
        return permission in user_permissions


class ObservabilityMixin:
    """
    Mixin providing observability (logging, metrics, tracing).
    """
    
    _metrics: Dict[str, Any] = {}
    _trace_id: Optional[str] = None
    _span_id: Optional[str] = None
    
    def set_trace_context(self, trace_id: str, span_id: Optional[str] = None):
        """Set tracing context."""
        self._trace_id = trace_id
        self._span_id = span_id or str(uuid.uuid4())[:8]
    
    def get_trace_context(self) -> Dict[str, Optional[str]]:
        """Get current trace context."""
        return {
            "trace_id": self._trace_id,
            "span_id": self._span_id
        }
    
    def record_metric(self, name: str, value: Any, tags: Optional[Dict[str, str]] = None):
        """Record a metric value."""
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append({
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tags": tags or {}
        })
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric."""
        if name not in self._metrics:
            self._metrics[name] = 0
        self._metrics[name] += value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all recorded metrics."""
        return self._metrics.copy()
    
    def clear_metrics(self):
        """Clear all metrics."""
        self._metrics = {}
    
    def log(self, level: str, message: str, **kwargs):
        """Log with component context."""
        extra = {
            "component": getattr(self, 'name', 'unknown'),
            "component_type": getattr(self, 'component_type', 'unknown'),
            "trace_id": self._trace_id,
            **kwargs
        }
        log_fn = getattr(logger, level.lower(), logger.info)
        log_fn(message, extra=extra)


class ADKComponent(ABC, LifecycleMixin, ValidationMixin, SecurityMixin, ObservabilityMixin):
    """
    Base class for all ADK components.
    
    All agents, tools, skills, capabilities, graphs, and adapters should
    inherit from this class to ensure consistent behavior.
    
    Example:
        class MyAgent(ADKComponent):
            component_type = ComponentType.AGENT
            
            def __init__(self, config: MyAgentConfig):
                super().__init__(config)
            
            async def _on_initialize(self):
                # Custom initialization
                pass
            
            async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                # Main execution logic
                pass
    """
    
    # Class-level attributes (override in subclass)
    component_type: ComponentType = ComponentType.PLUGIN
    
    def __init__(self, config: ADKComponentConfig):
        """Initialize with configuration."""
        self.config = config
        self._id = config.id
        self._name = config.name
        self._version = config.version
        
        # Initialize mixins
        self._status = ComponentStatus.DRAFT
        self._validation_errors = []
        self._validation_warnings = []
        self._metrics = {}
        self._error_count = 0
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the component's main function.
        
        Args:
            input_data: Input parameters for execution
            
        Returns:
            Execution result as a dictionary
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get component information."""
        return {
            "id": self._id,
            "name": self._name,
            "type": self.component_type.value,
            "version": self._version,
            "status": self._status.value,
            "enabled": self.config.enabled,
            "description": self.config.description,
            "tags": self.config.tags,
            "category": self.config.category,
            "initialized_at": self._initialized_at.isoformat() if self._initialized_at else None,
            "error": self._error,
            "error_count": self._error_count
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get component health status."""
        return {
            "id": self._id,
            "status": self._status.value,
            "healthy": self._status in (ComponentStatus.READY, ComponentStatus.ACTIVE),
            "error": self._error,
            "error_count": self._error_count,
            "uptime_seconds": (
                (datetime.now(timezone.utc) - self._initialized_at).total_seconds()
                if self._initialized_at else 0
            )
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary."""
        return {
            "config": self.config.model_dump(),
            "info": self.get_info(),
            "health": self.get_health()
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self._id} status={self._status.value}>"


class ComponentRegistry:
    """
    Registry for managing ADK components.
    
    Provides centralized registration, discovery, and lifecycle management
    for all component types.
    """
    
    def __init__(self):
        self._components: Dict[str, ADKComponent] = {}
        self._component_classes: Dict[str, Type[ADKComponent]] = {}
        self._by_type: Dict[ComponentType, Set[str]] = {t: set() for t in ComponentType}
        self._hooks: Dict[str, List[Callable]] = {
            "pre_register": [],
            "post_register": [],
            "pre_initialize": [],
            "post_initialize": [],
            "pre_shutdown": [],
            "post_shutdown": [],
        }
    
    def register_class(self, component_class: Type[ADKComponent], name: Optional[str] = None):
        """Register a component class for later instantiation."""
        key = name or component_class.__name__
        self._component_classes[key] = component_class
        logger.info(f"Registered component class: {key}")
    
    def register(self, component: ADKComponent) -> bool:
        """Register a component instance."""
        for hook in self._hooks["pre_register"]:
            hook(component)
        
        if component.id in self._components:
            logger.warning(f"Component {component.id} already registered, replacing")
        
        self._components[component.id] = component
        self._by_type[component.component_type].add(component.id)
        
        for hook in self._hooks["post_register"]:
            hook(component)
        
        logger.info(f"Registered component: {component.id} ({component.component_type.value})")
        return True
    
    def unregister(self, component_id: str) -> bool:
        """Unregister a component."""
        if component_id not in self._components:
            return False
        
        component = self._components[component_id]
        self._by_type[component.component_type].discard(component_id)
        del self._components[component_id]
        
        logger.info(f"Unregistered component: {component_id}")
        return True
    
    def get(self, component_id: str) -> Optional[ADKComponent]:
        """Get a component by ID."""
        return self._components.get(component_id)
    
    def get_by_type(self, component_type: ComponentType) -> List[ADKComponent]:
        """Get all components of a specific type."""
        return [
            self._components[cid] 
            for cid in self._by_type.get(component_type, set())
            if cid in self._components
        ]
    
    def list_all(self) -> Dict[str, ADKComponent]:
        """List all registered components."""
        return self._components.copy()
    
    def list_ids(self, component_type: Optional[ComponentType] = None) -> List[str]:
        """List component IDs, optionally filtered by type."""
        if component_type:
            return list(self._by_type.get(component_type, set()))
        return list(self._components.keys())
    
    def create(
        self,
        class_name: str,
        config: ADKComponentConfig,
        auto_register: bool = True
    ) -> Optional[ADKComponent]:
        """Create a component from a registered class."""
        if class_name not in self._component_classes:
            logger.error(f"Unknown component class: {class_name}")
            return None
        
        component = self._component_classes[class_name](config)
        
        if auto_register:
            self.register(component)
        
        return component
    
    async def initialize_all(self, component_type: Optional[ComponentType] = None):
        """Initialize all registered components."""
        for hook in self._hooks["pre_initialize"]:
            hook()
        
        components = (
            self.get_by_type(component_type)
            if component_type
            else list(self._components.values())
        )
        
        for component in components:
            await component.initialize()
        
        for hook in self._hooks["post_initialize"]:
            hook()
    
    async def shutdown_all(self, component_type: Optional[ComponentType] = None):
        """Shutdown all registered components."""
        for hook in self._hooks["pre_shutdown"]:
            hook()
        
        components = (
            self.get_by_type(component_type)
            if component_type
            else list(self._components.values())
        )
        
        for component in components:
            await component.shutdown()
        
        for hook in self._hooks["post_shutdown"]:
            hook()
    
    def add_hook(self, event: str, callback: Callable):
        """Add a lifecycle hook."""
        if event in self._hooks:
            self._hooks[event].append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        by_status = {}
        for component in self._components.values():
            status = component.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_components": len(self._components),
            "by_type": {t.value: len(ids) for t, ids in self._by_type.items() if ids},
            "by_status": by_status,
            "registered_classes": list(self._component_classes.keys())
        }


# Global registry instance
_global_registry: Optional[ComponentRegistry] = None


def get_component_registry() -> ComponentRegistry:
    """Get the global component registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ComponentRegistry()
    return _global_registry
