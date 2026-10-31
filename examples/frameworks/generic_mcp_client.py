from __future__ import annotations

import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, stdio_client


REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "scripts" / "launch_mcp.cmd"


async def main() -> None:
    params = StdioServerParameters(
        command=str(LAUNCHER),
        args=[],
        cwd=str(REPO_ROOT),
    )
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(tool.name)


if __name__ == "__main__":
    asyncio.run(main())
