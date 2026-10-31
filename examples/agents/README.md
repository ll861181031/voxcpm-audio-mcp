# Agent config examples

All examples use the same standard `mcpServers` shape.

For an absolute path on your machine, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_agent_config.py --agent cursor
```

Then paste the output into your agent's MCP settings.

## Common config locations

| Agent | Config location |
|---|---|
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Code | `.mcp.json` in the project root, or `claude mcp add` |
| Cursor | `.cursor/mcp.json` in the project, or global Cursor MCP settings |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |
| Cline | VS Code Cline MCP settings |
| Continue | `~/.continue/config.json` |
| VS Code | `.vscode/mcp.json` or user MCP settings |
| Generic MCP | Any client that supports stdio MCP servers |

If your client requires an absolute `command`, use the generator output instead of the relative example.
