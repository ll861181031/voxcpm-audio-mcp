from __future__ import annotations

import asyncio
from pathlib import Path

from langchain.mcp import MCPAdapter


REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "scripts" / "launch_mcp.cmd"


async def main() -> None:
    config = {
        "mcpServers": {
            "voxcpm-audio": {
                "command": str(LAUNCHER),
                "args": [],
            }
        }
    }
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        for tool in tools:
            print(tool.name)


if __name__ == "__main__":
    asyncio.run(main())
