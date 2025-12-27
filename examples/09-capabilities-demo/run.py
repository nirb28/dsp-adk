#!/usr/bin/env python
"""
Example 09: Capabilities Demo

Demonstrates the ADK modular capability system including:
- Session Management
- Memory (short-term, long-term)
- Streaming Support
- Guardrails (PII detection, content filtering)
- Cost Tracking
- Rate Limiting
- Model Router
"""
import asyncio
import sys
from pathlib import Path

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.capabilities import (
    # Base
    CapabilityRegistry,
    # Sessions
    SessionManager, SessionConfig,
    # Memory
    MemoryManager, MemoryConfig, MemoryScope,
    # Streaming
    StreamingManager, StreamConfig,
    # Guardrails
    GuardrailsManager, GuardrailConfig,
    # Cost Tracking
    CostTracker, CostConfig,
    # Rate Limiting
    RateLimiter, RateLimitConfig,
    # Model Router
    ModelRouter, ModelRouterConfig, RoutingStrategy,
    # Advanced Graph
    AdvancedGraphExecutor, AdvancedGraphConfig, GraphNode,
)


async def demo_sessions():
    """Demonstrate session management."""
    print("\n" + "="*60)
    print("SESSION MANAGEMENT DEMO")
    print("="*60)
    
    manager = SessionManager(SessionConfig(
        default_ttl_minutes=30,
        max_messages=50
    ))
    await manager.initialize()
    
    # Create a session
    session = await manager.create_session(user_id="user123")
    print(f"Created session: {session.id}")
    
    # Add messages
    await manager.add_message(session.id, "user", "Hello, how are you?")
    await manager.add_message(session.id, "assistant", "I'm doing well, thanks!")
    await manager.add_message(session.id, "user", "What's the weather like?")
    
    # Get history
    history = await manager.get_history(session.id)
    print(f"Session has {len(history)} messages")
    
    # Update state
    await manager.update_state(session.id, {"topic": "weather", "mood": "friendly"})
    
    # Get session info
    session = await manager.get_session(session.id)
    print(f"Session state: {session.state}")
    
    # Stats
    stats = await manager.get_stats()
    print(f"Session stats: {stats}")
    
    await manager.shutdown()


async def demo_memory():
    """Demonstrate memory management."""
    print("\n" + "="*60)
    print("MEMORY MANAGEMENT DEMO")
    print("="*60)
    
    manager = MemoryManager(MemoryConfig(
        default_scope=MemoryScope.SESSION,
        max_memories=100
    ))
    await manager.initialize()
    
    # Store memories in different scopes
    await manager.store(
        key="user_preference",
        value={"theme": "dark", "language": "en"},
        scope=MemoryScope.USER,
        scope_id="user123"
    )
    
    await manager.store(
        key="conversation_context",
        value="Discussing weather patterns",
        scope=MemoryScope.SESSION,
        scope_id="session456"
    )
    
    await manager.store(
        key="agent_knowledge",
        value="User prefers concise answers",
        scope=MemoryScope.AGENT,
        scope_id="agent789"
    )
    
    # Retrieve memories
    pref = await manager.retrieve("user_preference", MemoryScope.USER, "user123")
    print(f"User preference: {pref}")
    
    # List memories for a scope
    memories = await manager.list_memories(MemoryScope.USER, "user123")
    print(f"User memories: {len(memories)}")
    
    # Stats
    stats = await manager.get_stats()
    print(f"Memory stats: {stats}")
    
    await manager.shutdown()


async def demo_streaming():
    """Demonstrate streaming support."""
    print("\n" + "="*60)
    print("STREAMING SUPPORT DEMO")
    print("="*60)
    
    manager = StreamingManager(StreamConfig(chunk_size=50))
    await manager.initialize()
    
    # Create a stream
    stream = await manager.create_stream(
        stream_id="stream123",
        metadata={"agent": "demo-agent"}
    )
    print(f"Created stream: {stream.id}")
    
    # Add event listener
    events_received = []
    async def on_event(event):
        events_received.append(event)
    
    await manager.add_listener(stream.id, on_event)
    
    # Simulate streaming tokens
    response = "Hello! I'm streaming this response token by token."
    for word in response.split():
        await manager.emit_token(stream.id, word + " ")
        await asyncio.sleep(0.05)  # Simulate delay
    
    # Complete stream
    await manager.complete_stream(stream.id)
    
    print(f"Streamed {len(events_received)} events")
    
    # Stats
    stats = await manager.get_stats()
    print(f"Streaming stats: {stats}")
    
    await manager.shutdown()


async def demo_guardrails():
    """Demonstrate guardrails."""
    print("\n" + "="*60)
    print("GUARDRAILS DEMO")
    print("="*60)
    
    manager = GuardrailsManager(GuardrailConfig(
        pii_detection=True,
        content_filtering=True,
        max_input_length=1000
    ))
    await manager.initialize()
    
    # Test inputs
    test_inputs = [
        "What's the weather like today?",
        "My email is john@example.com and phone is 555-123-4567",
        "My SSN is 123-45-6789",
        "A" * 2000,  # Too long
    ]
    
    for text in test_inputs:
        result = await manager.check_input(text[:50] + "..." if len(text) > 50 else text)
        status = "PASSED" if result.passed else "BLOCKED"
        print(f"  [{status}] {text[:40]}... - {result.violations}")
    
    # Stats
    stats = await manager.get_stats()
    print(f"Guardrails stats: {stats}")
    
    await manager.shutdown()


async def demo_cost_tracking():
    """Demonstrate cost tracking."""
    print("\n" + "="*60)
    print("COST TRACKING DEMO")
    print("="*60)
    
    tracker = CostTracker(CostConfig(retention_days=30))
    await tracker.initialize()
    
    # Record some usage
    await tracker.record_usage(
        model="gpt-4",
        input_tokens=500,
        output_tokens=200,
        user_id="user123",
        agent_id="demo-agent"
    )
    
    await tracker.record_usage(
        model="gpt-3.5-turbo",
        input_tokens=1000,
        output_tokens=500,
        user_id="user123",
        agent_id="demo-agent"
    )
    
    await tracker.record_usage(
        model="gpt-4",
        input_tokens=300,
        output_tokens=150,
        user_id="user456",
        agent_id="demo-agent"
    )
    
    # Create a budget
    budget = await tracker.create_budget(
        name="Daily Budget",
        max_cost=10.0,
        max_tokens=100000,
        period="daily"
    )
    print(f"Created budget: {budget.name}")
    
    # Check budget
    check = await tracker.check_budget(user_id="user123", estimated_tokens=5000)
    print(f"Budget check: allowed={check['allowed']}, warnings={check['warnings']}")
    
    # Get stats
    stats = await tracker.get_usage_stats()
    print(f"Total cost: ${stats.total_cost:.4f}")
    print(f"Total tokens: {stats.total_tokens}")
    print(f"By model: {stats.by_model}")
    
    await tracker.shutdown()


async def demo_rate_limiting():
    """Demonstrate rate limiting."""
    print("\n" + "="*60)
    print("RATE LIMITING DEMO")
    print("="*60)
    
    limiter = RateLimiter(RateLimitConfig(
        default_requests_per_minute=10,
        default_tokens_per_minute=10000
    ))
    await limiter.initialize()
    
    # Simulate requests
    user_id = "user123"
    
    print("Making 12 requests (limit is 10/min)...")
    for i in range(12):
        result = await limiter.check(user_id=user_id)
        status = "ALLOWED" if result.allowed else "BLOCKED"
        print(f"  Request {i+1}: {status} (remaining: {result.remaining})")
    
    # Stats
    stats = await limiter.get_stats()
    print(f"Rate limiter stats: {stats}")
    
    await limiter.shutdown()


async def demo_model_router():
    """Demonstrate model routing."""
    print("\n" + "="*60)
    print("MODEL ROUTER DEMO")
    print("="*60)
    
    from app.capabilities.model_router import ModelEndpoint, ModelTier, TaskType
    
    router = ModelRouter(ModelRouterConfig(
        default_strategy=RoutingStrategy.TASK_BASED
    ))
    await router.initialize()
    
    # Register endpoints
    await router.register_endpoint(ModelEndpoint(
        id="gpt4",
        name="GPT-4",
        provider="openai",
        model="gpt-4",
        endpoint="https://api.openai.com/v1",
        tier=ModelTier.PREMIUM,
        supported_tasks=[TaskType.COMPLEX_REASONING, TaskType.CODE_GENERATION],
        input_price=0.03,
        output_price=0.06
    ))
    
    await router.register_endpoint(ModelEndpoint(
        id="gpt35",
        name="GPT-3.5 Turbo",
        provider="openai",
        model="gpt-3.5-turbo",
        endpoint="https://api.openai.com/v1",
        tier=ModelTier.ECONOMY,
        supported_tasks=[TaskType.SIMPLE_QA, TaskType.SUMMARIZATION],
        input_price=0.0005,
        output_price=0.0015
    ))
    
    # Route for different tasks
    tasks = [
        (TaskType.SIMPLE_QA, "Simple Q&A"),
        (TaskType.COMPLEX_REASONING, "Complex reasoning"),
        (TaskType.CODE_GENERATION, "Code generation"),
    ]
    
    for task_type, task_name in tasks:
        decision = await router.route(task_type=task_type)
        if decision:
            print(f"  {task_name} -> {decision.endpoint.name} ({decision.reason})")
    
    # Route with different strategies
    print("\nRouting strategies:")
    for strategy in [RoutingStrategy.LEAST_COST, RoutingStrategy.ROUND_ROBIN]:
        decision = await router.route(strategy=strategy)
        if decision:
            print(f"  {strategy.value} -> {decision.endpoint.name}")
    
    # Stats
    stats = await router.get_stats()
    print(f"Router stats: {stats}")
    
    await router.shutdown()


async def demo_advanced_graph():
    """Demonstrate advanced graph features."""
    print("\n" + "="*60)
    print("ADVANCED GRAPH DEMO")
    print("="*60)
    
    executor = AdvancedGraphExecutor(AdvancedGraphConfig(
        max_parallel_nodes=5,
        enable_checkpointing=True
    ))
    await executor.initialize()
    
    # Register handlers
    async def fetch_data(state, config):
        return {"data": f"Fetched data for {config.get('source', 'unknown')}"}
    
    async def process_data(state, config):
        return {"processed": f"Processed: {state.get('data', '')}"}
    
    async def generate_report(state, config):
        return {"report": f"Report: {state.get('processed', '')}"}
    
    executor.register_handler("fetch_data", fetch_data)
    executor.register_handler("process_data", process_data)
    executor.register_handler("generate_report", generate_report)
    
    # Create a simple graph
    nodes = [
        GraphNode(
            id="fetch",
            name="Fetch Data",
            node_type="action",
            handler="fetch_data",
            config={"source": "database"},
            next_nodes=["process"]
        ),
        GraphNode(
            id="process",
            name="Process Data",
            node_type="action",
            handler="process_data",
            next_nodes=["report"]
        ),
        GraphNode(
            id="report",
            name="Generate Report",
            node_type="action",
            handler="generate_report"
        ),
    ]
    
    await executor.register_graph("data-pipeline", nodes)
    
    # Execute the graph
    print("Executing data pipeline graph...")
    execution = await executor.execute(
        "data-pipeline",
        initial_state={"request_id": "req123"}
    )
    
    print(f"Execution status: {execution.status.value}")
    print(f"Final state: {execution.state}")
    print(f"Nodes executed: {len(execution.node_executions)}")
    
    # Stats
    stats = await executor.get_stats()
    print(f"Graph executor stats: {stats}")
    
    await executor.shutdown()


async def demo_capability_registry():
    """Demonstrate capability registry."""
    print("\n" + "="*60)
    print("CAPABILITY REGISTRY DEMO")
    print("="*60)
    
    registry = CapabilityRegistry()
    
    # Register capabilities
    session_mgr = SessionManager()
    memory_mgr = MemoryManager()
    guardrails = GuardrailsManager()
    
    registry.register(session_mgr)
    registry.register(memory_mgr)
    registry.register(guardrails)
    
    # Initialize all
    await registry.initialize_all()
    print(f"Initialized {len(registry.list_capabilities())} capabilities")
    
    # Get specific capability
    sessions = registry.get("sessions")
    print(f"Got capability: {sessions.name} v{sessions.version}")
    
    # Check status
    for name, cap in registry.list_capabilities().items():
        print(f"  {name}: {cap.status.value}")
    
    # Shutdown all
    await registry.shutdown_all()
    print("All capabilities shut down")


async def main():
    """Run all demos."""
    print("="*60)
    print("ADK CAPABILITIES DEMONSTRATION")
    print("="*60)
    
    demos = [
        ("Sessions", demo_sessions),
        ("Memory", demo_memory),
        ("Streaming", demo_streaming),
        ("Guardrails", demo_guardrails),
        ("Cost Tracking", demo_cost_tracking),
        ("Rate Limiting", demo_rate_limiting),
        ("Model Router", demo_model_router),
        ("Advanced Graph", demo_advanced_graph),
        ("Capability Registry", demo_capability_registry),
    ]
    
    for name, demo_fn in demos:
        try:
            await demo_fn()
        except Exception as e:
            print(f"\n[ERROR] {name} demo failed: {e}")
    
    print("\n" + "="*60)
    print("ALL DEMOS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
