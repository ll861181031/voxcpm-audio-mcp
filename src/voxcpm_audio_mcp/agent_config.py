from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


AGENTS = {
    "codex": "Codex",
    "claude-desktop": "Claude Desktop",
    "claude-code": "Claude Code",
    "cursor": "Cursor",
    "windsurf": "Windsurf",
    "cline": "Cline",
    "continue": "Continue",
    "vscode": "VS Code",
    "generic": "Generic MCP client",
}


def _default_env() -> dict[str, str]:
    return {
        "VOXCPM_HOME": os.getenv("VOXCPM_HOME", r"D:\Desktop\VoxCPM2"),
        "VOXCPM_URL": os.getenv("VOXCPM_URL", "http://127.0.0.1:8808"),
        "SOULX_HOME": os.getenv("SOULX_HOME", r"D:\Desktop\SoulX-Singer"),
        "SOULX_MODEL_PATH": os.getenv(
            "SOULX_MODEL_PATH",
            r"D:\Desktop\SoulX-Singer\pretrained_models\SoulX-Singer\model.pt",
        ),
        "FFMPEG": os.getenv(
            "FFMPEG",
            r"D:\Desktop\VoxCPM2\tools\ffmpeg\bin\ffmpeg.exe",
        ),
        "MIN_FREE_VRAM_MB": os.getenv("MIN_FREE_VRAM_MB", "6000"),
        "PYTHONUTF8": "1",
    }


def build_agent_config(
    repo_root: str | Path,
    *,
    agent: str = "generic",
    use_python: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    if use_python:
        python = root / ".venv" / "Scripts" / "python.exe"
        if not python.is_file():
            raise FileNotFoundError(f"Python environment not found: {python}")
        command = str(python)
        args = ["-m", "voxcpm_audio_mcp.server"]
    else:
        launcher = root / "scripts" / "launch_mcp.cmd"
        if not launcher.is_file():
            raise FileNotFoundError(f"MCP launcher not found: {launcher}")
        command = str(launcher)
        args = []
    wrapper = "servers" if agent == "vscode" else "mcpServers"
    return {
        wrapper: {
            "voxcpm-audio": {
                "command": command,
                "args": args,
                "env": env or _default_env(),
            }
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an MCP client configuration for VoxCPM Audio."
    )
    parser.add_argument(
        "--agent",
        choices=sorted(AGENTS),
        default="generic",
        help="Target agent name; used only for the output comment.",
    )
    parser.add_argument(
        "--repo",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root",
    )
    parser.add_argument(
        "--python",
        action="store_true",
        help="Use .venv Python directly instead of the launcher.",
    )
    parser.add_argument(
        "--output",
        help="Optional output JSON file",
    )
    args = parser.parse_args()

    config = build_agent_config(args.repo, agent=args.agent, use_python=args.python)
    text = json.dumps(config, ensure_ascii=False, indent=2)
    if args.output:
        path = Path(args.output).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {args.agent} config to {path}")
    else:
        print(text)


if __name__ == "__main__":
    main()
