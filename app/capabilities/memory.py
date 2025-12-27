"""
Memory Management capability.

Provides short-term, long-term, and shared memory for agents with
semantic retrieval capabilities.
"""
import logging
import uuid
import hashlib
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .base import Capability, CapabilityConfig

logger = logging.getLogger(__name__)


class MemoryScope(str, Enum):
    """Scope of memory."""
    SESSION = "session"      # Per-session memory
    USER = "user"           # Per-user across sessions
    AGENT = "agent"         # Per-agent across users
    GLOBAL = "global"       # Global shared memory


class MemoryType(str, Enum):
    """Type of memory."""
    SHORT_TERM = "short_term"   # Recent context window
    LONG_TERM = "long_term"     # Persistent semantic memory
    EPISODIC = "episodic"       # Event/conversation memories
    WORKING = "working"         # Current task working memory


class MemoryEntry(BaseModel):
    """A memory entry."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(..., description="Memory content")
    scope: MemoryScope = Field(default=MemoryScope.SESSION)
    memory_type: MemoryType = Field(default=MemoryType.SHORT_TERM)
    
    # Identifiers
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Relevance
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = Field(default=0)
    
    # Embedding for semantic search
    embedding: Optional[List[float]] = None
    content_hash: Optional[str] = None
    
    def touch(self):
        """Update access time and count."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1


class MemoryConfig(CapabilityConfig):
    """Memory manager configuration."""
    # Short-term memory
    short_term_limit: int = Field(default=20, description="Max short-term memories")
    
    # Long-term memory
    long_term_limit: int = Field(default=10000, description="Max long-term memories")
    auto_consolidate: bool = Field(default=True, description="Auto-consolidate to long-term")
    consolidation_threshold: int = Field(default=10, description="Consolidate after N accesses")
    
    # Embedding
    embedding_enabled: bool = Field(default=False, description="Enable semantic embeddings")
    embedding_model: Optional[str] = Field(default=None, description="Embedding model name")
    embedding_endpoint: Optional[str] = Field(default=None, description="Embedding API endpoint")
    
    # Storage
    storage_backend: str = Field(default="memory", description="Storage: memory, redis, vector_db")
    
    # Cleanup
    ttl_days: int = Field(default=30, description="Default TTL for long-term memories")


class MemoryManager(Capability):
    """Memory management capability."""
    
    name = "memory"
    version = "1.0.0"
    description = "Multi-scope memory management with semantic retrieval"
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        super().__init__(config or MemoryConfig())
        self.config: MemoryConfig = self.config
        
        # In-memory storage (replace with actual backends)
        self._memories: Dict[str, MemoryEntry] = {}
        self._scope_index: Dict[str, Dict[str, List[str]]] = {
            scope.value: {} for scope in MemoryScope
        }
    
    async def _do_initialize(self):
        """Initialize memory manager."""
        logger.info(f"Memory manager initialized (embedding={self.config.embedding_enabled})")
    
    def _get_scope_key(self, entry: MemoryEntry) -> str:
        """Get the scope key for indexing."""
        if entry.scope == MemoryScope.SESSION:
            return entry.session_id or "default"
        elif entry.scope == MemoryScope.USER:
            return entry.user_id or "default"
        elif entry.scope == MemoryScope.AGENT:
            return entry.agent_id or "default"
        else:
            return "global"
    
    def _compute_hash(self, content: str) -> str:
        """Compute content hash for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def store(
        self,
        content: str,
        scope: MemoryScope = MemoryScope.SESSION,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        importance: float = 0.5
    ) -> MemoryEntry:
        """Store a new memory."""
        content_hash = self._compute_hash(content)
        
        # Check for duplicate
        for entry in self._memories.values():
            if entry.content_hash == content_hash:
                entry.touch()
                return entry
        
        entry = MemoryEntry(
            content=content,
            scope=scope,
            memory_type=memory_type,
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            metadata=metadata or {},
            tags=tags or [],
            importance=importance,
            content_hash=content_hash
        )
        
        # Generate embedding if enabled
        if self.config.embedding_enabled:
            entry.embedding = await self._generate_embedding(content)
        
        # Store
        self._memories[entry.id] = entry
        
        # Index by scope
        scope_key = self._get_scope_key(entry)
        if scope_key not in self._scope_index[scope.value]:
            self._scope_index[scope.value][scope_key] = []
        self._scope_index[scope.value][scope_key].append(entry.id)
        
        # Enforce limits
        await self._enforce_limits(scope, scope_key, memory_type)
        
        logger.debug(f"Stored memory {entry.id} ({scope.value}/{memory_type.value})")
        return entry
    
    async def _generate_embedding(self, content: str) -> Optional[List[float]]:
        """Generate embedding for content."""
        # TODO: Integrate with actual embedding service
        return None
    
    async def _enforce_limits(self, scope: MemoryScope, scope_key: str, memory_type: MemoryType):
        """Enforce memory limits."""
        ids = self._scope_index[scope.value].get(scope_key, [])
        
        if memory_type == MemoryType.SHORT_TERM:
            limit = self.config.short_term_limit
        else:
            limit = self.config.long_term_limit
        
        # Filter by type
        type_ids = [
            mid for mid in ids 
            if mid in self._memories and self._memories[mid].memory_type == memory_type
        ]
        
        if len(type_ids) > limit:
            # Remove oldest/least important
            to_remove = sorted(
                type_ids,
                key=lambda x: (self._memories[x].importance, self._memories[x].accessed_at)
            )[:len(type_ids) - limit]
            
            for mid in to_remove:
                await self.delete(mid)
    
    async def retrieve(
        self,
        query: Optional[str] = None,
        scope: Optional[MemoryScope] = None,
        memory_type: Optional[MemoryType] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        semantic: bool = False
    ) -> List[MemoryEntry]:
        """Retrieve memories with filtering."""
        results = list(self._memories.values())
        
        # Filter by scope
        if scope:
            results = [m for m in results if m.scope == scope]
        
        # Filter by type
        if memory_type:
            results = [m for m in results if m.memory_type == memory_type]
        
        # Filter by identifiers
        if session_id:
            results = [m for m in results if m.session_id == session_id]
        if user_id:
            results = [m for m in results if m.user_id == user_id]
        if agent_id:
            results = [m for m in results if m.agent_id == agent_id]
        
        # Filter by tags
        if tags:
            results = [m for m in results if any(t in m.tags for t in tags)]
        
        # Semantic search if query provided
        if query and semantic and self.config.embedding_enabled:
            results = await self._semantic_search(query, results, limit)
        else:
            # Sort by recency and importance
            results.sort(key=lambda m: (m.importance, m.accessed_at), reverse=True)
            results = results[:limit]
        
        # Touch retrieved memories
        for entry in results:
            entry.touch()
        
        return results
    
    async def _semantic_search(
        self, 
        query: str, 
        candidates: List[MemoryEntry], 
        limit: int
    ) -> List[MemoryEntry]:
        """Semantic search over memories."""
        query_embedding = await self._generate_embedding(query)
        if not query_embedding:
            return candidates[:limit]
        
        # Compute similarities
        scored = []
        for entry in candidates:
            if entry.embedding:
                score = self._cosine_similarity(query_embedding, entry.embedding)
                scored.append((entry, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:limit]]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0
    
    async def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a memory by ID."""
        entry = self._memories.get(memory_id)
        if entry:
            entry.touch()
        return entry
    
    async def update(self, memory_id: str, updates: Dict[str, Any]) -> Optional[MemoryEntry]:
        """Update a memory."""
        entry = self._memories.get(memory_id)
        if not entry:
            return None
        
        for key, value in updates.items():
            if hasattr(entry, key) and key not in ['id', 'created_at']:
                setattr(entry, key, value)
        
        return entry
    
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory."""
        entry = self._memories.get(memory_id)
        if not entry:
            return False
        
        # Remove from index
        scope_key = self._get_scope_key(entry)
        if scope_key in self._scope_index[entry.scope.value]:
            ids = self._scope_index[entry.scope.value][scope_key]
            if memory_id in ids:
                ids.remove(memory_id)
        
        del self._memories[memory_id]
        return True
    
    async def consolidate(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> int:
        """Consolidate short-term memories to long-term."""
        if not self.config.auto_consolidate:
            return 0
        
        # Find high-access short-term memories
        candidates = await self.retrieve(
            memory_type=MemoryType.SHORT_TERM,
            session_id=session_id,
            user_id=user_id,
            limit=100
        )
        
        consolidated = 0
        for entry in candidates:
            if entry.access_count >= self.config.consolidation_threshold:
                entry.memory_type = MemoryType.LONG_TERM
                entry.scope = MemoryScope.USER if entry.user_id else MemoryScope.AGENT
                consolidated += 1
        
        if consolidated:
            logger.info(f"Consolidated {consolidated} memories to long-term")
        return consolidated
    
    async def clear(
        self,
        scope: Optional[MemoryScope] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> int:
        """Clear memories."""
        to_delete = []
        
        for mid, entry in self._memories.items():
            if scope and entry.scope != scope:
                continue
            if session_id and entry.session_id != session_id:
                continue
            if user_id and entry.user_id != user_id:
                continue
            to_delete.append(mid)
        
        for mid in to_delete:
            await self.delete(mid)
        
        return len(to_delete)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        by_scope = {scope.value: 0 for scope in MemoryScope}
        by_type = {mtype.value: 0 for mtype in MemoryType}
        
        for entry in self._memories.values():
            by_scope[entry.scope.value] += 1
            by_type[entry.memory_type.value] += 1
        
        return {
            "total_memories": len(self._memories),
            "by_scope": by_scope,
            "by_type": by_type,
            "embedding_enabled": self.config.embedding_enabled
        }
