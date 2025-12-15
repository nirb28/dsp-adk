"""
Adapter management API endpoints.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.adapters import (
    AdapterConfig, AdapterResponse, AdapterListResponse, AdapterType
)
from ..models.auth import AuthenticatedUser
from ..services.adapter_service import get_adapter_service, AdapterService
from .dependencies import get_current_user, get_optional_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/adapters", tags=["Adapters"])


def get_service() -> AdapterService:
    """Get the adapter service."""
    return get_adapter_service()


@router.get("", response_model=AdapterListResponse, summary="List all adapters")
async def list_adapters(
    adapter_type: Optional[AdapterType] = Query(default=None, description="Filter by adapter type"),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags to filter by"),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: AdapterService = Depends(get_service)
):
    """List all adapter configurations with optional filtering."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    return service.list_adapters(adapter_type=adapter_type, tags=tag_list)


@router.get("/types", response_model=List[str], summary="Get available adapter types")
async def get_adapter_types():
    """Get list of available adapter types."""
    return [t.value for t in AdapterType]


@router.get("/{adapter_id}", response_model=AdapterResponse, summary="Get adapter by ID")
async def get_adapter(
    adapter_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: AdapterService = Depends(get_service)
):
    """Get a specific adapter configuration by ID."""
    adapter = service.get_adapter(adapter_id)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adapter '{adapter_id}' not found"
        )
    return AdapterResponse(success=True, message="Adapter found", adapter=adapter)


@router.post("", response_model=AdapterResponse, status_code=status.HTTP_201_CREATED, summary="Create adapter")
async def create_adapter(
    config: AdapterConfig,
    user: AuthenticatedUser = Depends(get_current_user),
    service: AdapterService = Depends(get_service)
):
    """Create a new adapter configuration. Requires authentication."""
    response = service.create_adapter(config, user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.put("/{adapter_id}", response_model=AdapterResponse, summary="Update adapter")
async def update_adapter(
    adapter_id: str,
    updates: dict,
    user: AuthenticatedUser = Depends(get_current_user),
    service: AdapterService = Depends(get_service)
):
    """Update an existing adapter configuration."""
    response = service.update_adapter(adapter_id, updates, user)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    return response


@router.delete("/{adapter_id}", response_model=AdapterResponse, summary="Delete adapter")
async def delete_adapter(
    adapter_id: str,
    user: AuthenticatedUser = Depends(require_admin),
    service: AdapterService = Depends(get_service)
):
    """Delete an adapter configuration. Requires administrator access."""
    response = service.delete_adapter(adapter_id)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    return response


@router.get("/type/{adapter_type}", response_model=AdapterListResponse, summary="Get adapters by type")
async def get_adapters_by_type(
    adapter_type: AdapterType,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: AdapterService = Depends(get_service)
):
    """Get all adapters of a specific type."""
    adapters = service.get_adapters_by_type(adapter_type)
    return AdapterListResponse(
        success=True,
        adapters=adapters,
        total=len(adapters)
    )
