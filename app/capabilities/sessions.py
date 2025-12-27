"""
Session Management capability.

Provides persistent sessions with conversation history, state management,
and session lifecycle handling.
"""
import logging
import uuid
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field

from .base import Capability, CapabilityConfig

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """Session status."""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    CLOSED = "closed"


class Message(BaseModel):
    """A message in the conversation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str = Field(..., description="Role: user, assistant, system, tool")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # For tool messages
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None


class Session(BaseModel):
    """A user session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    graph_id: Optional[str] = None
    
    # Status
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Conversation
    messages: List[Message] = Field(default_factory=list)
    
    # State
    state: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Stats
    message_count: int = 0
    token_count: int = 0
    
    def add_message(self, role: str, content: str, **kwargs) -> Message:
        """Add a message to the session."""
        message = Message(role=role, content=content, **kwargs)
        self.messages.append(message)
        self.message_count += 1
        self.updated_at = datetime.utcnow()
        return message
    
    def get_messages(self, limit: Optional[int] = None, roles: Optional[List[str]] = None) -> List[Message]:
        """Get messages with optional filtering."""
        messages = self.messages
        if roles:
            messages = [m for m in messages if m.role in roles]
        if limit:
            messages = messages[-limit:]
        return messages
    
    def get_context_window(self, max_messages: int = 20) -> List[Dict[str, str]]:
        """Get messages formatted for LLM context."""
        messages = self.get_messages(limit=max_messages)
        return [{"role": m.role, "content": m.content} for m in messages]
    
    def update_state(self, updates: Dict[str, Any]):
        """Update session state."""
        self.state.update(updates)
        self.updated_at = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return self.status == SessionStatus.EXPIRED


class SessionConfig(CapabilityConfig):
    """Session manager configuration."""
    default_ttl_minutes: int = Field(default=60, description="Default session TTL in minutes")
    max_messages: int = Field(default=1000, description="Maximum messages per session")
    max_sessions: int = Field(default=10000, description="Maximum concurrent sessions")
    cleanup_interval_seconds: int = Field(default=300, description="Cleanup interval in seconds")
    persist_sessions: bool = Field(default=False, description="Persist sessions to storage")
    storage_backend: str = Field(default="memory", description="Storage backend: memory, redis, database")


class SessionManager(Capability):
    """Session management capability."""
    
    name = "sessions"
    version = "1.0.0"
    description = "Session management with conversation history"
    
    def __init__(self, config: Optional[SessionConfig] = None):
        super().__init__(config or SessionConfig())
        self.config: SessionConfig = self.config
        self._sessions: Dict[str, Session] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def _do_initialize(self):
        """Initialize session manager."""
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Session manager initialized with TTL={self.config.default_ttl_minutes}m")
    
    async def _do_shutdown(self):
        """Shutdown session manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    
    async def create_session(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        graph_id: Optional[str] = None,
        ttl_minutes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Create a new session."""
        if len(self._sessions) >= self.config.max_sessions:
            await self.cleanup_expired()
            if len(self._sessions) >= self.config.max_sessions:
                raise RuntimeError("Maximum sessions reached")
        
        ttl = ttl_minutes or self.config.default_ttl_minutes
        expires_at = datetime.utcnow() + timedelta(minutes=ttl) if ttl > 0 else None
        
        session = Session(
            user_id=user_id,
            agent_id=agent_id,
            graph_id=graph_id,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self._sessions[session.id] = session
        logger.info(f"Created session {session.id} for user {user_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            session.status = SessionStatus.EXPIRED
        return session
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Session]:
        """Update session properties."""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.updated_at = datetime.utcnow()
        return session
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        **kwargs
    ) -> Optional[Message]:
        """Add a message to a session."""
        session = await self.get_session(session_id)
        if not session or session.status != SessionStatus.ACTIVE:
            return None
        
        if session.message_count >= self.config.max_messages:
            # Remove oldest messages
            session.messages = session.messages[-(self.config.max_messages - 1):]
        
        return session.add_message(role, content, **kwargs)
    
    async def close_session(self, session_id: str) -> bool:
        """Close a session."""
        session = self._sessions.get(session_id)
        if session:
            session.status = SessionStatus.CLOSED
            logger.info(f"Closed session {session_id}")
            return True
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session {session_id}")
            return True
        return False
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 100
    ) -> List[Session]:
        """List sessions with optional filtering."""
        sessions = list(self._sessions.values())
        
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions[:limit]
    
    async def cleanup_expired(self) -> int:
        """Clean up expired sessions."""
        expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
        for sid in expired:
            del self._sessions[sid]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        active = sum(1 for s in self._sessions.values() if s.status == SessionStatus.ACTIVE)
        total_messages = sum(s.message_count for s in self._sessions.values())
        
        return {
            "total_sessions": len(self._sessions),
            "active_sessions": active,
            "total_messages": total_messages,
            "max_sessions": self.config.max_sessions
        }
