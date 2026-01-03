import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.tool_service import ToolService
from app.services.agent_executor import AgentExecutor

async def run_httpbin():
    tool = ToolService().get_tool("httpbin-test")
    executor = AgentExecutor()

    args = {
        "test_data": "hello from adk",
        "delay": 0,
        "timestamp": "2025-12-28T00:00:00Z",
    }

    result_json_str = await executor._execute_tool(tool, args, mock=False)
    print(json.dumps(json.loads(result_json_str), indent=2))

if __name__ == "__main__":
    asyncio.run(run_httpbin())