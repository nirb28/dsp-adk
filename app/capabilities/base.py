"""
Base classes for the capability system.

Capabilities are runtime services that provide cross-cutting functionality
like sessions, memory, streaming, guardrails, etc.

This module integrates with app.core.base for standardized component patterns.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Type
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.base import (
    ADKComponent, ADKComponentConfig, ComponentType, ComponentStatus,
    LifecycleMixin, ValidationMixin, ObservabilityMixin
)

logger = logging.getLogger(__name__)


class CapabilityStatus(str, Enum):
    """Status of a capability."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    INITIALIZING = "initializing"


class CapabilityConfig(BaseModel):
    """Base configuration for capabilities."""
    enabled: bool = Field(default=True, description="Whether the capability is enabled")
    
    class Config:
        extra = "allow"


class Capability(ABC, LifecycleMixin, ValidationMixin, ObservabilityMixin):
    """
    Base class for all capabilities.
    
    Capabilities are runtime services that provide cross-cutting functionality.
    They integrate with the ADK's standardized component patterns through mixins.
    
    Lifecycle: disabled -> initializing -> enabled -> (error) -> shutdown
    
    Example:
        class MyCapability(Capability):
            name = "my_capability"
            version = "1.0.0"
            
            async def _do_initialize(self):
                # Setup resources
                pass
            
            async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
                # Main capability logic
                pass
    """
    
    # Class-level attributes (override in subclass)
    name: str = "base"
    version: str = "1.0.0"
    description: str = "Base capability"
    component_type: ComponentType = ComponentType.CAPABILITY
    
    def __init__(self, config: Optional[CapabilityConfig] = None):
        self.config = config or CapabilityConfig()
        self._cap_status = CapabilityStatus.DISABLED
        self._initialized_at: Optional[datetime] = None
        self._shutdown_at: Optional[datetime] = None
        self._error: Optional[str] = None
        self._error_count: int = 0
        
        # Initialize mixins
        self._validation_errors = []
        self._validation_warnings = []
        self._metrics = {}
    
    @property
    def status(self) -> CapabilityStatus:
        return self._cap_status
    
    @property
    def is_enabled(self) -> bool:
        return self._cap_status == CapabilityStatus.ENABLED
    
    @property
    def is_ready(self) -> bool:
        return self._cap_status == CapabilityStatus.ENABLED
    
    async def initialize(self) -> bool:
        """Initialize the capability."""
        if not self.config.enabled:
            self._cap_status = CapabilityStatus.DISABLED
            return False
        
        try:
            self._cap_status = CapabilityStatus.INITIALIZING
            self._error = None
            await self._do_initialize()
            self._cap_status = CapabilityStatus.ENABLED
            self._initialized_at = datetime.utcnow()
            self.increment_counter("initializations")
            logger.info(f"Capability '{self.name}' initialized successfully")
            return True
        except Exception as e:
            self._cap_status = CapabilityStatus.ERROR
            self._error = str(e)
            self._error_count += 1
            self.increment_counter("initialization_failures")
            logger.error(f"Failed to initialize capability '{self.name}': {e}")
            return False
    
    async def _do_initialize(self):
        """Actual initialization logic. Override in subclasses."""
        pass
    
    async def shutdown(self):
        """Shutdown the capability."""
        try:
            await self._do_shutdown()
            self._cap_status = CapabilityStatus.DISABLED
            self._shutdown_at = datetime.utcnow()
            logger.info(f"Capability '{self.name}' shut down")
        except Exception as e:
            self._error = str(e)
            logger.error(f"Error shutting down capability '{self.name}': {e}")
    
    async def _do_shutdown(self):
        """Actual shutdown logic. Override in subclasses."""
        pass
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the capability's main function.
        Override in subclasses for specific behavior.
        """
        return {"status": "not_implemented"}
    
    def get_info(self) -> Dict[str, Any]:
        """Get capability information."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "component_type": self.component_type.value,
            "status": self._cap_status.value,
            "enabled": self.config.enabled,
            "initialized_at": self._initialized_at.isoformat() if self._initialized_at else None,
            "shutdown_at": self._shutdown_at.isoformat() if self._shutdown_at else None,
            "error": self._error,
            "error_count": self._error_count
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get capability health status."""
        return {
            "name": self.name,
            "status": self._cap_status.value,
            "healthy": self._cap_status == CapabilityStatus.ENABLED,
            "error": self._error,
            "error_count": self._error_count,
            "uptime_seconds": (
                (datetime.utcnow() - self._initialized_at).total_seconds()
                if self._initialized_at else 0
            )
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} status={self._cap_status.value}>"


class CapabilityRegistry:
    """Registry for managing capabilities."""
    
    def __init__(self):
        self._capabilities: Dict[str, Capability] = {}
        self._capability_classes: Dict[str, Type[Capability]] = {}
    
    def register_class(self, capability_class: Type[Capability]):
        """Register a capability class."""
        self._capability_classes[capability_class.name] = capability_class
        logger.info(f"Registered capability class: {capability_class.name}")
    
    def register(self, capability: Capability) -> bool:
        """Register a capability instance."""
        if capability.name in self._capabilities:
            logger.warning(f"Capability {capability.name} already registered, replacing")
        self._capabilities[capability.name] = capability
        logger.info(f"Registered capability: {capability.name}")
        return True
    
    def unregister(self, name: str) -> bool:
        """Unregister a capability."""
        if name in self._capabilities:
            del self._capabilities[name]
            return True
        return False
    
    def create(self, name: str, config: Optional[CapabilityConfig] = None) -> Optional[Capability]:
        """Create a capability instance from a registered class."""
        if name not in self._capability_classes:
            logger.error(f"Unknown capability class: {name}")
            return None
        
        capability = self._capability_classes[name](config)
        self._capabilities[name] = capability
        return capability
    
    def get(self, name: str) -> Optional[Capability]:
        """Get a capability by name."""
        return self._capabilities.get(name)
    
    def list_capabilities(self) -> Dict[str, Capability]:
        """Get all registered capabilities."""
        return self._capabilities.copy()
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all capabilities and their status."""
        return [cap.get_info() for cap in self._capabilities.values()]
    
    def list_available(self) -> List[str]:
        """List available capability classes."""
        return list(self._capability_classes.keys())
    
    async def initialize_all(self):
        """Initialize all registered capabilities."""
        for name, capability in self._capabilities.items():
            await capability.initialize()
    
    async def shutdown_all(self):
        """Shutdown all capabilities."""
        for name, capability in self._capabilities.items():
            await capability.shutdown()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        by_status = {}
        for cap in self._capabilities.values():
            status = cap.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_capabilities": len(self._capabilities),
            "by_status": by_status,
            "registered_classes": list(self._capability_classes.keys())
        }


# Global registry
_registry: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:
    """Get the global capability registry."""
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry
