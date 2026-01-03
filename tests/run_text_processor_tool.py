import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.tool_service import ToolService
from app.services.agent_executor import AgentExecutor

async def run_text_summary():
    print("\n=== Testing text-processor: summarize ===")
    tool_id = "text-processor"
    args = {
        "text": "This is a long text that needs to be summarized. It contains multiple sentences and should be truncated to demonstrate the summarization functionality.",
        "operation": "summarize_text",
        "max_length": 50
    }

    tool = ToolService().get_tool(tool_id)
    executor = AgentExecutor()

    result_json_str = await executor._execute_tool(tool, args, mock=False)
    result = json.loads(result_json_str)
    print(json.dumps(result, indent=2))


async def run_count_words():
    print("\n=== Testing text-processor: count_words ===")
    tool_id = "text-processor"
    args = {
        "text": "The quick brown fox jumps over the lazy dog. This sentence contains nine words.",
        "operation": "count_words"
    }

    tool = ToolService().get_tool(tool_id)
    executor = AgentExecutor()

    result_json_str = await executor._execute_tool(tool, args, mock=False)
    result = json.loads(result_json_str)
    print(json.dumps(result, indent=2))


async def run_extract_keywords():
    print("\n=== Testing text-processor: extract_keywords ===")
    tool_id = "text-processor"
    args = {
        "text": "Machine learning and artificial intelligence are transforming technology. Deep learning models use neural networks for pattern recognition. Machine learning algorithms process data efficiently.",
        "operation": "extract_keywords",
        "max_keywords": 5
    }

    tool = ToolService().get_tool(tool_id)
    executor = AgentExecutor()

    result_json_str = await executor._execute_tool(tool, args, mock=False)
    result = json.loads(result_json_str)
    print(json.dumps(result, indent=2))


async def run_all_tests():
    """Run all tool tests."""
    await run_text_summary()
    await run_count_words()
    await run_extract_keywords()
    print("\n=== All tests completed ===\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())