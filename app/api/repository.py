"""
Repository API endpoints for discovering and searching agents, tools, and skills.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.repository import (
    AssetType, AssetMetadata, SearchFilter, SearchRequest,
    SearchResponse, RepositoryStats
)
from ..models.skills import SkillConfig, SkillListResponse
from ..models.auth import AuthenticatedUser
from ..services.repository_service import get_repository_service, RepositoryService
from .dependencies import get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repository", tags=["Repository"])


def get_service() -> RepositoryService:
    """Get the repository service."""
    return get_repository_service()


@router.get("/search", response_model=SearchResponse, summary="Search the repository")
async def search_repository(
    query: Optional[str] = Query(default=None, description="Search query"),
    types: Optional[List[AssetType]] = Query(default=None, description="Filter by asset types"),
    categories: Optional[List[str]] = Query(default=None, description="Filter by categories"),
    tags: Optional[List[str]] = Query(default=None, description="Filter by tags"),
    author: Optional[str] = Query(default=None, description="Filter by author"),
    min_rating: Optional[float] = Query(default=None, ge=0.0, le=5.0),
    sort_by: str = Query(default="relevance", description="Sort by: relevance, rating, usage, created, name"),
    sort_order: str = Query(default="desc", description="Sort order: asc, desc"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: RepositoryService = Depends(get_service)
):
    """Search the repository for agents, tools, skills, and graphs."""
    filters = SearchFilter(
        types=types,
        categories=categories,
        tags=tags,
        author=author,
        min_rating=min_rating
    ) if any([types, categories, tags, author, min_rating]) else None
    
    request = SearchRequest(
        query=query,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    
    return service.search(request)


@router.get("/stats", response_model=RepositoryStats, summary="Get repository statistics")
async def get_repository_stats(
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: RepositoryService = Depends(get_service)
):
    """Get statistics about the repository."""
    return service.get_stats()


@router.get("/categories", response_model=List[str], summary="Get all categories")
async def get_categories(
    type: Optional[AssetType] = Query(default=None, description="Filter by asset type"),
    service: RepositoryService = Depends(get_service)
):
    """Get all categories in the repository."""
    return service.get_categories(type)


@router.get("/tags", response_model=List[str], summary="Get all tags")
async def get_tags(
    type: Optional[AssetType] = Query(default=None, description="Filter by asset type"),
    service: RepositoryService = Depends(get_service)
):
    """Get all tags in the repository."""
    return service.get_tags(type)


@router.get("/assets/{asset_type}/{asset_id}", response_model=AssetMetadata, summary="Get asset by ID")
async def get_asset(
    asset_type: AssetType,
    asset_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: RepositoryService = Depends(get_service)
):
    """Get a specific asset by type and ID."""
    asset = service.get_asset(asset_type, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_type.value}:{asset_id}' not found"
        )
    return asset


@router.get("/skills", response_model=SkillListResponse, summary="List all skills")
async def list_skills(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: RepositoryService = Depends(get_service)
):
    """List all skills in the repository."""
    return service.list_skills(category)


@router.get("/skills/{skill_id}", response_model=SkillConfig, summary="Get skill by ID")
async def get_skill(
    skill_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: RepositoryService = Depends(get_service)
):
    """Get a specific skill by ID."""
    skill = service.get_skill(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found"
        )
    return skill


@router.post("/reload", summary="Reload repository")
async def reload_repository(
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
    service: RepositoryService = Depends(get_service)
):
    """Reload all assets from disk."""
    service.reload()
    return {"success": True, "message": "Repository reloaded"}


@router.get("/agents", response_model=SearchResponse, summary="List all agents")
async def list_agents(
    category: Optional[str] = Query(default=None),
    tags: Optional[List[str]] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: RepositoryService = Depends(get_service)
):
    """List all agents in the repository."""
    filters = SearchFilter(
        types=[AssetType.AGENT],
        categories=[category] if category else None,
        tags=tags
    )
    request = SearchRequest(
        filters=filters,
        sort_by="name",
        sort_order="asc",
        limit=limit,
        offset=offset
    )
    return service.search(request)


@router.get("/tools", response_model=SearchResponse, summary="List all tools")
async def list_tools(
    category: Optional[str] = Query(default=None),
    tags: Optional[List[str]] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: RepositoryService = Depends(get_service)
):
    """List all tools in the repository."""
    filters = SearchFilter(
        types=[AssetType.TOOL],
        categories=[category] if category else None,
        tags=tags
    )
    request = SearchRequest(
        filters=filters,
        sort_by="name",
        sort_order="asc",
        limit=limit,
        offset=offset
    )
    return service.search(request)


@router.get("/graphs", response_model=SearchResponse, summary="List all graphs")
async def list_graphs(
    category: Optional[str] = Query(default=None),
    tags: Optional[List[str]] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: RepositoryService = Depends(get_service)
):
    """List all graphs in the repository."""
    filters = SearchFilter(
        types=[AssetType.GRAPH],
        categories=[category] if category else None,
        tags=tags
    )
    request = SearchRequest(
        filters=filters,
        sort_by="name",
        sort_order="asc",
        limit=limit,
        offset=offset
    )
    return service.search(request)
