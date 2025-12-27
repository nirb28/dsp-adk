#!/usr/bin/env python
"""
ADK Command Line Interface.

Provides commands for managing agents, tools, graphs, and capabilities.
"""
import argparse
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def load_yaml(path: str) -> dict:
    """Load a YAML file."""
    import yaml
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def save_yaml(path: str, data: dict):
    """Save data to YAML file."""
    import yaml
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)


def print_json(data: dict):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))


def print_table(headers: list, rows: list):
    """Print data as a table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * w for w in col_widths)
    
    print(header_line)
    print(separator)
    for row in rows:
        print(" | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)))


class ADKClient:
    """Client for ADK API."""
    
    def __init__(self, base_url: str = "http://localhost:8100"):
        self.base_url = base_url
        self.token: Optional[str] = None
    
    async def _request(self, method: str, path: str, data: dict = None) -> dict:
        """Make an API request."""
        import aiohttp
        
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        url = f"{self.base_url}{path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, json=data, headers=headers
            ) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    raise Exception(f"API error {resp.status}: {text}")
                return await resp.json()
    
    async def get(self, path: str) -> dict:
        return await self._request("GET", path)
    
    async def post(self, path: str, data: dict) -> dict:
        return await self._request("POST", path, data)
    
    async def put(self, path: str, data: dict) -> dict:
        return await self._request("PUT", path, data)
    
    async def delete(self, path: str) -> dict:
        return await self._request("DELETE", path)


# Agent Commands
async def cmd_agent_list(client: ADKClient, args):
    """List all agents."""
    result = await client.get("/agents")
    
    if args.json:
        print_json(result)
    else:
        rows = [
            [a["id"], a["name"], a.get("model", "N/A"), a.get("status", "active")]
            for a in result.get("agents", [])
        ]
        print_table(["ID", "Name", "Model", "Status"], rows)


async def cmd_agent_get(client: ADKClient, args):
    """Get agent details."""
    result = await client.get(f"/agents/{args.id}")
    print_json(result)


async def cmd_agent_create(client: ADKClient, args):
    """Create an agent from YAML file."""
    data = load_yaml(args.file)
    result = await client.post("/agents", data)
    print(f"Created agent: {result.get('id', 'unknown')}")
    if args.json:
        print_json(result)


async def cmd_agent_delete(client: ADKClient, args):
    """Delete an agent."""
    await client.delete(f"/agents/{args.id}")
    print(f"Deleted agent: {args.id}")


# Tool Commands
async def cmd_tool_list(client: ADKClient, args):
    """List all tools."""
    result = await client.get("/tools")
    
    if args.json:
        print_json(result)
    else:
        rows = [
            [t["id"], t["name"], t.get("type", "function"), t.get("description", "")[:40]]
            for t in result.get("tools", [])
        ]
        print_table(["ID", "Name", "Type", "Description"], rows)


async def cmd_tool_get(client: ADKClient, args):
    """Get tool details."""
    result = await client.get(f"/tools/{args.id}")
    print_json(result)


async def cmd_tool_create(client: ADKClient, args):
    """Create a tool from YAML file."""
    data = load_yaml(args.file)
    result = await client.post("/tools", data)
    print(f"Created tool: {result.get('id', 'unknown')}")


async def cmd_tool_schema(client: ADKClient, args):
    """Get OpenAI-compatible tool schema."""
    result = await client.get(f"/tools/{args.id}/schema")
    print_json(result)


# Graph Commands
async def cmd_graph_list(client: ADKClient, args):
    """List all graphs."""
    result = await client.get("/graphs")
    
    if args.json:
        print_json(result)
    else:
        rows = [
            [g["id"], g["name"], len(g.get("nodes", [])), g.get("status", "active")]
            for g in result.get("graphs", [])
        ]
        print_table(["ID", "Name", "Nodes", "Status"], rows)


async def cmd_graph_get(client: ADKClient, args):
    """Get graph details."""
    result = await client.get(f"/graphs/{args.id}")
    print_json(result)


async def cmd_graph_create(client: ADKClient, args):
    """Create a graph from YAML file."""
    data = load_yaml(args.file)
    result = await client.post("/graphs", data)
    print(f"Created graph: {result.get('id', 'unknown')}")


async def cmd_graph_run(client: ADKClient, args):
    """Run a graph."""
    data = {}
    if args.input:
        data["input"] = json.loads(args.input)
    
    result = await client.post(f"/graphs/{args.id}/run", data)
    print_json(result)


# MCP Server Commands
async def cmd_mcp_list(client: ADKClient, args):
    """List MCP servers."""
    result = await client.get("/mcp-servers")
    
    if args.json:
        print_json(result)
    else:
        rows = [
            [s["id"], s["name"], s.get("protocol", "stdio"), s.get("status", "stopped")]
            for s in result.get("servers", [])
        ]
        print_table(["ID", "Name", "Protocol", "Status"], rows)


async def cmd_mcp_status(client: ADKClient, args):
    """Get MCP server status."""
    result = await client.get(f"/mcp-servers/{args.id}/status")
    print_json(result)


# Init Command
def cmd_init(args):
    """Initialize a new ADK project."""
    project_dir = Path(args.name)
    
    if project_dir.exists() and not args.force:
        print(f"Directory {args.name} already exists. Use --force to overwrite.")
        return
    
    # Create directories
    dirs = ["agents", "tools", "graphs", "skills", "data"]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)
    
    # Create config.yaml
    config = {
        "name": args.name,
        "version": "1.0.0",
        "adk": {
            "server_url": "http://localhost:8100",
            "jwt_url": "http://localhost:8020"
        },
        "capabilities": {
            "sessions": {"enabled": True},
            "memory": {"enabled": True},
            "streaming": {"enabled": True},
            "guardrails": {"enabled": False}
        }
    }
    save_yaml(str(project_dir / "config.yaml"), config)
    
    # Create sample agent
    agent = {
        "id": "sample-agent",
        "name": "Sample Agent",
        "description": "A sample agent to get started",
        "model": "gpt-3.5-turbo",
        "system_prompt": "You are a helpful assistant."
    }
    save_yaml(str(project_dir / "agents" / "sample-agent.yaml"), agent)
    
    # Create sample tool
    tool = {
        "id": "hello-tool",
        "name": "Hello Tool",
        "type": "function",
        "description": "A simple greeting tool",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name to greet"}
            },
            "required": ["name"]
        }
    }
    save_yaml(str(project_dir / "tools" / "hello-tool.yaml"), tool)
    
    # Create README
    readme = f"""# {args.name}

ADK Project generated by `adk init`.

## Structure

- `agents/` - Agent configurations
- `tools/` - Tool definitions
- `graphs/` - Graph/workflow definitions
- `skills/` - Reusable skills
- `data/` - Data files
- `config.yaml` - Project configuration

## Getting Started

1. Start the ADK server: `python run.py`
2. List agents: `adk agent list`
3. Run an agent: `adk agent run sample-agent`

## Configuration

Edit `config.yaml` to configure capabilities and connections.
"""
    (project_dir / "README.md").write_text(readme)
    
    print(f"Initialized ADK project: {args.name}")
    print(f"  - Created config.yaml")
    print(f"  - Created sample agent: agents/sample-agent.yaml")
    print(f"  - Created sample tool: tools/hello-tool.yaml")
    print(f"\nNext steps:")
    print(f"  cd {args.name}")
    print(f"  adk agent list")


# Run Command
async def cmd_run(client: ADKClient, args):
    """Run an agent with a prompt."""
    data = {
        "prompt": args.prompt,
        "stream": args.stream
    }
    
    if args.context:
        data["context"] = json.loads(args.context)
    
    result = await client.post(f"/agents/{args.agent}/run", data)
    
    if args.stream:
        print(result.get("response", ""))
    else:
        print_json(result)


# Version Command
def cmd_version(args):
    """Show version information."""
    print("ADK CLI v1.0.0")
    print("Agent Development Kit")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="adk",
        description="ADK Command Line Interface"
    )
    parser.add_argument(
        "--url", 
        default=os.environ.get("ADK_URL", "http://localhost:8100"),
        help="ADK server URL"
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("ADK_TOKEN"),
        help="JWT token for authentication"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new ADK project")
    init_parser.add_argument("name", help="Project name")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing")
    
    # Version command
    subparsers.add_parser("version", help="Show version")
    
    # Agent commands
    agent_parser = subparsers.add_parser("agent", help="Agent commands")
    agent_sub = agent_parser.add_subparsers(dest="action")
    
    agent_sub.add_parser("list", help="List agents")
    
    agent_get = agent_sub.add_parser("get", help="Get agent details")
    agent_get.add_argument("id", help="Agent ID")
    
    agent_create = agent_sub.add_parser("create", help="Create agent")
    agent_create.add_argument("file", help="YAML file path")
    
    agent_delete = agent_sub.add_parser("delete", help="Delete agent")
    agent_delete.add_argument("id", help="Agent ID")
    
    # Tool commands
    tool_parser = subparsers.add_parser("tool", help="Tool commands")
    tool_sub = tool_parser.add_subparsers(dest="action")
    
    tool_sub.add_parser("list", help="List tools")
    
    tool_get = tool_sub.add_parser("get", help="Get tool details")
    tool_get.add_argument("id", help="Tool ID")
    
    tool_create = tool_sub.add_parser("create", help="Create tool")
    tool_create.add_argument("file", help="YAML file path")
    
    tool_schema = tool_sub.add_parser("schema", help="Get tool schema")
    tool_schema.add_argument("id", help="Tool ID")
    
    # Graph commands
    graph_parser = subparsers.add_parser("graph", help="Graph commands")
    graph_sub = graph_parser.add_subparsers(dest="action")
    
    graph_sub.add_parser("list", help="List graphs")
    
    graph_get = graph_sub.add_parser("get", help="Get graph details")
    graph_get.add_argument("id", help="Graph ID")
    
    graph_create = graph_sub.add_parser("create", help="Create graph")
    graph_create.add_argument("file", help="YAML file path")
    
    graph_run = graph_sub.add_parser("run", help="Run graph")
    graph_run.add_argument("id", help="Graph ID")
    graph_run.add_argument("--input", help="Input JSON")
    
    # MCP commands
    mcp_parser = subparsers.add_parser("mcp", help="MCP server commands")
    mcp_sub = mcp_parser.add_subparsers(dest="action")
    
    mcp_sub.add_parser("list", help="List MCP servers")
    
    mcp_status = mcp_sub.add_parser("status", help="Get server status")
    mcp_status.add_argument("id", help="Server ID")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run an agent")
    run_parser.add_argument("agent", help="Agent ID")
    run_parser.add_argument("prompt", help="Prompt text")
    run_parser.add_argument("--context", help="Context JSON")
    run_parser.add_argument("--stream", action="store_true", help="Stream output")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle sync commands
    if args.command == "init":
        cmd_init(args)
        return
    elif args.command == "version":
        cmd_version(args)
        return
    
    # Handle async commands
    client = ADKClient(args.url)
    if args.token:
        client.token = args.token
    
    async def run_async():
        if args.command == "agent":
            if args.action == "list":
                await cmd_agent_list(client, args)
            elif args.action == "get":
                await cmd_agent_get(client, args)
            elif args.action == "create":
                await cmd_agent_create(client, args)
            elif args.action == "delete":
                await cmd_agent_delete(client, args)
        elif args.command == "tool":
            if args.action == "list":
                await cmd_tool_list(client, args)
            elif args.action == "get":
                await cmd_tool_get(client, args)
            elif args.action == "create":
                await cmd_tool_create(client, args)
            elif args.action == "schema":
                await cmd_tool_schema(client, args)
        elif args.command == "graph":
            if args.action == "list":
                await cmd_graph_list(client, args)
            elif args.action == "get":
                await cmd_graph_get(client, args)
            elif args.action == "create":
                await cmd_graph_create(client, args)
            elif args.action == "run":
                await cmd_graph_run(client, args)
        elif args.command == "mcp":
            if args.action == "list":
                await cmd_mcp_list(client, args)
            elif args.action == "status":
                await cmd_mcp_status(client, args)
        elif args.command == "run":
            await cmd_run(client, args)
    
    try:
        asyncio.run(run_async())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
