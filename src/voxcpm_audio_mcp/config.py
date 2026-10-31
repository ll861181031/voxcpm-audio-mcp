from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _path(name: str, default: str) -> Path:
    return Path(os.path.expandvars(os.getenv(name, default)))


@dataclass(frozen=True)
class Settings:
    voxcpm_home: Path
    voxcpm_url: str
    voxcpm_python: Path
    voxcpm_start_script: Path
    soulx_home: Path
    soulx_python: Path
    soulx_model_path: Path
    soulx_config: Path
    soulx_phoneset: Path
    soulx_prompt_wav: Path
    soulx_prompt_metadata: Path
    ffmpeg: Path
    output_dir: Path
    log_dir: Path
    min_free_vram_mb: int
    request_timeout_s: int
    max_text_chars: int

    @classmethod
    def from_env(cls) -> "Settings":
        plugin_data = os.getenv("PLUGIN_DATA")
        return cls(
            voxcpm_home=_path("VOXCPM_HOME", r"D:\Desktop\VoxCPM2"),
            voxcpm_url=os.getenv("VOXCPM_URL", "http://127.0.0.1:8808").rstrip("/"),
            voxcpm_python=_path(
                "VOXCPM_PYTHON",
                r"D:\Desktop\VoxCPM2\.venv\Scripts\python.exe",
            ),
            voxcpm_start_script=_path(
                "VOXCPM_START_SCRIPT",
                r"D:\Desktop\VoxCPM2\Start-VoxCPM.ps1",
            ),
            soulx_home=_path("SOULX_HOME", r"D:\Desktop\SoulX-Singer"),
            soulx_python=_path(
                "SOULX_PYTHON",
                r"D:\Desktop\SoulX-Singer\.venv\Scripts\python.exe",
            ),
            soulx_model_path=_path(
                "SOULX_MODEL_PATH",
                r"D:\Desktop\SoulX-Singer\pretrained_models\SoulX-Singer\model.pt",
            ),
            soulx_config=_path(
                "SOULX_CONFIG",
                r"D:\Desktop\SoulX-Singer\soulxsinger\config\soulxsinger.yaml",
            ),
            soulx_phoneset=_path(
                "SOULX_PHONESET",
                r"D:\Desktop\SoulX-Singer\soulxsinger\utils\phoneme\phone_set.json",
            ),
            soulx_prompt_wav=_path(
                "SOULX_PROMPT_WAV",
                r"D:\Desktop\SoulX-Singer\example\audio\zh_prompt.wav",
            ),
            soulx_prompt_metadata=_path(
                "SOULX_PROMPT_METADATA",
                r"D:\Desktop\SoulX-Singer\example\audio\zh_prompt.json",
            ),
            ffmpeg=_path(
                "FFMPEG",
                r"D:\Desktop\VoxCPM2\tools\ffmpeg\bin\ffmpeg.exe",
            ),
            output_dir=_path(
                "AUDIO_OUTPUT_DIR",
                str(Path(plugin_data) / "audio" if plugin_data else Path.home() / "Music" / "VoxCPM-MCP"),
            ),
            log_dir=_path(
                "MCP_LOG_DIR",
                str(
                    Path(plugin_data)
                    / "logs"
                    if plugin_data
                    else Path(os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
                    / "OpenAI"
                    / "Codex"
                    / "Plugins"
                    / "voxcpm-audio-mcp"
                    / "logs"
                ),
            ),
            min_free_vram_mb=int(os.getenv("MIN_FREE_VRAM_MB", "6000")),
            request_timeout_s=int(os.getenv("REQUEST_TIMEOUT_S", "3600")),
            max_text_chars=int(os.getenv("MAX_TEXT_CHARS", "2000")),
        )
