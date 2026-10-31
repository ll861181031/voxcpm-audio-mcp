from pathlib import Path

from voxcpm_audio_mcp.agent_config import build_agent_config


def test_build_agent_config_uses_launcher():
    root = Path(__file__).resolve().parents[1]
    config = build_agent_config(root)
    server = config["mcpServers"]["voxcpm-audio"]
    assert server["command"].endswith("launch_mcp.cmd")
    assert server["args"] == []
    assert server["env"]["PYTHONUTF8"] == "1"


def test_build_agent_config_vscode_uses_servers_wrapper():
    root = Path(__file__).resolve().parents[1]
    config = build_agent_config(root, agent="vscode")
    assert "servers" in config
    assert "voxcpm-audio" in config["servers"]


def test_build_agent_config_generic_uses_mcp_servers_wrapper():
    root = Path(__file__).resolve().parents[1]
    config = build_agent_config(root, agent="generic")
    assert "mcpServers" in config


def test_build_agent_config_rejects_missing_python():
    import pytest

    missing_root = Path(__file__).resolve().parents[1] / "missing"
    with pytest.raises(FileNotFoundError):
        build_agent_config(missing_root, use_python=True)
