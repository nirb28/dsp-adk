"""
Storage service for persisting configurations.
"""
import os
import json
import yaml
import logging
from typing import Optional, List, Dict, Any, TypeVar, Generic, Type
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel

from ..config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


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
        """Load an item from storage."""
        try:
            file_path = self._get_file_path(item_id)
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            data = self._deserialize(content)
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
        """Check if an item exists."""
        return self._get_file_path(item_id).exists()
    
    def list_all(self) -> List[T]:
        """List all items in storage."""
        items = []
        try:
            for file_path in self.directory.glob(f"*.{self.file_extension}"):
                item_id = file_path.stem
                item = self.load(item_id)
                if item:
                    items.append(item)
        except Exception as e:
            logger.error(f"Error listing items: {e}")
        return items
    
    def list_ids(self) -> List[str]:
        """List all item IDs in storage."""
        ids = []
        try:
            for file_path in self.directory.glob(f"*.{self.file_extension}"):
                ids.append(file_path.stem)
        except Exception as e:
            logger.error(f"Error listing IDs: {e}")
        return ids
    
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
        """Count total items in storage."""
        return len(list(self.directory.glob(f"*.{self.file_extension}")))
