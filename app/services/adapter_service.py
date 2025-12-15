"""
Adapter management service.
"""
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timezone

from ..config import get_settings
from ..models.adapters import (
    AdapterConfig, AdapterResponse, AdapterListResponse, AdapterType
)
from ..models.auth import AuthenticatedUser
from .storage import StorageService

logger = logging.getLogger(__name__)


class AdapterService:
    """Service for managing adapter configurations."""
    
    def __init__(self):
        settings = get_settings()
        # Store adapters in a dedicated directory
        adapters_dir = f"{settings.storage_path}/adapters"
        self.storage = StorageService(
            directory=adapters_dir,
            model_class=AdapterConfig,
            file_extension="yaml"
        )
    
    def create_adapter(
        self,
        config: AdapterConfig,
        user: Optional[AuthenticatedUser] = None
    ) -> AdapterResponse:
        """Create a new adapter configuration."""
        try:
            if self.storage.exists(config.id):
                return AdapterResponse(
                    success=False,
                    message=f"Adapter with ID '{config.id}' already exists",
                    adapter=None
                )
            
            # Validate type-specific config is provided
            validation_error = self._validate_adapter_config(config)
            if validation_error:
                return AdapterResponse(
                    success=False,
                    message=validation_error,
                    adapter=None
                )
            
            now = datetime.now(timezone.utc)
            config.created_at = now
            config.updated_at = now
            if user:
                config.created_by = user.user_id
            
            if self.storage.save(config):
                logger.info(f"Created adapter '{config.id}' of type {config.type}")
                return AdapterResponse(
                    success=True,
                    message=f"Adapter '{config.name}' created successfully",
                    adapter=config
                )
            else:
                return AdapterResponse(
                    success=False,
                    message="Failed to save adapter configuration",
                    adapter=None
                )
                
        except Exception as e:
            logger.error(f"Error creating adapter: {e}")
            return AdapterResponse(
                success=False,
                message=f"Error creating adapter: {str(e)}",
                adapter=None
            )
    
    def _validate_adapter_config(self, config: AdapterConfig) -> Optional[str]:
        """Validate that the adapter has appropriate type-specific config."""
        type_config_map = {
            AdapterType.SECURITY: config.security,
            AdapterType.OBSERVABILITY: config.observability,
            AdapterType.CACHING: config.caching,
            AdapterType.RATE_LIMITING: config.rate_limiting,
            AdapterType.RETRY: config.retry,
            AdapterType.TRANSFORMATION: config.transformation,
            AdapterType.VALIDATION: config.validation,
            AdapterType.CUSTOM: config.custom,
        }
        
        # Logging type doesn't need special config (uses observability.logging)
        if config.type == AdapterType.LOGGING:
            if config.observability and config.observability.logging:
                return None
            return "Logging adapter requires observability.logging configuration"
        
        expected_config = type_config_map.get(config.type)
        if config.type != AdapterType.CUSTOM and expected_config is None:
            return f"Adapter type '{config.type}' requires corresponding configuration"
        
        return None
    
    def get_adapter(self, adapter_id: str) -> Optional[AdapterConfig]:
        """Get an adapter by ID."""
        return self.storage.load(adapter_id)
    
    def update_adapter(
        self,
        adapter_id: str,
        updates: dict,
        user: Optional[AuthenticatedUser] = None
    ) -> AdapterResponse:
        """Update an existing adapter configuration."""
        try:
            existing = self.storage.load(adapter_id)
            if not existing:
                return AdapterResponse(
                    success=False,
                    message=f"Adapter '{adapter_id}' not found",
                    adapter=None
                )
            
            existing_data = existing.model_dump()
            existing_data.update(updates)
            existing_data["updated_at"] = datetime.now(timezone.utc)
            existing_data["id"] = adapter_id
            
            updated_adapter = AdapterConfig(**existing_data)
            
            # Validate updated config
            validation_error = self._validate_adapter_config(updated_adapter)
            if validation_error:
                return AdapterResponse(
                    success=False,
                    message=validation_error,
                    adapter=None
                )
            
            if self.storage.save(updated_adapter):
                logger.info(f"Updated adapter '{adapter_id}'")
                return AdapterResponse(
                    success=True,
                    message=f"Adapter '{adapter_id}' updated successfully",
                    adapter=updated_adapter
                )
            else:
                return AdapterResponse(
                    success=False,
                    message="Failed to save updated adapter",
                    adapter=None
                )
                
        except Exception as e:
            logger.error(f"Error updating adapter: {e}")
            return AdapterResponse(
                success=False,
                message=f"Error updating adapter: {str(e)}",
                adapter=None
            )
    
    def delete_adapter(self, adapter_id: str) -> AdapterResponse:
        """Delete an adapter configuration."""
        try:
            existing = self.storage.load(adapter_id)
            if not existing:
                return AdapterResponse(
                    success=False,
                    message=f"Adapter '{adapter_id}' not found",
                    adapter=None
                )
            
            if self.storage.delete(adapter_id):
                logger.info(f"Deleted adapter '{adapter_id}'")
                return AdapterResponse(
                    success=True,
                    message=f"Adapter '{adapter_id}' deleted successfully",
                    adapter=existing
                )
            else:
                return AdapterResponse(
                    success=False,
                    message="Failed to delete adapter",
                    adapter=None
                )
                
        except Exception as e:
            logger.error(f"Error deleting adapter: {e}")
            return AdapterResponse(
                success=False,
                message=f"Error deleting adapter: {str(e)}",
                adapter=None
            )
    
    def list_adapters(
        self,
        adapter_type: Optional[AdapterType] = None,
        tags: Optional[List[str]] = None
    ) -> AdapterListResponse:
        """List all adapters with optional filtering."""
        try:
            adapters = self.storage.list_all()
            
            if adapter_type:
                adapters = [a for a in adapters if a.type == adapter_type]
            
            if tags:
                adapters = [a for a in adapters if any(tag in a.tags for tag in tags)]
            
            return AdapterListResponse(
                success=True,
                adapters=adapters,
                total=len(adapters)
            )
            
        except Exception as e:
            logger.error(f"Error listing adapters: {e}")
            return AdapterListResponse(
                success=False,
                adapters=[],
                total=0
            )
    
    def get_adapters_by_type(self, adapter_type: AdapterType) -> List[AdapterConfig]:
        """Get all adapters of a specific type."""
        adapters = self.storage.list_all()
        return [a for a in adapters if a.type == adapter_type]
    
    def get_enabled_adapters(self) -> List[AdapterConfig]:
        """Get all enabled adapters."""
        adapters = self.storage.list_all()
        return [a for a in adapters if a.enabled]


# Singleton
_adapter_service: Optional[AdapterService] = None


def get_adapter_service() -> AdapterService:
    """Get the adapter service singleton."""
    global _adapter_service
    if _adapter_service is None:
        _adapter_service = AdapterService()
    return _adapter_service
