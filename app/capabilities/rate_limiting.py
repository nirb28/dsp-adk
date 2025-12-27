"""
Rate Limiting capability.

Provides configurable rate limiting with multiple strategies
and scopes.
"""
import logging
import asyncio
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from collections import defaultdict

from .base import Capability, CapabilityConfig

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(str, Enum):
    """Scope for rate limiting."""
    GLOBAL = "global"
    USER = "user"
    IP = "ip"
    AGENT = "agent"
    ENDPOINT = "endpoint"


class RateLimitRule(BaseModel):
    """A rate limit rule."""
    id: str
    name: str
    enabled: bool = True
    
    # Limits
    requests_per_second: Optional[float] = None
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    
    # Token limits
    tokens_per_minute: Optional[int] = None
    tokens_per_hour: Optional[int] = None
    
    # Scope
    scope: RateLimitScope = RateLimitScope.GLOBAL
    scope_key: Optional[str] = None  # Specific user_id, ip, etc.
    
    # Strategy
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    
    # Burst
    burst_size: int = Field(default=10, description="Max burst size for token bucket")
    
    # Actions
    retry_after_seconds: int = Field(default=60)


class RateLimitResult(BaseModel):
    """Result of rate limit check."""
    allowed: bool = True
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    
    # Current state
    current_count: int = 0
    limit: int = 0
    remaining: int = 0
    
    # Retry info
    retry_after_seconds: Optional[int] = None
    reset_at: Optional[datetime] = None
    
    # Details
    message: str = ""


class RateLimitConfig(CapabilityConfig):
    """Rate limiting configuration."""
    # Default limits
    default_requests_per_minute: int = Field(default=60)
    default_requests_per_hour: int = Field(default=1000)
    default_tokens_per_minute: int = Field(default=100000)
    
    # Strategy
    default_strategy: RateLimitStrategy = Field(default=RateLimitStrategy.SLIDING_WINDOW)
    
    # Cleanup
    cleanup_interval_seconds: int = Field(default=60)
    
    # Custom rules
    rules: List[RateLimitRule] = Field(default_factory=list)


class TokenBucket:
    """Token bucket implementation."""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # Tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait for tokens."""
        if self.tokens >= tokens:
            return 0
        needed = tokens - self.tokens
        return needed / self.rate


class SlidingWindow:
    """Sliding window counter implementation."""
    
    def __init__(self, window_seconds: int, max_requests: int):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.requests: List[float] = []
        self._lock = asyncio.Lock()
    
    async def record(self) -> bool:
        """Record a request and check if allowed."""
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Remove old requests
            self.requests = [t for t in self.requests if t > cutoff]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    def get_count(self) -> int:
        """Get current request count."""
        cutoff = time.time() - self.window_seconds
        return len([t for t in self.requests if t > cutoff])
    
    def get_remaining(self) -> int:
        """Get remaining requests."""
        return max(0, self.max_requests - self.get_count())
    
    def get_reset_time(self) -> float:
        """Get time until window resets."""
        if not self.requests:
            return 0
        oldest = min(self.requests)
        return max(0, oldest + self.window_seconds - time.time())


class RateLimiter(Capability):
    """Rate limiting capability."""
    
    name = "rate_limiting"
    version = "1.0.0"
    description = "Request and token rate limiting"
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        super().__init__(config or RateLimitConfig())
        self.config: RateLimitConfig = self.config
        
        # Limiters by scope
        self._windows: Dict[str, SlidingWindow] = {}
        self._buckets: Dict[str, TokenBucket] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def _do_initialize(self):
        """Initialize rate limiter."""
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Rate limiter initialized")
    
    async def _do_shutdown(self):
        """Shutdown rate limiter."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """Background cleanup of old entries."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                await self._cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")
    
    async def _cleanup(self):
        """Clean up old rate limit entries."""
        # Remove windows with no recent activity
        now = time.time()
        to_remove = []
        
        for key, window in self._windows.items():
            if window.get_count() == 0:
                to_remove.append(key)
        
        for key in to_remove:
            del self._windows[key]
    
    def _get_limiter_key(
        self,
        scope: RateLimitScope,
        user_id: Optional[str] = None,
        ip: Optional[str] = None,
        agent_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        rule_id: Optional[str] = None
    ) -> str:
        """Generate a unique key for the limiter."""
        parts = [scope.value]
        
        if scope == RateLimitScope.USER and user_id:
            parts.append(user_id)
        elif scope == RateLimitScope.IP and ip:
            parts.append(ip)
        elif scope == RateLimitScope.AGENT and agent_id:
            parts.append(agent_id)
        elif scope == RateLimitScope.ENDPOINT and endpoint:
            parts.append(endpoint)
        
        if rule_id:
            parts.append(rule_id)
        
        return ":".join(parts)
    
    async def check(
        self,
        user_id: Optional[str] = None,
        ip: Optional[str] = None,
        agent_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        tokens: int = 0
    ) -> RateLimitResult:
        """Check if request is allowed."""
        # Check custom rules first
        for rule in self.config.rules:
            if not rule.enabled:
                continue
            
            result = await self._check_rule(
                rule, user_id, ip, agent_id, endpoint, tokens
            )
            if not result.allowed:
                return result
        
        # Check default limits
        result = await self._check_default_limits(
            user_id, ip, agent_id, endpoint, tokens
        )
        
        return result
    
    async def _check_rule(
        self,
        rule: RateLimitRule,
        user_id: Optional[str],
        ip: Optional[str],
        agent_id: Optional[str],
        endpoint: Optional[str],
        tokens: int
    ) -> RateLimitResult:
        """Check a specific rule."""
        result = RateLimitResult(rule_id=rule.id, rule_name=rule.name)
        
        # Check scope match
        if rule.scope == RateLimitScope.USER and rule.scope_key and rule.scope_key != user_id:
            result.allowed = True
            return result
        if rule.scope == RateLimitScope.AGENT and rule.scope_key and rule.scope_key != agent_id:
            result.allowed = True
            return result
        
        key = self._get_limiter_key(
            rule.scope, user_id, ip, agent_id, endpoint, rule.id
        )
        
        # Check request limits
        if rule.requests_per_minute:
            if not await self._check_window(key + ":rpm", 60, rule.requests_per_minute):
                result.allowed = False
                result.limit = rule.requests_per_minute
                result.message = f"Rate limit exceeded: {rule.requests_per_minute}/min"
                result.retry_after_seconds = rule.retry_after_seconds
                return result
        
        if rule.requests_per_hour:
            if not await self._check_window(key + ":rph", 3600, rule.requests_per_hour):
                result.allowed = False
                result.limit = rule.requests_per_hour
                result.message = f"Rate limit exceeded: {rule.requests_per_hour}/hour"
                result.retry_after_seconds = rule.retry_after_seconds
                return result
        
        # Check token limits
        if tokens > 0 and rule.tokens_per_minute:
            if not await self._check_token_bucket(
                key + ":tpm", 
                rule.tokens_per_minute / 60,
                rule.burst_size,
                tokens
            ):
                result.allowed = False
                result.message = f"Token limit exceeded: {rule.tokens_per_minute}/min"
                result.retry_after_seconds = rule.retry_after_seconds
                return result
        
        result.allowed = True
        return result
    
    async def _check_default_limits(
        self,
        user_id: Optional[str],
        ip: Optional[str],
        agent_id: Optional[str],
        endpoint: Optional[str],
        tokens: int
    ) -> RateLimitResult:
        """Check default rate limits."""
        result = RateLimitResult()
        
        # Determine scope (user > ip > global)
        if user_id:
            scope = RateLimitScope.USER
            key = f"default:user:{user_id}"
        elif ip:
            scope = RateLimitScope.IP
            key = f"default:ip:{ip}"
        else:
            scope = RateLimitScope.GLOBAL
            key = "default:global"
        
        # Check requests per minute
        if self.config.default_requests_per_minute:
            window_key = key + ":rpm"
            allowed = await self._check_window(
                window_key,
                60,
                self.config.default_requests_per_minute
            )
            
            if not allowed:
                window = self._windows.get(window_key)
                result.allowed = False
                result.limit = self.config.default_requests_per_minute
                result.current_count = window.get_count() if window else 0
                result.remaining = 0
                result.message = f"Rate limit exceeded: {self.config.default_requests_per_minute}/min"
                result.retry_after_seconds = 60
                return result
            
            window = self._windows.get(window_key)
            if window:
                result.current_count = window.get_count()
                result.remaining = window.get_remaining()
                result.limit = self.config.default_requests_per_minute
        
        # Check tokens per minute
        if tokens > 0 and self.config.default_tokens_per_minute:
            bucket_key = key + ":tpm"
            allowed = await self._check_token_bucket(
                bucket_key,
                self.config.default_tokens_per_minute / 60,
                1000,  # Burst size
                tokens
            )
            
            if not allowed:
                result.allowed = False
                result.message = f"Token rate limit exceeded"
                result.retry_after_seconds = 60
                return result
        
        result.allowed = True
        return result
    
    async def _check_window(
        self,
        key: str,
        window_seconds: int,
        max_requests: int
    ) -> bool:
        """Check sliding window limit."""
        if key not in self._windows:
            self._windows[key] = SlidingWindow(window_seconds, max_requests)
        
        window = self._windows[key]
        return await window.record()
    
    async def _check_token_bucket(
        self,
        key: str,
        rate: float,
        capacity: int,
        tokens: int
    ) -> bool:
        """Check token bucket limit."""
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(rate, capacity)
        
        bucket = self._buckets[key]
        return await bucket.acquire(tokens)
    
    async def record_request(
        self,
        user_id: Optional[str] = None,
        ip: Optional[str] = None,
        agent_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        tokens: int = 0
    ):
        """Record a request (for manual recording)."""
        # This is called after check() passes and request is processed
        # Used for tracking even when check was already done
        pass
    
    # Rule Management
    async def add_rule(self, rule: RateLimitRule):
        """Add a rate limit rule."""
        self.config.rules.append(rule)
    
    async def remove_rule(self, rule_id: str) -> bool:
        """Remove a rate limit rule."""
        for i, rule in enumerate(self.config.rules):
            if rule.id == rule_id:
                del self.config.rules[i]
                return True
        return False
    
    async def list_rules(self) -> List[RateLimitRule]:
        """List all rules."""
        return self.config.rules
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter stats."""
        return {
            "active_windows": len(self._windows),
            "active_buckets": len(self._buckets),
            "custom_rules": len(self.config.rules),
            "default_rpm": self.config.default_requests_per_minute,
            "default_tpm": self.config.default_tokens_per_minute
        }
