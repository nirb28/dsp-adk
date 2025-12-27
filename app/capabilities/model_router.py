"""
Model Router capability.

Provides intelligent routing to different models based on
task type, cost, latency, and availability.
"""
import logging
import random
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .base import Capability, CapabilityConfig

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Model routing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_COST = "least_cost"
    LEAST_LATENCY = "least_latency"
    TASK_BASED = "task_based"
    LOAD_BALANCED = "load_balanced"
    FALLBACK = "fallback"
    RANDOM = "random"


class ModelTier(str, Enum):
    """Model capability tiers."""
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"
    LOCAL = "local"


class TaskType(str, Enum):
    """Types of tasks for routing."""
    SIMPLE_QA = "simple_qa"
    COMPLEX_REASONING = "complex_reasoning"
    CODE_GENERATION = "code_generation"
    CREATIVE_WRITING = "creative_writing"
    SUMMARIZATION = "summarization"
    EMBEDDING = "embedding"


class ModelEndpoint(BaseModel):
    """A model endpoint configuration."""
    id: str
    name: str
    provider: str
    model: str
    endpoint: str
    api_key_env: Optional[str] = None
    tier: ModelTier = ModelTier.STANDARD
    supported_tasks: List[TaskType] = Field(default_factory=list)
    max_tokens: int = 4096
    input_price: float = 0.001
    output_price: float = 0.002
    avg_latency_ms: float = 500
    enabled: bool = True
    healthy: bool = True
    consecutive_failures: int = 0


class RoutingDecision(BaseModel):
    """Result of routing decision."""
    endpoint: ModelEndpoint
    reason: str
    alternatives: List[str] = Field(default_factory=list)


class ModelRouterConfig(CapabilityConfig):
    """Model router configuration."""
    default_strategy: RoutingStrategy = Field(default=RoutingStrategy.TASK_BASED)
    fallback_enabled: bool = True
    max_fallback_attempts: int = 3
    health_check_interval: int = 60
    unhealthy_threshold: int = 3
    task_routing: Dict[str, str] = Field(default_factory=lambda: {
        "simple_qa": "economy",
        "complex_reasoning": "premium",
        "code_generation": "premium",
        "summarization": "economy",
    })


class ModelRouter(Capability):
    """Model routing capability."""
    
    name = "model_router"
    version = "1.0.0"
    description = "Intelligent model routing"
    
    def __init__(self, config: Optional[ModelRouterConfig] = None):
        super().__init__(config or ModelRouterConfig())
        self.config: ModelRouterConfig = self.config
        self._endpoints: Dict[str, ModelEndpoint] = {}
        self._round_robin_index: int = 0
        self._health_task: Optional[asyncio.Task] = None
    
    async def _do_initialize(self):
        """Initialize model router."""
        self._health_task = asyncio.create_task(self._health_loop())
        logger.info("Model router initialized")
    
    async def _do_shutdown(self):
        """Shutdown model router."""
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
    
    async def _health_loop(self):
        """Background health checking."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                for ep in self._endpoints.values():
                    ep.healthy = ep.consecutive_failures < self.config.unhealthy_threshold
            except asyncio.CancelledError:
                break
    
    async def register_endpoint(self, endpoint: ModelEndpoint) -> ModelEndpoint:
        """Register a model endpoint."""
        self._endpoints[endpoint.id] = endpoint
        logger.info(f"Registered endpoint: {endpoint.name}")
        return endpoint
    
    async def unregister_endpoint(self, endpoint_id: str) -> bool:
        """Unregister an endpoint."""
        if endpoint_id in self._endpoints:
            del self._endpoints[endpoint_id]
            return True
        return False
    
    async def get_endpoint(self, endpoint_id: str) -> Optional[ModelEndpoint]:
        """Get an endpoint by ID."""
        return self._endpoints.get(endpoint_id)
    
    async def list_endpoints(self, healthy_only: bool = False) -> List[ModelEndpoint]:
        """List all endpoints."""
        endpoints = list(self._endpoints.values())
        if healthy_only:
            endpoints = [e for e in endpoints if e.healthy and e.enabled]
        return endpoints
    
    async def route(
        self,
        task_type: Optional[TaskType] = None,
        strategy: Optional[RoutingStrategy] = None,
        required_tier: Optional[ModelTier] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> Optional[RoutingDecision]:
        """Route to the best model endpoint."""
        strategy = strategy or self.config.default_strategy
        exclude_ids = exclude_ids or []
        
        candidates = [
            e for e in self._endpoints.values()
            if e.enabled and e.healthy and e.id not in exclude_ids
        ]
        
        if required_tier:
            candidates = [e for e in candidates if e.tier == required_tier]
        
        if task_type:
            task_candidates = [e for e in candidates if task_type in e.supported_tasks]
            if task_candidates:
                candidates = task_candidates
        
        if not candidates:
            return None
        
        if strategy == RoutingStrategy.ROUND_ROBIN:
            endpoint = self._route_round_robin(candidates)
            reason = "Round robin selection"
        elif strategy == RoutingStrategy.LEAST_COST:
            endpoint = self._route_least_cost(candidates)
            reason = "Lowest cost model"
        elif strategy == RoutingStrategy.LEAST_LATENCY:
            endpoint = self._route_least_latency(candidates)
            reason = "Lowest latency model"
        elif strategy == RoutingStrategy.TASK_BASED:
            endpoint = self._route_task_based(candidates, task_type)
            reason = f"Best for {task_type.value if task_type else 'general'}"
        elif strategy == RoutingStrategy.RANDOM:
            endpoint = random.choice(candidates)
            reason = "Random selection"
        else:
            endpoint = candidates[0]
            reason = "Default selection"
        
        alternatives = [e.id for e in candidates if e.id != endpoint.id][:3]
        
        return RoutingDecision(
            endpoint=endpoint,
            reason=reason,
            alternatives=alternatives
        )
    
    def _route_round_robin(self, candidates: List[ModelEndpoint]) -> ModelEndpoint:
        """Round robin routing."""
        self._round_robin_index = (self._round_robin_index + 1) % len(candidates)
        return candidates[self._round_robin_index]
    
    def _route_least_cost(self, candidates: List[ModelEndpoint]) -> ModelEndpoint:
        """Route to cheapest model."""
        return min(candidates, key=lambda e: e.input_price + e.output_price)
    
    def _route_least_latency(self, candidates: List[ModelEndpoint]) -> ModelEndpoint:
        """Route to fastest model."""
        return min(candidates, key=lambda e: e.avg_latency_ms)
    
    def _route_task_based(
        self,
        candidates: List[ModelEndpoint],
        task_type: Optional[TaskType]
    ) -> ModelEndpoint:
        """Route based on task type."""
        if task_type:
            preferred_tier = self.config.task_routing.get(task_type.value)
            if preferred_tier:
                tier_candidates = [e for e in candidates if e.tier.value == preferred_tier]
                if tier_candidates:
                    return self._route_least_cost(tier_candidates)
        return self._route_least_cost(candidates)
    
    async def report_success(self, endpoint_id: str, latency_ms: float):
        """Report successful request."""
        if endpoint_id in self._endpoints:
            ep = self._endpoints[endpoint_id]
            ep.consecutive_failures = 0
            ep.avg_latency_ms = (ep.avg_latency_ms + latency_ms) / 2
    
    async def report_failure(self, endpoint_id: str):
        """Report failed request."""
        if endpoint_id in self._endpoints:
            self._endpoints[endpoint_id].consecutive_failures += 1
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get router stats."""
        healthy = sum(1 for e in self._endpoints.values() if e.healthy)
        return {
            "total_endpoints": len(self._endpoints),
            "healthy_endpoints": healthy,
            "default_strategy": self.config.default_strategy.value
        }
