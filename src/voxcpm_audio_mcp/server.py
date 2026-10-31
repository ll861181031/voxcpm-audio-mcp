from __future__ import annotations

from pathlib import Path
from typing import Literal

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field

from .audio import vram_free_mb
from .backends import AudioBackendError, SoulXSingerBackend, VoxCPMBackend
from .config import Settings


class SpeakSegment(BaseModel):
    text: str = Field(description="要合成的这一段文字")
    control_instruction: str = Field(default="", description="这一段的情绪、语气、音量、重音和语速提示")
    pause_ms: int = Field(default=700, ge=0, le=5000, description="这段结束后的停顿，单位毫秒")


settings = Settings.from_env()
speech = VoxCPMBackend(settings)
singing = SoulXSingerBackend(settings)

mcp = MCPServer("VoxCPM Audio")


@mcp.tool(
    description="用本地 VoxCPM2 生成说话或情感旁白。返回音频文件路径。",
)
def speak(
    text: str,
    control_instruction: str = "自然、清晰、亲切的普通话，语速适中，情绪真实。",
    reference_audio_path: str | None = None,
    cfg_value: float = 2.2,
    inference_timesteps: int = 14,
    seed: int | None = None,
    output_format: Literal["wav", "mp3"] = "mp3",
    normalize_loudness: bool = True,
) -> dict:
    """Generate speech with VoxCPM2."""
    try:
        return speech.speak(
            text=text,
            control_instruction=control_instruction,
            reference_audio_path=reference_audio_path,
            cfg_value=cfg_value,
            inference_timesteps=inference_timesteps,
            seed=seed,
            output_format=output_format,
            normalize_loudness=normalize_loudness,
        )
    except (AudioBackendError, FileNotFoundError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


@mcp.tool(
    description="把多段文字分别用 VoxCPM2 合成，并按停顿拼接成一条情感旁白。",
)
def speak_segments(
    segments: list[SpeakSegment],
    reference_audio_path: str | None = None,
    cfg_value: float = 2.3,
    inference_timesteps: int = 16,
    seed: int | None = None,
    output_format: Literal["wav", "mp3"] = "mp3",
    normalize_loudness: bool = True,
) -> dict:
    """Generate segmented emotional narration with VoxCPM2."""
    try:
        return speech.speak_segments(
            segments=[segment.model_dump() for segment in segments],
            reference_audio_path=reference_audio_path,
            cfg_value=cfg_value,
            inference_timesteps=inference_timesteps,
            seed=seed,
            output_format=output_format,
            normalize_loudness=normalize_loudness,
        )
    except (AudioBackendError, FileNotFoundError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


@mcp.tool(
    description="用 SoulX-Singer 根据已写好的目标元数据生成带旋律的歌声。",
)
def sing_metadata(
    target_metadata_path: str,
    prompt_wav_path: str | None = None,
    prompt_metadata_path: str | None = None,
    device: Literal["auto", "cuda", "cpu"] = "auto",
    control: Literal["score", "melody"] = "score",
    pitch_shift: int = 0,
    auto_shift: bool = True,
    output_format: Literal["wav", "mp3"] = "mp3",
    normalize_loudness: bool = True,
) -> dict:
    """Generate singing from a SoulX-Singer metadata JSON file."""
    try:
        return singing.sing_metadata(
            target_metadata_path=target_metadata_path,
            prompt_wav_path=prompt_wav_path,
            prompt_metadata_path=prompt_metadata_path,
            device=device,
            control=control,
            pitch_shift=pitch_shift,
            auto_shift=auto_shift,
            output_format=output_format,
            normalize_loudness=normalize_loudness,
        )
    except (AudioBackendError, FileNotFoundError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


@mcp.tool(
    description="用音素、MIDI 音高和每字时长直接生成唱歌，不需要手写完整元数据。",
)
def sing_notes(
    phonemes: list[str],
    note_pitches: list[int],
    durations_ms: list[int],
    text: str | None = None,
    language: str = "Mandarin",
    prompt_wav_path: str | None = None,
    prompt_metadata_path: str | None = None,
    device: Literal["auto", "cuda", "cpu"] = "auto",
    pitch_shift: int = 0,
    auto_shift: bool = True,
    output_format: Literal["wav", "mp3"] = "mp3",
    normalize_loudness: bool = True,
) -> dict:
    """Generate singing from phonemes, notes, and durations."""
    try:
        return singing.sing_notes(
            phonemes=phonemes,
            note_pitches=note_pitches,
            durations_ms=durations_ms,
            text=text,
            language=language,
            prompt_wav_path=prompt_wav_path,
            prompt_metadata_path=prompt_metadata_path,
            device=device,
            pitch_shift=pitch_shift,
            auto_shift=auto_shift,
            output_format=output_format,
            normalize_loudness=normalize_loudness,
        )
    except (AudioBackendError, FileNotFoundError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


@mcp.tool(
    description="检查本地模型、FFmpeg、VoxCPM2 服务和 GPU 显存状态。",
)
def health() -> dict:
    """Report local backend health."""
    free_mb = vram_free_mb()
    return {
        "voxcpm_url": settings.voxcpm_url,
        "voxcpm_ready": speech.ready(),
        "voxcpm_model_dir": str(settings.voxcpm_home / "models" / "VoxCPM2"),
        "soulx_home": str(settings.soulx_home),
        "soulx_model_exists": settings.soulx_model_path.is_file(),
        "ffmpeg_exists": settings.ffmpeg.is_file(),
        "free_vram_mb": free_mb,
        "min_free_vram_mb": settings.min_free_vram_mb,
        "output_dir": str(settings.output_dir),
    }


def main() -> None:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    mcp.run()


if __name__ == "__main__":
    main()
