"""
Storage service for persisting configurations.
"""
import os
import json
import yaml
import logging
import re
from typing import Optional, List, Dict, Any, TypeVar, Generic, Type
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel

from ..config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


def resolve_env_variables(data: Any, max_depth: int = 10) -> Any:
    """
    Recursively resolve environment variables in data structures.
    Supports both ${VAR_NAME} and $VAR_NAME syntax with nested resolution.
    
    Args:
        data: Data structure to resolve
        max_depth: Maximum recursion depth to prevent infinite loops
    """
    if isinstance(data, dict):
        return {k: resolve_env_variables(v, max_depth) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_env_variables(item, max_depth) for item in data]
    elif isinstance(data, str):
        result = data
        depth = 0
        
        # Keep resolving until no more variables or max depth reached
        while depth < max_depth:
            original = result
            
            # First, match ${VAR_NAME:default} or ${VAR_NAME} pattern (with braces)
            pattern_braces = r'\$\{([^}]+)\}'
            matches_braces = re.findall(pattern_braces, result)
            
            if matches_braces:
                for match in matches_braces:
                    # Check if there's a default value (VAR:default syntax)
                    if ':' in match:
                        var_name, default_value = match.split(':', 1)
                        env_value = os.getenv(var_name, default_value)
                        result = result.replace(f'${{{match}}}', env_value)
                    else:
                        var_name = match
                        env_value = os.getenv(var_name, '')
                        if env_value:
                            result = result.replace(f'${{{var_name}}}', env_value)
                        else:
                            logger.warning(f"Environment variable '{var_name}' not set, leaving placeholder")
            
            # Second, match $VAR_NAME pattern (without braces)
            pattern_simple = r'\$([A-Za-z_][A-Za-z0-9_]*)'
            matches_simple = re.findall(pattern_simple, result)
            
            if matches_simple:
                for var_name in matches_simple:
                    env_value = os.getenv(var_name, '')
                    if env_value:
                        result = result.replace(f'${var_name}', env_value)
                    else:
                        logger.warning(f"Environment variable '{var_name}' not set, leaving placeholder")
            
            # If nothing changed, we're done
            if result == original:
                break
            
            depth += 1
        
        if depth >= max_depth:
            logger.warning(f"Maximum recursion depth ({max_depth}) reached resolving: {data}")
        
        return result
    else:
        return data


class StorageService(Generic[T]):
    """Generic storage service for configuration files."""
    
    def __init__(self, directory: str, model_class: Type[T], file_extension: str = "yaml"):
        self.directory = Path(directory)
        self.model_class = model_class
        self.file_extension = file_extension
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure the storage directory exists."""
        self.directory.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, item_id: str) -> Path:
        """Get the file path for an item."""
        return self.directory / f"{item_id}.{self.file_extension}"
    
    def _find_file(self, item_id: str) -> Optional[Path]:
        """Find a file by ID, searching subdirectories recursively."""
        # First check the root directory
        direct_path = self._get_file_path(item_id)
        if direct_path.exists():
            return direct_path
        
        # Search subdirectories recursively
        for file_path in self.directory.rglob(f"{item_id}.{self.file_extension}"):
            return file_path
        
        return None
    
    def _serialize(self, item: T) -> str:
        """Serialize item to string."""
        data = item.model_dump(mode="json", exclude_none=True)
        if self.file_extension == "yaml":
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        else:
            return json.dumps(data, indent=2, default=str)
    
    def _deserialize(self, content: str) -> Dict[str, Any]:
        """Deserialize string to dict."""
        if self.file_extension == "yaml":
            return yaml.safe_load(content)
        else:
            return json.loads(content)
    
    def save(self, item: T) -> bool:
        """Save an item to storage."""
        try:
            item_id = getattr(item, 'id', None)
            if not item_id:
                raise ValueError("Item must have an 'id' field")
            
            file_path = self._get_file_path(item_id)
            content = self._serialize(item)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved {self.model_class.__name__} '{item_id}' to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving item: {e}")
            return False
    
    def load(self, item_id: str) -> Optional[T]:
        """Load an item from storage (searches subdirectories)."""
        try:
            file_path = self._find_file(item_id)
            if not file_path:
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            data = self._deserialize(content)
            # Resolve environment variables
            data = resolve_env_variables(data)
            return self.model_class(**data)
            
        except Exception as e:
            logger.error(f"Error loading item '{item_id}': {e}")
            return None
    
    def delete(self, item_id: str) -> bool:
        """Delete an item from storage."""
        try:
            file_path = self._get_file_path(item_id)
            if file_path.exists():
                os.remove(file_path)
                logger.info(f"Deleted {self.model_class.__name__} '{item_id}'")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting item '{item_id}': {e}")
            return False
    
    def exists(self, item_id: str) -> bool:
        """Check if an item exists (searches subdirectories)."""
        return self._find_file(item_id) is not None
    
    def list_all(self) -> List[T]:
        """List all items in storage (including subdirectories)."""
        items = []
        seen_ids = set()
        try:
            # Use rglob to search recursively
            for file_path in self.directory.rglob(f"*.{self.file_extension}"):
                item_id = file_path.stem
                # Avoid duplicates if same ID exists in multiple places
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
                item = self._load_from_path(file_path)
                if item:
                    items.append(item)
        except Exception as e:
            logger.error(f"Error listing items: {e}")
        return items
    
    def _load_from_path(self, file_path: Path) -> Optional[T]:
        """Load an item from a specific file path."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            data = self._deserialize(content)
            # Resolve environment variables
            data = resolve_env_variables(data)
            return self.model_class(**data)
        except Exception as e:
            logger.error(f"Error loading from {file_path}: {e}")
            return None
    
    def list_ids(self) -> List[str]:
        """List all item IDs in storage (including subdirectories)."""
        ids = set()
        try:
            for file_path in self.directory.rglob(f"*.{self.file_extension}"):
                ids.add(file_path.stem)
        except Exception as e:
            logger.error(f"Error listing IDs: {e}")
        return list(ids)
    
    def search(self, **filters) -> List[T]:
        """Search items by field values."""
        results = []
        for item in self.list_all():
            matches = True
            for field, value in filters.items():
                item_value = getattr(item, field, None)
                if item_value != value:
                    # Check if it's a list and value is in it
                    if isinstance(item_value, list) and value in item_value:
                        continue
                    matches = False
                    break
            if matches:
                results.append(item)
        return results
    
    def count(self) -> int:
        """Count total items in storage (including subdirectories)."""
        return len(set(p.stem for p in self.directory.rglob(f"*.{self.file_extension}")))
