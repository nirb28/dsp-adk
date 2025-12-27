"""
Cost Tracking capability.

Tracks token usage, estimated costs, and provides budgeting controls.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
from collections import defaultdict

from .base import Capability, CapabilityConfig

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    """Types of tokens."""
    INPUT = "input"
    OUTPUT = "output"
    EMBEDDING = "embedding"


class UsageRecord(BaseModel):
    """A usage record."""
    id: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Identifiers
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    model: str = "unknown"
    
    # Token counts
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    # Cost
    estimated_cost: float = 0.0
    
    # Context
    request_type: str = "chat"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UsageStats(BaseModel):
    """Aggregated usage statistics."""
    period_start: datetime
    period_end: datetime
    
    # Totals
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    
    # Breakdowns
    by_model: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    by_user: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    by_agent: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Averages
    avg_tokens_per_request: float = 0.0
    avg_cost_per_request: float = 0.0


class Budget(BaseModel):
    """A budget configuration."""
    id: str
    name: str
    
    # Limits
    max_tokens: Optional[int] = None
    max_cost: Optional[float] = None
    max_requests: Optional[int] = None
    
    # Scope
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    # Period
    period: str = "daily"  # daily, weekly, monthly, total
    
    # Current usage
    current_tokens: int = 0
    current_cost: float = 0.0
    current_requests: int = 0
    
    # Reset tracking
    period_start: datetime = Field(default_factory=datetime.utcnow)
    
    # Actions
    action_on_limit: str = "block"  # block, warn, log
    
    def is_exceeded(self) -> bool:
        """Check if budget is exceeded."""
        if self.max_tokens and self.current_tokens >= self.max_tokens:
            return True
        if self.max_cost and self.current_cost >= self.max_cost:
            return True
        if self.max_requests and self.current_requests >= self.max_requests:
            return True
        return False
    
    def usage_percentage(self) -> Dict[str, float]:
        """Get usage percentage for each limit."""
        percentages = {}
        if self.max_tokens:
            percentages["tokens"] = (self.current_tokens / self.max_tokens) * 100
        if self.max_cost:
            percentages["cost"] = (self.current_cost / self.max_cost) * 100
        if self.max_requests:
            percentages["requests"] = (self.current_requests / self.max_requests) * 100
        return percentages


class CostConfig(CapabilityConfig):
    """Cost tracking configuration."""
    # Model pricing (per 1K tokens)
    model_pricing: Dict[str, Dict[str, float]] = Field(
        default_factory=lambda: {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "llama-3-70b": {"input": 0.001, "output": 0.001},
            "llama-3-8b": {"input": 0.0001, "output": 0.0001},
            "default": {"input": 0.001, "output": 0.002}
        }
    )
    
    # Storage
    retention_days: int = Field(default=30, description="Days to retain usage records")
    max_records: int = Field(default=100000, description="Max records to store")
    
    # Budgets
    default_daily_budget: Optional[float] = None
    enforce_budgets: bool = Field(default=True)


class CostTracker(Capability):
    """Cost tracking capability."""
    
    name = "cost_tracking"
    version = "1.0.0"
    description = "Token usage and cost tracking"
    
    def __init__(self, config: Optional[CostConfig] = None):
        super().__init__(config or CostConfig())
        self.config: CostConfig = self.config
        
        self._records: List[UsageRecord] = []
        self._budgets: Dict[str, Budget] = {}
    
    async def _do_initialize(self):
        """Initialize cost tracker."""
        logger.info("Cost tracker initialized")
    
    def get_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing for a model."""
        # Normalize model name
        model_lower = model.lower()
        
        for model_key, pricing in self.config.model_pricing.items():
            if model_key in model_lower:
                return pricing
        
        return self.config.model_pricing.get("default", {"input": 0.001, "output": 0.002})
    
    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for token usage."""
        pricing = self.get_pricing(model)
        input_cost = (input_tokens / 1000) * pricing.get("input", 0)
        output_cost = (output_tokens / 1000) * pricing.get("output", 0)
        return round(input_cost + output_cost, 6)
    
    async def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        request_type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageRecord:
        """Record token usage."""
        total_tokens = input_tokens + output_tokens
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        record = UsageRecord(
            user_id=user_id,
            session_id=session_id,
            agent_id=agent_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            request_type=request_type,
            metadata=metadata or {}
        )
        
        self._records.append(record)
        
        # Update budgets
        await self._update_budgets(record)
        
        # Enforce storage limits
        await self._enforce_retention()
        
        logger.debug(f"Recorded usage: {total_tokens} tokens, ${cost:.6f}")
        return record
    
    async def _update_budgets(self, record: UsageRecord):
        """Update relevant budgets."""
        for budget in self._budgets.values():
            # Check if budget applies
            if budget.user_id and budget.user_id != record.user_id:
                continue
            if budget.agent_id and budget.agent_id != record.agent_id:
                continue
            
            # Check if period needs reset
            await self._check_budget_reset(budget)
            
            # Update usage
            budget.current_tokens += record.total_tokens
            budget.current_cost += record.estimated_cost
            budget.current_requests += 1
    
    async def _check_budget_reset(self, budget: Budget):
        """Check if budget period should reset."""
        now = datetime.utcnow()
        reset = False
        
        if budget.period == "daily":
            if (now - budget.period_start).days >= 1:
                reset = True
        elif budget.period == "weekly":
            if (now - budget.period_start).days >= 7:
                reset = True
        elif budget.period == "monthly":
            if (now - budget.period_start).days >= 30:
                reset = True
        
        if reset:
            budget.current_tokens = 0
            budget.current_cost = 0.0
            budget.current_requests = 0
            budget.period_start = now
    
    async def _enforce_retention(self):
        """Enforce retention policy."""
        # Remove old records
        cutoff = datetime.utcnow() - timedelta(days=self.config.retention_days)
        self._records = [r for r in self._records if r.timestamp >= cutoff]
        
        # Enforce max records
        if len(self._records) > self.config.max_records:
            self._records = self._records[-self.config.max_records:]
    
    async def check_budget(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        estimated_tokens: int = 0
    ) -> Dict[str, Any]:
        """Check if usage is within budget."""
        results = {
            "allowed": True,
            "warnings": [],
            "exceeded_budgets": []
        }
        
        if not self.config.enforce_budgets:
            return results
        
        for budget in self._budgets.values():
            # Check if budget applies
            if budget.user_id and budget.user_id != user_id:
                continue
            if budget.agent_id and budget.agent_id != agent_id:
                continue
            
            # Check if would exceed
            await self._check_budget_reset(budget)
            
            projected_tokens = budget.current_tokens + estimated_tokens
            if budget.max_tokens and projected_tokens > budget.max_tokens:
                if budget.action_on_limit == "block":
                    results["allowed"] = False
                    results["exceeded_budgets"].append(budget.id)
                elif budget.action_on_limit == "warn":
                    results["warnings"].append(f"Budget '{budget.name}' token limit approaching")
            
            # Check usage percentage
            usage = budget.usage_percentage()
            for limit_type, pct in usage.items():
                if pct >= 80:
                    results["warnings"].append(f"Budget '{budget.name}' {limit_type} at {pct:.1f}%")
        
        return results
    
    # Budget Management
    async def create_budget(
        self,
        name: str,
        max_tokens: Optional[int] = None,
        max_cost: Optional[float] = None,
        max_requests: Optional[int] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        period: str = "daily",
        action_on_limit: str = "block"
    ) -> Budget:
        """Create a budget."""
        budget_id = f"{user_id or 'global'}_{agent_id or 'all'}_{period}"
        
        budget = Budget(
            id=budget_id,
            name=name,
            max_tokens=max_tokens,
            max_cost=max_cost,
            max_requests=max_requests,
            user_id=user_id,
            agent_id=agent_id,
            period=period,
            action_on_limit=action_on_limit
        )
        
        self._budgets[budget_id] = budget
        return budget
    
    async def get_budget(self, budget_id: str) -> Optional[Budget]:
        """Get a budget."""
        return self._budgets.get(budget_id)
    
    async def list_budgets(self) -> List[Budget]:
        """List all budgets."""
        return list(self._budgets.values())
    
    async def delete_budget(self, budget_id: str) -> bool:
        """Delete a budget."""
        if budget_id in self._budgets:
            del self._budgets[budget_id]
            return True
        return False
    
    # Statistics
    async def get_usage_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> UsageStats:
        """Get aggregated usage statistics."""
        end_date = end_date or datetime.utcnow()
        start_date = start_date or (end_date - timedelta(days=7))
        
        # Filter records
        records = [
            r for r in self._records
            if start_date <= r.timestamp <= end_date
        ]
        
        if user_id:
            records = [r for r in records if r.user_id == user_id]
        if agent_id:
            records = [r for r in records if r.agent_id == agent_id]
        
        stats = UsageStats(period_start=start_date, period_end=end_date)
        
        if not records:
            return stats
        
        # Calculate totals
        stats.total_requests = len(records)
        stats.total_input_tokens = sum(r.input_tokens for r in records)
        stats.total_output_tokens = sum(r.output_tokens for r in records)
        stats.total_tokens = sum(r.total_tokens for r in records)
        stats.total_cost = sum(r.estimated_cost for r in records)
        
        # Calculate averages
        stats.avg_tokens_per_request = stats.total_tokens / stats.total_requests
        stats.avg_cost_per_request = stats.total_cost / stats.total_requests
        
        # Group by model
        by_model = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        for r in records:
            by_model[r.model]["requests"] += 1
            by_model[r.model]["tokens"] += r.total_tokens
            by_model[r.model]["cost"] += r.estimated_cost
        stats.by_model = dict(by_model)
        
        # Group by user
        by_user = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        for r in records:
            if r.user_id:
                by_user[r.user_id]["requests"] += 1
                by_user[r.user_id]["tokens"] += r.total_tokens
                by_user[r.user_id]["cost"] += r.estimated_cost
        stats.by_user = dict(by_user)
        
        # Group by agent
        by_agent = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        for r in records:
            if r.agent_id:
                by_agent[r.agent_id]["requests"] += 1
                by_agent[r.agent_id]["tokens"] += r.total_tokens
                by_agent[r.agent_id]["cost"] += r.estimated_cost
        stats.by_agent = dict(by_agent)
        
        return stats
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cost tracking stats."""
        total_cost = sum(r.estimated_cost for r in self._records)
        total_tokens = sum(r.total_tokens for r in self._records)
        
        return {
            "total_records": len(self._records),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "budgets_count": len(self._budgets),
            "retention_days": self.config.retention_days
        }
