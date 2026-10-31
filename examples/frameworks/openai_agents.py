from __future__ import annotations

import asyncio
from pathlib import Path

from agents.mcp import MCPServerStdio


REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "scripts" / "launch_mcp.cmd"


async def main() -> None:
    params = {
        "command": str(LAUNCHER),
        "args": [],
        "cwd": str(REPO_ROOT),
    }
    async with MCPServerStdio(params=params) as server:
        tools = await server.list_tools()
        for tool in tools:
            print(tool.name)


if __name__ == "__main__":
    asyncio.run(main())
