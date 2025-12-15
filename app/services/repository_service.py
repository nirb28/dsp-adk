"""
Repository service for discovering, searching, and managing agents, tools, and skills.
"""
import logging
import os
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

import yaml

from ..config import get_settings
from ..models.repository import (
    AssetType, AssetVisibility, AssetMetadata, SearchFilter,
    SearchRequest, SearchResult, SearchResponse, RepositoryStats
)
from ..models.skills import SkillConfig, SkillListResponse

logger = logging.getLogger(__name__)


class RepositoryService:
    """Service for managing the agent/tool/skill repository."""
    
    def __init__(self):
        self.settings = get_settings()
        self._assets: Dict[str, AssetMetadata] = {}
        self._skills: Dict[str, SkillConfig] = {}
        self._loaded = False
    
    def _ensure_loaded(self):
        """Ensure assets are loaded from disk."""
        if not self._loaded:
            self._load_all_assets()
            self._loaded = True
    
    def _load_all_assets(self):
        """Load all assets from the data directories."""
        base_path = Path(self.settings.storage_path)
        
        # Load agents
        self._load_assets_from_dir(base_path / "agents", AssetType.AGENT)
        
        # Load tools
        self._load_assets_from_dir(base_path / "tools", AssetType.TOOL)
        
        # Load skills
        self._load_skills_from_dir(base_path / "skills")
        
        # Load graphs
        self._load_assets_from_dir(base_path / "graphs", AssetType.GRAPH)
        
        # Load adapters
        self._load_assets_from_dir(base_path / "adapters", AssetType.ADAPTER)
        
        logger.info(f"Loaded {len(self._assets)} assets and {len(self._skills)} skills")
    
    def _load_assets_from_dir(self, directory: Path, asset_type: AssetType):
        """Load assets from a directory recursively."""
        if not directory.exists():
            return
        
        for file_path in directory.rglob("*.yaml"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if not data or 'id' not in data:
                    continue
                
                # Create asset metadata
                asset = AssetMetadata(
                    id=data['id'],
                    type=asset_type,
                    name=data.get('name', data['id']),
                    description=data.get('description', ''),
                    version=data.get('version', data.get('metadata', {}).get('version', '1.0.0')),
                    category=data.get('category', 'general'),
                    tags=data.get('tags', []),
                    author=data.get('metadata', {}).get('author'),
                    visibility=AssetVisibility.PUBLIC,
                    rating=data.get('metadata', {}).get('rating', 0.0),
                    usage_count=data.get('metadata', {}).get('usage_count', 0),
                    dependencies=self._extract_dependencies(data, asset_type),
                    config_schema=data.get('config_schema', {}),
                    readme=data.get('readme'),
                    examples=data.get('examples', [])
                )
                
                # Store with type prefix to avoid ID collisions
                key = f"{asset_type.value}:{asset.id}"
                self._assets[key] = asset
                
            except Exception as e:
                logger.warning(f"Failed to load asset from {file_path}: {e}")
    
    def _load_skills_from_dir(self, directory: Path):
        """Load skills from the skills directory."""
        if not directory.exists():
            os.makedirs(directory, exist_ok=True)
            return
        
        for file_path in directory.rglob("*.yaml"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if not data or 'id' not in data:
                    continue
                
                skill = SkillConfig(**data)
                self._skills[skill.id] = skill
                
                # Also add to assets
                asset = AssetMetadata(
                    id=skill.id,
                    type=AssetType.SKILL,
                    name=skill.name,
                    description=skill.description,
                    version=skill.version,
                    category=skill.category.value if skill.category else 'custom',
                    tags=skill.tags,
                    author=skill.author,
                    visibility=AssetVisibility.PUBLIC,
                    rating=skill.rating,
                    usage_count=skill.usage_count,
                    dependencies=skill.required_tools,
                    examples=[{"input": e.get("input", ""), "output": e.get("output", "")} for e in skill.examples]
                )
                self._assets[f"skill:{skill.id}"] = asset
                
            except Exception as e:
                logger.warning(f"Failed to load skill from {file_path}: {e}")
    
    def _extract_dependencies(self, data: Dict, asset_type: AssetType) -> List[str]:
        """Extract dependencies from asset data."""
        deps = []
        
        if asset_type == AssetType.AGENT:
            deps.extend(data.get('tools', []))
            deps.extend(data.get('skills', []))
            deps.extend(data.get('mcp_servers', []))
        elif asset_type == AssetType.GRAPH:
            deps.extend(data.get('agents', []))
            deps.extend(data.get('tools', []))
        
        return deps
    
    def search(self, request: SearchRequest) -> SearchResponse:
        """Search the repository."""
        self._ensure_loaded()
        
        start_time = datetime.utcnow()
        results: List[SearchResult] = []
        
        for key, asset in self._assets.items():
            # Apply filters
            if request.filters:
                if not self._matches_filters(asset, request.filters):
                    continue
            
            # Calculate relevance score
            score = 0.0
            highlights: Dict[str, List[str]] = {}
            
            if request.query:
                score, highlights = self._calculate_relevance(asset, request.query)
                if score == 0:
                    continue
            else:
                score = 1.0
            
            results.append(SearchResult(
                asset=asset,
                score=score,
                highlights=highlights
            ))
        
        # Sort results
        results = self._sort_results(results, request.sort_by, request.sort_order)
        
        total = len(results)
        results = results[request.offset:request.offset + request.limit]
        
        took_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return SearchResponse(
            success=True,
            results=results,
            total=total,
            query=request.query,
            took_ms=took_ms
        )
    
    def _matches_filters(self, asset: AssetMetadata, filters: SearchFilter) -> bool:
        """Check if asset matches filters."""
        if filters.types and asset.type not in filters.types:
            return False
        if filters.categories and asset.category not in filters.categories:
            return False
        if filters.tags and not any(tag in asset.tags for tag in filters.tags):
            return False
        if filters.author and asset.author != filters.author:
            return False
        if filters.organization and asset.organization != filters.organization:
            return False
        if filters.visibility and asset.visibility != filters.visibility:
            return False
        if filters.min_rating and asset.rating < filters.min_rating:
            return False
        if filters.created_after and asset.created_at and asset.created_at < filters.created_after:
            return False
        if filters.created_before and asset.created_at and asset.created_at > filters.created_before:
            return False
        return True
    
    def _calculate_relevance(self, asset: AssetMetadata, query: str) -> tuple:
        """Calculate relevance score and highlights for a query."""
        score = 0.0
        highlights: Dict[str, List[str]] = {}
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # Name match (highest weight)
        if query_lower in asset.name.lower():
            score += 10.0
            highlights['name'] = [asset.name]
        elif any(word in asset.name.lower() for word in query_words):
            score += 5.0
            highlights['name'] = [asset.name]
        
        # ID match
        if query_lower in asset.id.lower():
            score += 8.0
        
        # Description match
        desc_lower = asset.description.lower()
        if query_lower in desc_lower:
            score += 5.0
            # Extract highlight snippet
            idx = desc_lower.find(query_lower)
            start = max(0, idx - 30)
            end = min(len(asset.description), idx + len(query) + 30)
            highlights['description'] = [f"...{asset.description[start:end]}..."]
        elif any(word in desc_lower for word in query_words):
            score += 2.0
        
        # Tag match
        matching_tags = [tag for tag in asset.tags if any(word in tag.lower() for word in query_words)]
        if matching_tags:
            score += 3.0 * len(matching_tags)
            highlights['tags'] = matching_tags
        
        # Category match
        if query_lower in asset.category.lower():
            score += 2.0
        
        return score, highlights
    
    def _sort_results(self, results: List[SearchResult], sort_by: str, sort_order: str) -> List[SearchResult]:
        """Sort search results."""
        reverse = sort_order == "desc"
        
        if sort_by == "relevance":
            results.sort(key=lambda r: r.score, reverse=reverse)
        elif sort_by == "rating":
            results.sort(key=lambda r: r.asset.rating, reverse=reverse)
        elif sort_by == "usage":
            results.sort(key=lambda r: r.asset.usage_count, reverse=reverse)
        elif sort_by == "created":
            results.sort(key=lambda r: r.asset.created_at or datetime.min, reverse=reverse)
        elif sort_by == "name":
            results.sort(key=lambda r: r.asset.name.lower(), reverse=reverse)
        
        return results
    
    def get_asset(self, asset_type: AssetType, asset_id: str) -> Optional[AssetMetadata]:
        """Get a specific asset by type and ID."""
        self._ensure_loaded()
        key = f"{asset_type.value}:{asset_id}"
        return self._assets.get(key)
    
    def get_skill(self, skill_id: str) -> Optional[SkillConfig]:
        """Get a specific skill by ID."""
        self._ensure_loaded()
        return self._skills.get(skill_id)
    
    def list_skills(self, category: Optional[str] = None) -> SkillListResponse:
        """List all skills, optionally filtered by category."""
        self._ensure_loaded()
        
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if s.category and s.category.value == category]
        
        return SkillListResponse(
            success=True,
            skills=skills,
            total=len(skills)
        )
    
    def get_stats(self) -> RepositoryStats:
        """Get repository statistics."""
        self._ensure_loaded()
        
        assets_by_type: Dict[str, int] = {}
        assets_by_category: Dict[str, int] = {}
        tag_counts: Dict[str, int] = {}
        
        for asset in self._assets.values():
            # Count by type
            type_key = asset.type.value
            assets_by_type[type_key] = assets_by_type.get(type_key, 0) + 1
            
            # Count by category
            assets_by_category[asset.category] = assets_by_category.get(asset.category, 0) + 1
            
            # Count tags
            for tag in asset.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Sort tags by count
        top_tags = sorted(
            [{"tag": k, "count": v} for k, v in tag_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:20]
        
        # Get recent and popular assets
        all_assets = list(self._assets.values())
        recent = sorted(all_assets, key=lambda a: a.created_at or datetime.min, reverse=True)[:10]
        popular = sorted(all_assets, key=lambda a: a.usage_count, reverse=True)[:10]
        
        return RepositoryStats(
            total_assets=len(self._assets),
            assets_by_type=assets_by_type,
            assets_by_category=assets_by_category,
            top_tags=top_tags,
            recent_assets=recent,
            popular_assets=popular
        )
    
    def get_categories(self, asset_type: Optional[AssetType] = None) -> List[str]:
        """Get all categories, optionally filtered by asset type."""
        self._ensure_loaded()
        
        categories = set()
        for asset in self._assets.values():
            if asset_type is None or asset.type == asset_type:
                categories.add(asset.category)
        
        return sorted(list(categories))
    
    def get_tags(self, asset_type: Optional[AssetType] = None) -> List[str]:
        """Get all tags, optionally filtered by asset type."""
        self._ensure_loaded()
        
        tags = set()
        for asset in self._assets.values():
            if asset_type is None or asset.type == asset_type:
                tags.update(asset.tags)
        
        return sorted(list(tags))
    
    def reload(self):
        """Reload all assets from disk."""
        self._assets.clear()
        self._skills.clear()
        self._loaded = False
        self._ensure_loaded()


# Singleton
_repository_service: Optional[RepositoryService] = None


def get_repository_service() -> RepositoryService:
    """Get the repository service singleton."""
    global _repository_service
    if _repository_service is None:
        _repository_service = RepositoryService()
    return _repository_service
