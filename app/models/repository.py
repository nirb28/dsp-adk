"""
Repository models for agent/tool/skill discovery and search.
"""
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class AssetType(str, Enum):
    """Types of assets in the repository."""
    AGENT = "agent"
    TOOL = "tool"
    SKILL = "skill"
    GRAPH = "graph"
    ADAPTER = "adapter"


class AssetVisibility(str, Enum):
    """Visibility of assets."""
    PUBLIC = "public"
    PRIVATE = "private"
    ORGANIZATION = "organization"


class AssetMetadata(BaseModel):
    """Common metadata for all repository assets."""
    id: str = Field(..., description="Unique asset identifier")
    type: AssetType = Field(..., description="Asset type")
    name: str = Field(..., description="Asset name")
    description: str = Field(default="", description="Asset description")
    version: str = Field(default="1.0.0")
    
    # Categorization
    category: str = Field(default="general")
    tags: List[str] = Field(default_factory=list)
    
    # Authorship
    author: Optional[str] = Field(default=None)
    organization: Optional[str] = Field(default=None)
    
    # Visibility and access
    visibility: AssetVisibility = Field(default=AssetVisibility.PUBLIC)
    
    # Statistics
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    rating_count: int = Field(default=0)
    usage_count: int = Field(default=0)
    download_count: int = Field(default=0)
    
    # Timestamps
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list, description="IDs of required assets")
    
    # Configuration schema
    config_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema for configuration")
    
    # Documentation
    readme: Optional[str] = Field(default=None, description="Markdown documentation")
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        extra = "allow"


class SearchFilter(BaseModel):
    """Filters for repository search."""
    types: Optional[List[AssetType]] = Field(default=None, description="Filter by asset types")
    categories: Optional[List[str]] = Field(default=None, description="Filter by categories")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    author: Optional[str] = Field(default=None, description="Filter by author")
    organization: Optional[str] = Field(default=None, description="Filter by organization")
    visibility: Optional[AssetVisibility] = Field(default=None)
    min_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    created_after: Optional[datetime] = Field(default=None)
    created_before: Optional[datetime] = Field(default=None)


class SearchRequest(BaseModel):
    """Request for searching the repository."""
    query: Optional[str] = Field(default=None, description="Search query string")
    filters: Optional[SearchFilter] = Field(default=None)
    sort_by: str = Field(default="relevance", description="Sort by: relevance, rating, usage, created, name")
    sort_order: str = Field(default="desc", description="Sort order: asc, desc")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResult(BaseModel):
    """A single search result."""
    asset: AssetMetadata
    score: float = Field(default=0.0, description="Relevance score")
    highlights: Dict[str, List[str]] = Field(default_factory=dict, description="Search highlights")


class SearchResponse(BaseModel):
    """Response for repository search."""
    success: bool = Field(default=True)
    results: List[SearchResult] = Field(default_factory=list)
    total: int = Field(default=0)
    query: Optional[str] = Field(default=None)
    took_ms: float = Field(default=0.0)


class AssetRating(BaseModel):
    """Rating for an asset."""
    asset_id: str
    user_id: str
    rating: float = Field(..., ge=1.0, le=5.0)
    review: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RepositoryStats(BaseModel):
    """Statistics for the repository."""
    total_assets: int = Field(default=0)
    assets_by_type: Dict[str, int] = Field(default_factory=dict)
    assets_by_category: Dict[str, int] = Field(default_factory=dict)
    top_tags: List[Dict[str, Any]] = Field(default_factory=list)
    recent_assets: List[AssetMetadata] = Field(default_factory=list)
    popular_assets: List[AssetMetadata] = Field(default_factory=list)
