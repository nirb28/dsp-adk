"""
Simple telemetry test to verify spans are being created and exported.
"""
import asyncio
import sys
import logging
from pathlib import Path

# Configure logging FIRST
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, str(Path(__file__).parent))

from app.services.telemetry_service import get_telemetry_service
from app.models.telemetry import ActionType, SpanStatus, SpanKind


async def test_basic_telemetry():
    """Test basic telemetry creation and export."""
    print("=" * 60)
    print("Testing Basic Telemetry")
    print("=" * 60)
    
    telemetry = get_telemetry_service()
    
    print(f"OTEL Enabled: {telemetry.otel_enabled}")
    print(f"OTEL Endpoint: {telemetry.otel_endpoint}")
    print(f"Service Name: {telemetry.service_name}")
    print()
    
    # Create a test trace
    print("Creating test trace...")
    trace = telemetry.start_trace(
        name="test_trace",
        agent_id="test-agent"
    )
    print(f"✓ Trace created: {trace.trace_id}")
    
    # Add a span
    print("Adding test span...")
    span = telemetry.log_action(
        trace_id=trace.trace_id,
        action_type=ActionType.AGENT_START,
        name="test_action",
        input_data={"test": "data"},
        attributes={"test_attr": "value"},
        kind=SpanKind.SERVER
    )
    print(f"✓ Span created: {span.span_id}")
    
    # Add an event
    print("Adding span event...")
    telemetry.add_span_event(
        span_id=span.span_id,
        name="test_event",
        attributes={"event_data": "test payload"}
    )
    print(f"✓ Event added")
    
    # Complete the span
    print("Completing span...")
    telemetry.complete_action(
        span_id=span.span_id,
        status=SpanStatus.OK,
        output_data={"result": "success"}
    )
    print(f"✓ Span completed")
    
    # End the trace
    print("Ending trace...")
    telemetry.end_trace(trace.trace_id, SpanStatus.OK)
    print(f"✓ Trace ended")
    
    # Wait a moment for export
    print("\nWaiting for export...")
    await asyncio.sleep(2)
    
    print()
    print("=" * 60)
    print("CHECK JAEGER")
    print("=" * 60)
    print("1. Open http://localhost:16686")
    print(f"2. Select service: '{telemetry.service_name}'")
    print("3. Click 'Find Traces'")
    print("4. Look for trace: 'test_trace'")
    print()
    print("If you don't see it, check the logs above for [TELEMETRY] messages")
    print()


if __name__ == "__main__":
    asyncio.run(test_basic_telemetry())
