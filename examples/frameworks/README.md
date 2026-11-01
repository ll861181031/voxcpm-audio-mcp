# Framework examples

> 工作区级部署与飞牛唱歌链路见
> `C:\Users\lsr\Documents\Codex\2026-09-16\yan\README.md`。

These examples show how to connect popular Python agent frameworks to the local VoxCPM Audio stdio MCP server.

- `generic_mcp_client.py`: uses the official Python MCP SDK.
- `openai_agents.py`: uses the OpenAI Agents SDK.
- `langchain_mcp.py`: uses LangChain's MCP adapter.

Install the framework you want, then replace the launcher path with the absolute path printed by:

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_agent_config.py --agent generic
```
