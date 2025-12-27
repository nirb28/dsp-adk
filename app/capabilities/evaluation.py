"""
Evaluation Framework capability.

Provides automated evaluation, test suites, regression testing,
and quality metrics for agents.
"""
import logging
import uuid
import asyncio
import json
from typing import Optional, Dict, Any, List, Callable, Awaitable
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .base import Capability, CapabilityConfig

logger = logging.getLogger(__name__)


class EvalMetricType(str, Enum):
    """Types of evaluation metrics."""
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
    FLUENCY = "fluency"
    HELPFULNESS = "helpfulness"
    SAFETY = "safety"
    LATENCY = "latency"
    COST = "cost"
    CUSTOM = "custom"


class EvalStatus(str, Enum):
    """Evaluation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestCase(BaseModel):
    """A test case for evaluation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    
    # Input
    input_prompt: str
    input_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Expected output
    expected_output: Optional[str] = None
    expected_contains: List[str] = Field(default_factory=list)
    expected_not_contains: List[str] = Field(default_factory=list)
    
    # Grading
    grading_criteria: Optional[str] = None
    min_score: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # Tags
    tags: List[str] = Field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestResult(BaseModel):
    """Result of a single test case."""
    test_case_id: str
    test_case_name: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    
    # Outputs
    actual_output: str = ""
    
    # Metrics
    metrics: Dict[str, float] = Field(default_factory=dict)
    
    # Timing
    latency_ms: float = 0.0
    tokens_used: int = 0
    
    # Details
    details: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EvalResult(BaseModel):
    """Result of a full evaluation run."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: EvalStatus = EvalStatus.PENDING
    
    # Target
    agent_id: Optional[str] = None
    agent_version: Optional[str] = None
    
    # Results
    test_results: List[TestResult] = Field(default_factory=list)
    
    # Aggregate metrics
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    pass_rate: float = 0.0
    average_score: float = 0.0
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Cost
    total_tokens: int = 0
    estimated_cost: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def calculate_aggregates(self):
        """Calculate aggregate metrics."""
        if not self.test_results:
            return
        
        self.total_tests = len(self.test_results)
        self.passed_tests = sum(1 for r in self.test_results if r.passed)
        self.failed_tests = self.total_tests - self.passed_tests
        self.pass_rate = self.passed_tests / self.total_tests if self.total_tests else 0.0
        self.average_score = sum(r.score for r in self.test_results) / self.total_tests
        self.total_tokens = sum(r.tokens_used for r in self.test_results)


class TestSuite(BaseModel):
    """A collection of test cases."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    
    test_cases: List[TestCase] = Field(default_factory=list)
    
    # Configuration
    parallel: bool = Field(default=False, description="Run tests in parallel")
    stop_on_failure: bool = Field(default=False)
    timeout_seconds: int = Field(default=300)
    
    # Tags
    tags: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EvalConfig(CapabilityConfig):
    """Evaluation framework configuration."""
    # Default metrics
    default_metrics: List[EvalMetricType] = Field(
        default_factory=lambda: [
            EvalMetricType.RELEVANCE,
            EvalMetricType.COHERENCE,
            EvalMetricType.LATENCY
        ]
    )
    
    # LLM-as-judge
    judge_enabled: bool = Field(default=False, description="Use LLM as judge")
    judge_model: Optional[str] = Field(default=None)
    judge_endpoint: Optional[str] = Field(default=None)
    
    # Storage
    store_results: bool = Field(default=True)
    max_stored_results: int = Field(default=1000)
    
    # Defaults
    default_timeout: int = Field(default=60)
    max_concurrent_tests: int = Field(default=10)


class EvalFramework(Capability):
    """Evaluation framework capability."""
    
    name = "evaluation"
    version = "1.0.0"
    description = "Automated testing and evaluation framework"
    
    def __init__(self, config: Optional[EvalConfig] = None):
        super().__init__(config or EvalConfig())
        self.config: EvalConfig = self.config
        
        self._test_suites: Dict[str, TestSuite] = {}
        self._eval_results: Dict[str, EvalResult] = {}
        self._custom_metrics: Dict[str, Callable] = {}
        self._agent_executor: Optional[Callable] = None
    
    async def _do_initialize(self):
        """Initialize evaluation framework."""
        logger.info(f"Evaluation framework initialized (judge={self.config.judge_enabled})")
    
    def set_agent_executor(self, executor: Callable[[str, Dict[str, Any]], Awaitable[str]]):
        """Set the function to execute agent calls."""
        self._agent_executor = executor
    
    def register_metric(
        self,
        name: str,
        metric_fn: Callable[[str, str, TestCase], Awaitable[float]]
    ):
        """Register a custom metric function."""
        self._custom_metrics[name] = metric_fn
    
    # Test Suite Management
    async def create_test_suite(
        self,
        name: str,
        description: str = "",
        test_cases: Optional[List[TestCase]] = None,
        **kwargs
    ) -> TestSuite:
        """Create a test suite."""
        suite = TestSuite(
            name=name,
            description=description,
            test_cases=test_cases or [],
            **kwargs
        )
        self._test_suites[suite.id] = suite
        return suite
    
    async def get_test_suite(self, suite_id: str) -> Optional[TestSuite]:
        """Get a test suite by ID."""
        return self._test_suites.get(suite_id)
    
    async def add_test_case(self, suite_id: str, test_case: TestCase) -> bool:
        """Add a test case to a suite."""
        suite = self._test_suites.get(suite_id)
        if not suite:
            return False
        suite.test_cases.append(test_case)
        suite.updated_at = datetime.utcnow()
        return True
    
    async def list_test_suites(self) -> List[TestSuite]:
        """List all test suites."""
        return list(self._test_suites.values())
    
    # Evaluation Execution
    async def run_evaluation(
        self,
        suite_id: str,
        agent_id: Optional[str] = None,
        agent_version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvalResult:
        """Run evaluation on a test suite."""
        suite = self._test_suites.get(suite_id)
        if not suite:
            raise ValueError(f"Test suite {suite_id} not found")
        
        result = EvalResult(
            name=f"Eval: {suite.name}",
            agent_id=agent_id,
            agent_version=agent_version,
            status=EvalStatus.RUNNING,
            started_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        try:
            if suite.parallel:
                test_results = await self._run_parallel(suite)
            else:
                test_results = await self._run_sequential(suite)
            
            result.test_results = test_results
            result.calculate_aggregates()
            result.status = EvalStatus.COMPLETED
            
        except Exception as e:
            result.status = EvalStatus.FAILED
            result.metadata["error"] = str(e)
            logger.error(f"Evaluation failed: {e}")
        
        result.completed_at = datetime.utcnow()
        if result.started_at:
            result.duration_seconds = (result.completed_at - result.started_at).total_seconds()
        
        # Store result
        if self.config.store_results:
            self._eval_results[result.id] = result
            await self._enforce_storage_limit()
        
        return result
    
    async def _run_sequential(self, suite: TestSuite) -> List[TestResult]:
        """Run tests sequentially."""
        results = []
        for test_case in suite.test_cases:
            result = await self._run_test_case(test_case, suite.timeout_seconds)
            results.append(result)
            if suite.stop_on_failure and not result.passed:
                break
        return results
    
    async def _run_parallel(self, suite: TestSuite) -> List[TestResult]:
        """Run tests in parallel."""
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tests)
        
        async def run_with_semaphore(test_case: TestCase) -> TestResult:
            async with semaphore:
                return await self._run_test_case(test_case, suite.timeout_seconds)
        
        tasks = [run_with_semaphore(tc) for tc in suite.test_cases]
        return await asyncio.gather(*tasks)
    
    async def _run_test_case(self, test_case: TestCase, timeout: int) -> TestResult:
        """Run a single test case."""
        start_time = datetime.utcnow()
        
        result = TestResult(
            test_case_id=test_case.id,
            test_case_name=test_case.name,
            passed=False,
            score=0.0
        )
        
        try:
            # Execute agent
            if self._agent_executor:
                actual_output = await asyncio.wait_for(
                    self._agent_executor(test_case.input_prompt, test_case.input_context),
                    timeout=timeout
                )
            else:
                actual_output = f"[Mock output for: {test_case.input_prompt[:50]}...]"
            
            result.actual_output = actual_output
            
            # Calculate metrics
            metrics = await self._calculate_metrics(test_case, actual_output)
            result.metrics = metrics
            
            # Calculate overall score
            result.score = await self._calculate_score(test_case, actual_output, metrics)
            result.passed = result.score >= test_case.min_score
            
        except asyncio.TimeoutError:
            result.error = "Test timed out"
        except Exception as e:
            result.error = str(e)
        
        # Calculate latency
        result.latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return result
    
    async def _calculate_metrics(self, test_case: TestCase, output: str) -> Dict[str, float]:
        """Calculate evaluation metrics."""
        metrics = {}
        
        for metric_type in self.config.default_metrics:
            if metric_type == EvalMetricType.LATENCY:
                continue  # Handled separately
            
            metric_value = await self._calculate_metric(metric_type, test_case, output)
            metrics[metric_type.value] = metric_value
        
        # Custom metrics
        for name, metric_fn in self._custom_metrics.items():
            try:
                metrics[name] = await metric_fn(output, test_case.expected_output or "", test_case)
            except Exception as e:
                logger.warning(f"Custom metric {name} failed: {e}")
        
        return metrics
    
    async def _calculate_metric(
        self, 
        metric_type: EvalMetricType, 
        test_case: TestCase, 
        output: str
    ) -> float:
        """Calculate a single metric."""
        if metric_type == EvalMetricType.RELEVANCE:
            return self._relevance_score(test_case, output)
        elif metric_type == EvalMetricType.COHERENCE:
            return self._coherence_score(output)
        elif metric_type == EvalMetricType.FLUENCY:
            return self._fluency_score(output)
        elif metric_type == EvalMetricType.SAFETY:
            return self._safety_score(output)
        else:
            return 0.5  # Default neutral score
    
    def _relevance_score(self, test_case: TestCase, output: str) -> float:
        """Calculate relevance score."""
        score = 0.5
        output_lower = output.lower()
        
        # Check expected contains
        if test_case.expected_contains:
            matches = sum(1 for kw in test_case.expected_contains if kw.lower() in output_lower)
            score = matches / len(test_case.expected_contains)
        
        # Penalize for expected_not_contains
        if test_case.expected_not_contains:
            violations = sum(1 for kw in test_case.expected_not_contains if kw.lower() in output_lower)
            penalty = violations / len(test_case.expected_not_contains)
            score = max(0, score - penalty * 0.5)
        
        # Check against expected output
        if test_case.expected_output:
            expected_words = set(test_case.expected_output.lower().split())
            output_words = set(output_lower.split())
            overlap = len(expected_words & output_words)
            if expected_words:
                score = (score + overlap / len(expected_words)) / 2
        
        return min(1.0, max(0.0, score))
    
    def _coherence_score(self, output: str) -> float:
        """Calculate coherence score based on structure."""
        if not output.strip():
            return 0.0
        
        # Simple heuristics
        score = 0.5
        
        # Has proper sentences
        sentences = [s.strip() for s in output.split('.') if s.strip()]
        if len(sentences) > 0:
            score += 0.2
        
        # Not too short
        if len(output) > 50:
            score += 0.1
        
        # Not too repetitive
        words = output.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            score += unique_ratio * 0.2
        
        return min(1.0, score)
    
    def _fluency_score(self, output: str) -> float:
        """Calculate fluency score."""
        if not output.strip():
            return 0.0
        
        # Simple heuristics for fluency
        score = 0.7  # Base score
        
        # Penalize excessive punctuation
        punct_ratio = sum(1 for c in output if c in '!?...') / len(output)
        if punct_ratio > 0.05:
            score -= 0.2
        
        # Check for complete sentences (ends with punctuation)
        if output.strip()[-1] in '.!?':
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _safety_score(self, output: str) -> float:
        """Calculate safety score."""
        # Simple keyword-based safety check
        unsafe_patterns = [
            'kill', 'harm', 'illegal', 'dangerous',
            'hate', 'discriminate'
        ]
        
        output_lower = output.lower()
        violations = sum(1 for p in unsafe_patterns if p in output_lower)
        
        if violations == 0:
            return 1.0
        elif violations <= 2:
            return 0.5
        else:
            return 0.0
    
    async def _calculate_score(
        self, 
        test_case: TestCase, 
        output: str, 
        metrics: Dict[str, float]
    ) -> float:
        """Calculate overall score."""
        if not metrics:
            return 0.5
        
        # Simple average of all metrics
        return sum(metrics.values()) / len(metrics)
    
    async def _enforce_storage_limit(self):
        """Enforce storage limit for results."""
        if len(self._eval_results) > self.config.max_stored_results:
            # Remove oldest results
            sorted_results = sorted(
                self._eval_results.items(),
                key=lambda x: x[1].completed_at or datetime.min
            )
            to_remove = len(self._eval_results) - self.config.max_stored_results
            for rid, _ in sorted_results[:to_remove]:
                del self._eval_results[rid]
    
    # Results Management
    async def get_eval_result(self, result_id: str) -> Optional[EvalResult]:
        """Get an evaluation result."""
        return self._eval_results.get(result_id)
    
    async def list_eval_results(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[EvalResult]:
        """List evaluation results."""
        results = list(self._eval_results.values())
        
        if agent_id:
            results = [r for r in results if r.agent_id == agent_id]
        
        results.sort(key=lambda r: r.completed_at or datetime.min, reverse=True)
        return results[:limit]
    
    async def compare_results(
        self,
        result_id_1: str,
        result_id_2: str
    ) -> Dict[str, Any]:
        """Compare two evaluation results."""
        r1 = self._eval_results.get(result_id_1)
        r2 = self._eval_results.get(result_id_2)
        
        if not r1 or not r2:
            return {"error": "One or both results not found"}
        
        return {
            "result_1": {"id": r1.id, "pass_rate": r1.pass_rate, "avg_score": r1.average_score},
            "result_2": {"id": r2.id, "pass_rate": r2.pass_rate, "avg_score": r2.average_score},
            "comparison": {
                "pass_rate_diff": r2.pass_rate - r1.pass_rate,
                "avg_score_diff": r2.average_score - r1.average_score,
                "improved": r2.average_score > r1.average_score
            }
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics."""
        total_evals = len(self._eval_results)
        total_tests = sum(r.total_tests for r in self._eval_results.values())
        avg_pass_rate = (
            sum(r.pass_rate for r in self._eval_results.values()) / total_evals
            if total_evals else 0
        )
        
        return {
            "total_evaluations": total_evals,
            "total_test_cases": total_tests,
            "average_pass_rate": avg_pass_rate,
            "test_suites": len(self._test_suites),
            "custom_metrics": list(self._custom_metrics.keys())
        }
