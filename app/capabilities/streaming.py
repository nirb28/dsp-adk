"""
Streaming Support capability.

Provides real-time token streaming for LLM responses with
event-driven architecture.
"""
import logging
import asyncio
import uuid
import json
from typing import Optional, Dict, Any, List, AsyncGenerator, Callable, Awaitable
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .base import Capability, CapabilityConfig

logger = logging.getLogger(__name__)


class StreamEventType(str, Enum):
    """Types of stream events."""
    START = "start"
    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CHUNK = "chunk"
    ERROR = "error"
    END = "end"


class StreamEvent(BaseModel):
    """A streaming event."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stream_id: str
    event_type: StreamEventType
    data: Any = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sequence: int = 0
    
    # For tokens
    token: Optional[str] = None
    tokens_so_far: int = 0
    
    # For tool calls
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    
    # For errors
    error: Optional[str] = None
    
    def to_sse(self) -> str:
        """Convert to Server-Sent Event format."""
        data = {
            "id": self.id,
            "type": self.event_type.value,
            "sequence": self.sequence,
            "data": self.data,
            "token": self.token,
            "tokens_so_far": self.tokens_so_far,
            "timestamp": self.timestamp.isoformat()
        }
        if self.error:
            data["error"] = self.error
        if self.tool_name:
            data["tool_name"] = self.tool_name
            data["tool_args"] = self.tool_args
        
        return f"data: {json.dumps(data)}\n\n"


class StreamConfig(CapabilityConfig):
    """Streaming configuration."""
    buffer_size: int = Field(default=100, description="Event buffer size")
    timeout_seconds: int = Field(default=300, description="Stream timeout")
    heartbeat_interval: int = Field(default=15, description="Heartbeat interval in seconds")
    max_concurrent_streams: int = Field(default=1000, description="Max concurrent streams")


class Stream:
    """A streaming response handler."""
    
    def __init__(self, stream_id: str, config: StreamConfig):
        self.id = stream_id
        self.config = config
        self.created_at = datetime.utcnow()
        self.sequence = 0
        self._buffer: asyncio.Queue = asyncio.Queue(maxsize=config.buffer_size)
        self._closed = False
        self._listeners: List[Callable[[StreamEvent], Awaitable[None]]] = []
        self._accumulated_text = ""
        self._token_count = 0
    
    @property
    def is_closed(self) -> bool:
        return self._closed
    
    @property
    def accumulated_text(self) -> str:
        return self._accumulated_text
    
    @property
    def token_count(self) -> int:
        return self._token_count
    
    async def emit(self, event_type: StreamEventType, **kwargs) -> StreamEvent:
        """Emit a stream event."""
        if self._closed and event_type != StreamEventType.END:
            raise RuntimeError("Stream is closed")
        
        self.sequence += 1
        event = StreamEvent(
            stream_id=self.id,
            event_type=event_type,
            sequence=self.sequence,
            **kwargs
        )
        
        # Accumulate text
        if event_type == StreamEventType.TOKEN and event.token:
            self._accumulated_text += event.token
            self._token_count += 1
            event.tokens_so_far = self._token_count
        
        # Add to buffer
        try:
            self._buffer.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"Stream {self.id} buffer full, dropping event")
        
        # Notify listeners
        for listener in self._listeners:
            try:
                await listener(event)
            except Exception as e:
                logger.error(f"Stream listener error: {e}")
        
        return event
    
    async def emit_token(self, token: str) -> StreamEvent:
        """Emit a token event."""
        return await self.emit(StreamEventType.TOKEN, token=token)
    
    async def emit_tool_call(self, tool_name: str, tool_args: Dict[str, Any]) -> StreamEvent:
        """Emit a tool call event."""
        return await self.emit(
            StreamEventType.TOOL_CALL,
            tool_name=tool_name,
            tool_args=tool_args
        )
    
    async def emit_error(self, error: str) -> StreamEvent:
        """Emit an error event."""
        return await self.emit(StreamEventType.ERROR, error=error)
    
    async def start(self) -> StreamEvent:
        """Start the stream."""
        return await self.emit(StreamEventType.START)
    
    async def end(self) -> StreamEvent:
        """End the stream."""
        event = await self.emit(
            StreamEventType.END,
            data={
                "total_tokens": self._token_count,
                "accumulated_text": self._accumulated_text
            }
        )
        self._closed = True
        return event
    
    def add_listener(self, listener: Callable[[StreamEvent], Awaitable[None]]):
        """Add an event listener."""
        self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable[[StreamEvent], Awaitable[None]]):
        """Remove an event listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    async def events(self) -> AsyncGenerator[StreamEvent, None]:
        """Iterate over stream events."""
        while not self._closed or not self._buffer.empty():
            try:
                event = await asyncio.wait_for(
                    self._buffer.get(),
                    timeout=self.config.timeout_seconds
                )
                yield event
                if event.event_type == StreamEventType.END:
                    break
            except asyncio.TimeoutError:
                logger.warning(f"Stream {self.id} timed out")
                break
    
    async def sse_events(self) -> AsyncGenerator[str, None]:
        """Iterate over events in SSE format."""
        async for event in self.events():
            yield event.to_sse()


class StreamingManager(Capability):
    """Streaming support capability."""
    
    name = "streaming"
    version = "1.0.0"
    description = "Real-time token streaming for LLM responses"
    
    def __init__(self, config: Optional[StreamConfig] = None):
        super().__init__(config or StreamConfig())
        self.config: StreamConfig = self.config
        self._streams: Dict[str, Stream] = {}
    
    async def _do_initialize(self):
        """Initialize streaming manager."""
        logger.info("Streaming manager initialized")
    
    async def _do_shutdown(self):
        """Shutdown all streams."""
        for stream in list(self._streams.values()):
            if not stream.is_closed:
                await stream.end()
        self._streams.clear()
    
    async def create_stream(self, stream_id: Optional[str] = None) -> Stream:
        """Create a new stream."""
        if len(self._streams) >= self.config.max_concurrent_streams:
            # Clean up closed streams
            self._streams = {
                sid: s for sid, s in self._streams.items() 
                if not s.is_closed
            }
            if len(self._streams) >= self.config.max_concurrent_streams:
                raise RuntimeError("Maximum concurrent streams reached")
        
        stream_id = stream_id or str(uuid.uuid4())
        stream = Stream(stream_id, self.config)
        self._streams[stream_id] = stream
        
        logger.debug(f"Created stream {stream_id}")
        return stream
    
    async def get_stream(self, stream_id: str) -> Optional[Stream]:
        """Get a stream by ID."""
        return self._streams.get(stream_id)
    
    async def close_stream(self, stream_id: str) -> bool:
        """Close a stream."""
        stream = self._streams.get(stream_id)
        if stream and not stream.is_closed:
            await stream.end()
            return True
        return False
    
    async def delete_stream(self, stream_id: str) -> bool:
        """Delete a stream."""
        if stream_id in self._streams:
            stream = self._streams[stream_id]
            if not stream.is_closed:
                await stream.end()
            del self._streams[stream_id]
            return True
        return False
    
    async def list_streams(self, include_closed: bool = False) -> List[Dict[str, Any]]:
        """List active streams."""
        streams = []
        for stream_id, stream in self._streams.items():
            if not include_closed and stream.is_closed:
                continue
            streams.append({
                "id": stream_id,
                "created_at": stream.created_at.isoformat(),
                "token_count": stream.token_count,
                "is_closed": stream.is_closed
            })
        return streams
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        active = sum(1 for s in self._streams.values() if not s.is_closed)
        total_tokens = sum(s.token_count for s in self._streams.values())
        
        return {
            "total_streams": len(self._streams),
            "active_streams": active,
            "total_tokens_streamed": total_tokens,
            "max_concurrent": self.config.max_concurrent_streams
        }
