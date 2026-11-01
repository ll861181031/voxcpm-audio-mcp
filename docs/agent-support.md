# Agent support

> 工作区级部署与飞牛唱歌链路见
> `C:\Users\lsr\Documents\Codex\2026-09-16\yan\README.md`。

VoxCPM Audio uses a standard stdio MCP server, so it works with any MCP client that can launch a local command.

## Supported clients

| Client | Status | Notes |
|---|---|---|
| Codex | Supported | Uses `.codex-plugin/plugin.json` and `.mcp.json` |
| Claude Desktop | Supported | Use the generated `mcpServers` JSON |
| Claude Code | Supported | Use the generated `mcpServers` JSON |
| Cursor | Supported | Use the generated `mcpServers` JSON |
| Windsurf | Supported | Use the generated `mcpServers` JSON |
| Cline | Supported | Use the generated `mcpServers` JSON |
| Continue | Supported | Use the generated `mcpServers` JSON |
| VS Code MCP clients | Supported | Use the generated `mcpServers` JSON |
| Generic MCP clients | Supported | Any stdio MCP client |

## Generate a client config

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_agent_config.py --agent cursor
```

To write the config to a file:

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_agent_config.py --agent claude-desktop --output claude-desktop.json
```

The generated JSON uses this shape:

```json
{
  "mcpServers": {
    "voxcpm-audio": {
      "command": "C:\\path\\to\\scripts\\launch_mcp.cmd",
      "args": [],
      "env": {
        "VOXCPM_HOME": "D:\\Desktop\\VoxCPM2",
        "SOULX_HOME": "D:\\Desktop\\SoulX-Singer"
      }
    }
  }
}
```

Most MCP clients accept this same `mcpServers` object. Put it in the client’s MCP configuration file, or paste it into the client’s MCP settings UI.

VS Code uses a `servers` wrapper instead of `mcpServers`; the generator handles that automatically:

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_agent_config.py --agent vscode
```

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

## Portable Agent Plugins

The repository also includes:

```text
plugin.json
mcp.json
skills/audio/SKILL.md
```

These follow the portable Agent Plugins layout. Compatible clients can install the repository as a plugin and discover the bundled skill and stdio MCP server automatically.

Portable clients provide `PLUGIN_ROOT` and `PLUGIN_DATA`. The launcher stores its virtual environment, logs, and generated audio under `PLUGIN_DATA` when available, so the installed plugin stays self-contained.

## Python framework examples

The repository also includes framework examples:

```text
examples/frameworks/generic_mcp_client.py
examples/frameworks/openai_agents.py
examples/frameworks/langchain_mcp.py
```

These show how to connect the same stdio MCP server from the official Python MCP SDK, OpenAI Agents SDK, and LangChain.
