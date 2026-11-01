from __future__ import annotations

from pathlib import Path
from typing import Literal
from contextlib import contextmanager

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field

from .audio import append_log, vram_info
from .backends import AudioBackendError, SoulXSingerBackend, VoxCPMBackend
from .config import Settings
from .presets import VoicePresetStore


class SpeakSegment(BaseModel):
    text: str = Field(description="要合成的这一段文字")
    control_instruction: str = Field(default="", description="这一段的情绪、语气、音量、重音和语速提示")
    pause_ms: int = Field(default=700, ge=0, le=5000, description="这段结束后的停顿，单位毫秒")


settings = Settings.from_env()
speech = VoxCPMBackend(settings)
singing = SoulXSingerBackend(settings)
voice_presets = VoicePresetStore(settings.voice_presets_path)

mcp = MCPServer("VoxCPM Audio")

DEFAULT_TARGET_F0 = 260.0
DEFAULT_TEMPO = 1.05
DEFAULT_CFG_VALUE = 2.3
DEFAULT_INFERENCE_TIMESTEPS = 16


@contextmanager
def logged_call(name: str, payload: dict):
    append_log(settings.log_dir, f"{name}.start", payload)
    try:
        yield
    except Exception as exc:
        append_log(settings.log_dir, f"{name}.error", {**payload, "error": type(exc).__name__, "message": str(exc)})
        raise
    else:
        append_log(settings.log_dir, f"{name}.finish", payload)


def resolve_speech_preset(
    *,
    voice_preset: str | None,
    control_instruction: str | None,
    reference_audio_path: str | None,
    cfg_value: float | None,
    inference_timesteps: int | None,
    target_f0: float | None,
    tempo: float | None,
    default_cfg_value: float = DEFAULT_CFG_VALUE,
    default_inference_timesteps: int = DEFAULT_INFERENCE_TIMESTEPS,
    default_target_f0: float = DEFAULT_TARGET_F0,
    default_tempo: float = DEFAULT_TEMPO,
) -> dict:
    preset = voice_presets.get(voice_preset) if voice_preset else {}
    return {
        "control_instruction": control_instruction
        or preset.get("control_instruction")
        or "自然、清晰、亲切的普通话，语速适中，情绪真实。",
        "reference_audio_path": reference_audio_path
        or preset.get("reference_audio_path"),
        "cfg_value": cfg_value if cfg_value is not None else preset.get("cfg_value", default_cfg_value),
        "inference_timesteps": inference_timesteps
        if inference_timesteps is not None
        else preset.get("inference_timesteps", default_inference_timesteps),
        "target_f0": target_f0 if target_f0 is not None else preset.get("target_f0", default_target_f0),
        "tempo": tempo if tempo is not None else preset.get("tempo", default_tempo),
    }


@mcp.tool(
    description="用本地 VoxCPM2 生成说话或情感旁白。返回音频文件路径。",
)
def speak(
    text: str,
    control_instruction: str | None = None,
    reference_audio_path: str | None = None,
    cfg_value: float | None = None,
    inference_timesteps: int | None = None,
    voice_preset: str | None = None,
    target_f0: float | None = None,
    tempo: float | None = None,
    seed: int | None = None,
    output_format: Literal["wav", "mp3"] = "mp3",
    normalize_loudness: bool = True,
) -> dict:
    """Generate speech with VoxCPM2."""
    try:
        resolved = resolve_speech_preset(
            voice_preset=voice_preset,
            control_instruction=control_instruction,
            reference_audio_path=reference_audio_path,
            cfg_value=cfg_value,
            inference_timesteps=inference_timesteps,
            target_f0=target_f0,
            tempo=tempo,
        )
        with logged_call(
            "speak",
            {
                "text_chars": len(text),
                "voice_preset": voice_preset,
                "cfg_value": resolved["cfg_value"],
                "inference_timesteps": resolved["inference_timesteps"],
                "target_f0": resolved["target_f0"],
                "tempo": resolved["tempo"],
                "output_format": output_format,
            },
        ):
            return speech.speak(
                text=text,
                control_instruction=resolved["control_instruction"],
                reference_audio_path=resolved["reference_audio_path"],
                cfg_value=resolved["cfg_value"],
                inference_timesteps=resolved["inference_timesteps"],
                target_f0=resolved["target_f0"],
                tempo=resolved["tempo"],
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
    cfg_value: float | None = None,
    inference_timesteps: int | None = None,
    voice_preset: str | None = None,
    target_f0: float | None = None,
    tempo: float | None = None,
    seed: int | None = None,
    output_format: Literal["wav", "mp3"] = "mp3",
    normalize_loudness: bool = True,
) -> dict:
    """Generate segmented emotional narration with VoxCPM2."""
    try:
        resolved = resolve_speech_preset(
            voice_preset=voice_preset,
            control_instruction=None,
            reference_audio_path=reference_audio_path,
            cfg_value=cfg_value,
            inference_timesteps=inference_timesteps,
            target_f0=target_f0,
            tempo=tempo,
        )
        with logged_call(
            "speak_segments",
            {
                "segments": len(segments),
                "voice_preset": voice_preset,
                "cfg_value": resolved["cfg_value"],
                "inference_timesteps": resolved["inference_timesteps"],
                "target_f0": resolved["target_f0"],
                "tempo": resolved["tempo"],
                "output_format": output_format,
            },
        ):
            return speech.speak_segments(
                segments=[segment.model_dump() for segment in segments],
                reference_audio_path=resolved["reference_audio_path"],
                cfg_value=resolved["cfg_value"],
                inference_timesteps=resolved["inference_timesteps"],
                target_f0=resolved["target_f0"],
                tempo=resolved["tempo"],
                seed=seed,
                output_format=output_format,
                normalize_loudness=normalize_loudness,
            )
    except (AudioBackendError, FileNotFoundError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


@mcp.tool(
    description="列出已保存的 VoxCPM2 音色预设。",
)
def list_voice_presets() -> dict:
    """List saved voice presets."""
    return {"presets": voice_presets.list()}


@mcp.tool(
    description="保存一组 VoxCPM2 音色参数，可包含目标基频、语速、CFG、采样步数、提示词和参考音频。",
)
def save_voice_preset(
    name: str,
    target_f0: float | None = None,
    tempo: float | None = None,
    cfg_value: float | None = None,
    inference_timesteps: int | None = None,
    control_instruction: str | None = None,
    reference_audio_path: str | None = None,
    overwrite: bool = False,
) -> dict:
    """Save a reusable VoxCPM2 voice preset."""
    preset = {
        key: value
        for key, value in {
            "target_f0": target_f0,
            "tempo": tempo,
            "cfg_value": cfg_value,
            "inference_timesteps": inference_timesteps,
            "control_instruction": control_instruction,
            "reference_audio_path": reference_audio_path,
        }.items()
        if value is not None
    }
    return voice_presets.save(name, preset, overwrite=overwrite)


@mcp.tool(
    description="删除一个已保存的 VoxCPM2 音色预设。",
)
def delete_voice_preset(name: str) -> dict:
    """Delete a saved voice preset."""
    return voice_presets.delete(name)


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
        with logged_call(
            "sing_metadata",
            {
                "target_metadata_path": target_metadata_path,
                "device": device,
                "control": control,
                "pitch_shift": pitch_shift,
                "output_format": output_format,
            },
        ):
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
        with logged_call(
            "sing_notes",
            {
                "notes": len(note_pitches),
                "device": device,
                "pitch_shift": pitch_shift,
                "output_format": output_format,
            },
        ):
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
    vram = vram_info()
    return {
        "voxcpm_url": settings.voxcpm_url,
        "voxcpm_ready": speech.ready(),
        "voxcpm_model_dir": str(settings.voxcpm_home / "models" / "VoxCPM2"),
        "soulx_home": str(settings.soulx_home),
        "soulx_model_exists": settings.soulx_model_path.is_file(),
        "ffmpeg_exists": settings.ffmpeg.is_file(),
        "free_vram_mb": vram["free_mb"],
        "vram_source": vram["path"],
        "vram_error": vram["error"],
        "min_free_vram_mb": settings.min_free_vram_mb,
        "output_dir": str(settings.output_dir),
        "log_dir": str(settings.log_dir),
    }


def main() -> None:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    mcp.run()


if __name__ == "__main__":
    main()
