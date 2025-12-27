"""
Advanced Graph Features capability.

Provides parallel execution, conditional branching, loops,
human-in-the-loop, and checkpointing for agent graphs.
"""
import logging
import asyncio
import uuid
from typing import Optional, Dict, Any, List, Callable, Awaitable, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from collections import deque

from .base import Capability, CapabilityConfig

logger = logging.getLogger(__name__)


class NodeStatus(str, Enum):
    """Status of a graph node execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_INPUT = "waiting_input"


class ExecutionMode(str, Enum):
    """Graph execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class GraphNode(BaseModel):
    """A node in the execution graph."""
    id: str
    name: str
    node_type: str = "action"  # action, condition, input, output, parallel, loop
    
    # Execution
    handler: Optional[str] = None  # Handler function name
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Flow control
    next_nodes: List[str] = Field(default_factory=list)
    condition: Optional[str] = None  # Condition expression
    true_branch: Optional[str] = None
    false_branch: Optional[str] = None
    
    # Parallel execution
    parallel_nodes: List[str] = Field(default_factory=list)
    join_node: Optional[str] = None
    
    # Loop control
    loop_condition: Optional[str] = None
    max_iterations: int = Field(default=10)
    loop_body: List[str] = Field(default_factory=list)
    
    # Human-in-the-loop
    requires_approval: bool = False
    approval_prompt: Optional[str] = None
    timeout_seconds: int = Field(default=300)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeExecution(BaseModel):
    """Record of a node execution."""
    node_id: str
    node_name: str
    status: NodeStatus = NodeStatus.PENDING
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    
    # Results
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    
    # Loop tracking
    iteration: int = 0


class GraphExecution(BaseModel):
    """Record of a full graph execution."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    graph_id: str
    status: NodeStatus = NodeStatus.PENDING
    
    # Nodes
    node_executions: Dict[str, NodeExecution] = Field(default_factory=dict)
    
    # State
    state: Dict[str, Any] = Field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Human-in-the-loop
    pending_approvals: List[str] = Field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Checkpoint(BaseModel):
    """A checkpoint for graph execution."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    node_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    state: Dict[str, Any] = Field(default_factory=dict)
    node_executions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class HumanInputRequest(BaseModel):
    """Request for human input."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    node_id: str
    prompt: str
    options: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    timeout_seconds: int = 300
    response: Optional[str] = None
    responded_at: Optional[datetime] = None


class AdvancedGraphConfig(CapabilityConfig):
    """Advanced graph configuration."""
    max_parallel_nodes: int = Field(default=10)
    max_loop_iterations: int = Field(default=100)
    default_timeout: int = Field(default=60)
    enable_checkpointing: bool = Field(default=True)
    checkpoint_interval: int = Field(default=5)  # Checkpoint every N nodes
    human_input_timeout: int = Field(default=300)


class AdvancedGraphExecutor(Capability):
    """Advanced graph execution capability."""
    
    name = "advanced_graph"
    version = "1.0.0"
    description = "Advanced graph execution with parallel, loops, and human-in-loop"
    
    def __init__(self, config: Optional[AdvancedGraphConfig] = None):
        super().__init__(config or AdvancedGraphConfig())
        self.config: AdvancedGraphConfig = self.config
        
        self._graphs: Dict[str, Dict[str, GraphNode]] = {}
        self._executions: Dict[str, GraphExecution] = {}
        self._checkpoints: Dict[str, List[Checkpoint]] = {}
        self._pending_inputs: Dict[str, HumanInputRequest] = {}
        self._handlers: Dict[str, Callable] = {}
    
    async def _do_initialize(self):
        """Initialize graph executor."""
        logger.info("Advanced graph executor initialized")
    
    def register_handler(
        self,
        name: str,
        handler: Callable[[Dict[str, Any], Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ):
        """Register a node handler function."""
        self._handlers[name] = handler
    
    # Graph Management
    async def register_graph(
        self,
        graph_id: str,
        nodes: List[GraphNode]
    ) -> bool:
        """Register a graph definition."""
        self._graphs[graph_id] = {node.id: node for node in nodes}
        logger.info(f"Registered graph: {graph_id} with {len(nodes)} nodes")
        return True
    
    async def get_graph(self, graph_id: str) -> Optional[Dict[str, GraphNode]]:
        """Get a graph definition."""
        return self._graphs.get(graph_id)
    
    # Execution
    async def execute(
        self,
        graph_id: str,
        initial_state: Optional[Dict[str, Any]] = None,
        start_node: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GraphExecution:
        """Execute a graph."""
        if graph_id not in self._graphs:
            raise ValueError(f"Graph {graph_id} not found")
        
        graph = self._graphs[graph_id]
        
        execution = GraphExecution(
            graph_id=graph_id,
            status=NodeStatus.RUNNING,
            state=initial_state or {},
            started_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        self._executions[execution.id] = execution
        
        # Find start node
        if start_node:
            current_node = start_node
        else:
            # Find node with no incoming edges
            all_next = set()
            for node in graph.values():
                all_next.update(node.next_nodes)
                all_next.update(node.parallel_nodes)
            current_node = next(
                (n.id for n in graph.values() if n.id not in all_next),
                list(graph.keys())[0]
            )
        
        try:
            await self._execute_from_node(execution, graph, current_node)
            execution.status = NodeStatus.COMPLETED
        except Exception as e:
            execution.status = NodeStatus.FAILED
            logger.error(f"Graph execution failed: {e}")
        
        execution.completed_at = datetime.utcnow()
        return execution
    
    async def _execute_from_node(
        self,
        execution: GraphExecution,
        graph: Dict[str, GraphNode],
        node_id: str,
        iteration: int = 0
    ):
        """Execute from a specific node."""
        if node_id not in graph:
            return
        
        node = graph[node_id]
        
        # Check for pending approvals
        if node.requires_approval:
            await self._request_human_input(execution, node)
            if execution.status == NodeStatus.WAITING_INPUT:
                return
        
        # Execute based on node type
        if node.node_type == "parallel":
            await self._execute_parallel(execution, graph, node)
        elif node.node_type == "condition":
            await self._execute_condition(execution, graph, node)
        elif node.node_type == "loop":
            await self._execute_loop(execution, graph, node)
        else:
            await self._execute_action(execution, node, iteration)
        
        # Checkpoint if needed
        if self.config.enable_checkpointing:
            completed_count = sum(
                1 for ne in execution.node_executions.values()
                if ne.status == NodeStatus.COMPLETED
            )
            if completed_count % self.config.checkpoint_interval == 0:
                await self._create_checkpoint(execution, node_id)
        
        # Continue to next nodes
        for next_id in node.next_nodes:
            await self._execute_from_node(execution, graph, next_id)
    
    async def _execute_action(
        self,
        execution: GraphExecution,
        node: GraphNode,
        iteration: int = 0
    ):
        """Execute an action node."""
        node_exec = NodeExecution(
            node_id=node.id,
            node_name=node.name,
            status=NodeStatus.RUNNING,
            started_at=datetime.utcnow(),
            input_data=dict(execution.state),
            iteration=iteration
        )
        execution.node_executions[node.id] = node_exec
        
        try:
            if node.handler and node.handler in self._handlers:
                handler = self._handlers[node.handler]
                result = await asyncio.wait_for(
                    handler(execution.state, node.config),
                    timeout=self.config.default_timeout
                )
                node_exec.output_data = result
                execution.state.update(result)
            else:
                # Mock execution
                node_exec.output_data = {"mock": f"Executed {node.name}"}
            
            node_exec.status = NodeStatus.COMPLETED
        except asyncio.TimeoutError:
            node_exec.status = NodeStatus.FAILED
            node_exec.error = "Timeout"
        except Exception as e:
            node_exec.status = NodeStatus.FAILED
            node_exec.error = str(e)
        
        node_exec.completed_at = datetime.utcnow()
        if node_exec.started_at:
            node_exec.duration_ms = (
                node_exec.completed_at - node_exec.started_at
            ).total_seconds() * 1000
    
    async def _execute_parallel(
        self,
        execution: GraphExecution,
        graph: Dict[str, GraphNode],
        node: GraphNode
    ):
        """Execute nodes in parallel."""
        semaphore = asyncio.Semaphore(self.config.max_parallel_nodes)
        
        async def run_with_semaphore(n_id: str):
            async with semaphore:
                if n_id in graph:
                    await self._execute_action(execution, graph[n_id])
        
        tasks = [run_with_semaphore(n_id) for n_id in node.parallel_nodes]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Continue to join node if specified
        if node.join_node:
            await self._execute_from_node(execution, graph, node.join_node)
    
    async def _execute_condition(
        self,
        execution: GraphExecution,
        graph: Dict[str, GraphNode],
        node: GraphNode
    ):
        """Execute a conditional branch."""
        # Evaluate condition
        result = False
        if node.condition:
            try:
                result = eval(node.condition, {"state": execution.state})
            except Exception as e:
                logger.warning(f"Condition evaluation failed: {e}")
        
        # Record execution
        node_exec = NodeExecution(
            node_id=node.id,
            node_name=node.name,
            status=NodeStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            output_data={"condition_result": result}
        )
        execution.node_executions[node.id] = node_exec
        
        # Follow appropriate branch
        next_node = node.true_branch if result else node.false_branch
        if next_node:
            await self._execute_from_node(execution, graph, next_node)
    
    async def _execute_loop(
        self,
        execution: GraphExecution,
        graph: Dict[str, GraphNode],
        node: GraphNode
    ):
        """Execute a loop."""
        max_iter = min(node.max_iterations, self.config.max_loop_iterations)
        
        for i in range(max_iter):
            # Check loop condition
            if node.loop_condition:
                try:
                    should_continue = eval(
                        node.loop_condition,
                        {"state": execution.state, "iteration": i}
                    )
                    if not should_continue:
                        break
                except Exception:
                    break
            
            # Execute loop body
            for body_node_id in node.loop_body:
                if body_node_id in graph:
                    await self._execute_action(execution, graph[body_node_id], i)
    
    async def _request_human_input(
        self,
        execution: GraphExecution,
        node: GraphNode
    ):
        """Request human input for a node."""
        request = HumanInputRequest(
            execution_id=execution.id,
            node_id=node.id,
            prompt=node.approval_prompt or f"Approve execution of {node.name}?",
            options=["approve", "reject"],
            timeout_seconds=node.timeout_seconds
        )
        
        self._pending_inputs[request.id] = request
        execution.pending_approvals.append(request.id)
        execution.status = NodeStatus.WAITING_INPUT
        
        logger.info(f"Waiting for human input: {request.id}")
    
    async def provide_input(
        self,
        request_id: str,
        response: str
    ) -> bool:
        """Provide human input for a pending request."""
        if request_id not in self._pending_inputs:
            return False
        
        request = self._pending_inputs[request_id]
        request.response = response
        request.responded_at = datetime.utcnow()
        
        # Resume execution if approved
        if response == "approve":
            execution = self._executions.get(request.execution_id)
            if execution:
                execution.pending_approvals.remove(request_id)
                if not execution.pending_approvals:
                    execution.status = NodeStatus.RUNNING
        
        del self._pending_inputs[request_id]
        return True
    
    async def get_pending_inputs(
        self,
        execution_id: Optional[str] = None
    ) -> List[HumanInputRequest]:
        """Get pending human input requests."""
        requests = list(self._pending_inputs.values())
        if execution_id:
            requests = [r for r in requests if r.execution_id == execution_id]
        return requests
    
    # Checkpointing
    async def _create_checkpoint(
        self,
        execution: GraphExecution,
        node_id: str
    ):
        """Create a checkpoint."""
        checkpoint = Checkpoint(
            execution_id=execution.id,
            node_id=node_id,
            state=dict(execution.state),
            node_executions={
                k: v.model_dump() for k, v in execution.node_executions.items()
            }
        )
        
        if execution.id not in self._checkpoints:
            self._checkpoints[execution.id] = []
        self._checkpoints[execution.id].append(checkpoint)
        
        execution.checkpoints.append({
            "id": checkpoint.id,
            "node_id": node_id,
            "timestamp": checkpoint.timestamp.isoformat()
        })
    
    async def restore_from_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[GraphExecution]:
        """Restore execution from a checkpoint."""
        for exec_id, checkpoints in self._checkpoints.items():
            for cp in checkpoints:
                if cp.id == checkpoint_id:
                    execution = self._executions.get(exec_id)
                    if execution:
                        execution.state = dict(cp.state)
                        execution.node_executions = {
                            k: NodeExecution(**v) 
                            for k, v in cp.node_executions.items()
                        }
                        return execution
        return None
    
    async def get_checkpoints(
        self,
        execution_id: str
    ) -> List[Checkpoint]:
        """Get checkpoints for an execution."""
        return self._checkpoints.get(execution_id, [])
    
    # Execution Management
    async def get_execution(self, execution_id: str) -> Optional[GraphExecution]:
        """Get an execution by ID."""
        return self._executions.get(execution_id)
    
    async def list_executions(
        self,
        graph_id: Optional[str] = None,
        limit: int = 100
    ) -> List[GraphExecution]:
        """List executions."""
        executions = list(self._executions.values())
        if graph_id:
            executions = [e for e in executions if e.graph_id == graph_id]
        return executions[:limit]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get executor stats."""
        return {
            "registered_graphs": len(self._graphs),
            "total_executions": len(self._executions),
            "pending_inputs": len(self._pending_inputs),
            "registered_handlers": list(self._handlers.keys())
        }
