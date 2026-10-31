from __future__ import annotations

import json
import os
import random
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Literal

from .audio import (
    concat_wavs,
    convert_audio,
    copy_result,
    http_ready,
    new_output_path,
    probe_duration,
    safe_stem,
    validate_file,
    vram_free_mb,
)
from .config import Settings
from .metadata import build_target_metadata


class AudioBackendError(RuntimeError):
    """Raised when a local audio backend cannot complete a request."""


class VoxCPMBackend:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def ready(self) -> bool:
        return http_ready(self.settings.voxcpm_url)

    def ensure_server(self) -> None:
        if self.ready():
            return
        free_mb = vram_free_mb()
        if free_mb is not None and free_mb < self.settings.min_free_vram_mb:
            raise AudioBackendError(
                f"VoxCPM2 needs at least {self.settings.min_free_vram_mb} MB free VRAM; "
                f"currently {free_mb} MB is free. Stop another GPU job or start VoxCPM2 manually."
            )
        script = validate_file(self.settings.voxcpm_start_script, {".ps1"})
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                "-NoBrowser",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if result.returncode != 0:
            raise AudioBackendError(result.stderr.strip() or result.stdout.strip())
        deadline = time.time() + 180
        while time.time() < deadline:
            if self.ready():
                return
            time.sleep(1)
        raise AudioBackendError("VoxCPM2 did not become ready within 180 seconds")

    def speak(
        self,
        *,
        text: str,
        control_instruction: str = "",
        reference_audio_path: str | None = None,
        cfg_value: float = 2.2,
        inference_timesteps: int = 14,
        seed: int | None = None,
        output_format: Literal["wav", "mp3"] = "mp3",
        normalize_loudness: bool = True,
    ) -> dict[str, Any]:
        text = text.strip()
        if not text:
            raise ValueError("text must not be empty")
        if len(text) > self.settings.max_text_chars:
            raise ValueError(f"text is longer than {self.settings.max_text_chars} characters")
        if not 0.1 <= cfg_value <= 10.0:
            raise ValueError("cfg_value must be between 0.1 and 10.0")
        if not 1 <= inference_timesteps <= 100:
            raise ValueError("inference_timesteps must be between 1 and 100")
        self.ensure_server()
        from gradio_client import Client, handle_file

        ref = validate_file(reference_audio_path, {".wav", ".mp3", ".flac", ".ogg", ".m4a"}) if reference_audio_path else None
        actual_seed = int(seed) if seed is not None else random.randint(0, 2**32 - 1)
        with tempfile.TemporaryDirectory(prefix="voxcpm-mcp-") as temp:
            client = Client(self.settings.voxcpm_url, verbose=False, download_files=temp)
            result = client.predict(
                text=text,
                control_instruction=control_instruction.strip(),
                ref_wav=handle_file(str(ref)) if ref else None,
                use_prompt_text=False,
                prompt_text_value="",
                cfg_value=float(cfg_value),
                do_normalize=False,
                denoise=False,
                dit_steps=int(inference_timesteps),
                seed_value=actual_seed,
                api_name="/generate",
            )
            raw = Path(result[0])
            destination = new_output_path(self.settings.output_dir, text, output_format)
            final = convert_audio(
                raw,
                destination,
                self.settings.ffmpeg,
                normalize_loudness=normalize_loudness,
            )
            return {
                "backend": "VoxCPM2",
                "kind": "speech",
                "path": str(final),
                "duration_seconds": round(probe_duration(final), 3),
                "sample_rate": 48000,
                "seed": actual_seed,
                "text": text,
            }

    def speak_segments(
        self,
        *,
        segments: list[dict[str, Any]],
        reference_audio_path: str | None = None,
        cfg_value: float = 2.3,
        inference_timesteps: int = 16,
        seed: int | None = None,
        output_format: Literal["wav", "mp3"] = "mp3",
        normalize_loudness: bool = True,
    ) -> dict[str, Any]:
        if not segments:
            raise ValueError("segments must not be empty")
        if len(segments) > 50:
            raise ValueError("segments supports at most 50 entries")
        with tempfile.TemporaryDirectory(prefix="voxcpm-segments-") as temp:
            paths: list[Path] = []
            pauses: list[int] = []
            for index, segment in enumerate(segments):
                text = str(segment.get("text", "")).strip()
                if not text:
                    raise ValueError(f"segments[{index}].text must not be empty")
                pause_ms = int(segment.get("pause_ms", 700))
                if pause_ms < 0 or pause_ms > 5000:
                    raise ValueError(f"segments[{index}].pause_ms must be between 0 and 5000")
                item = self.speak(
                    text=text,
                    control_instruction=str(segment.get("control_instruction", "")),
                    reference_audio_path=reference_audio_path,
                    cfg_value=cfg_value,
                    inference_timesteps=inference_timesteps,
                    seed=(seed + index * 1009) if seed is not None else None,
                    output_format="wav",
                    normalize_loudness=False,
                )
                paths.append(Path(item["path"]))
                pauses.append(pause_ms)
            merged = Path(temp) / "narration.wav"
            concat_wavs(paths, pauses, merged)
            destination = new_output_path(
                self.settings.output_dir,
                f"narration-{len(segments)}-segments",
                output_format,
            )
            final = convert_audio(
                merged,
                destination,
                self.settings.ffmpeg,
                normalize_loudness=normalize_loudness,
            )
            return {
                "backend": "VoxCPM2",
                "kind": "segmented_narration",
                "path": str(final),
                "duration_seconds": round(probe_duration(final), 3),
                "segments": len(segments),
            }


class SoulXSingerBackend:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _select_device(self, requested: Literal["auto", "cuda", "cpu"]) -> str:
        if requested == "cpu":
            return "cpu"
        free_mb = vram_free_mb()
        if requested == "cuda":
            if free_mb is not None and free_mb < self.settings.min_free_vram_mb:
                raise AudioBackendError(
                    f"SoulX-Singer needs at least {self.settings.min_free_vram_mb} MB free VRAM; "
                    f"currently {free_mb} MB is free."
                )
            return "cuda"
        if free_mb is not None and free_mb >= self.settings.min_free_vram_mb:
            return "cuda"
        return "cpu"

    def sing_metadata(
        self,
        *,
        target_metadata_path: str,
        prompt_wav_path: str | None = None,
        prompt_metadata_path: str | None = None,
        device: Literal["auto", "cuda", "cpu"] = "auto",
        control: Literal["score", "melody"] = "score",
        pitch_shift: int = 0,
        auto_shift: bool = True,
        output_format: Literal["wav", "mp3"] = "mp3",
        normalize_loudness: bool = True,
    ) -> dict[str, Any]:
        target = validate_file(target_metadata_path, {".json"})
        prompt_wav = validate_file(
            prompt_wav_path or str(self.settings.soulx_prompt_wav),
            {".wav", ".mp3", ".flac", ".ogg", ".m4a"},
        )
        prompt_metadata = validate_file(
            prompt_metadata_path or str(self.settings.soulx_prompt_metadata),
            {".json"},
        )
        for path in (
            self.settings.soulx_model_path,
            self.settings.soulx_config,
            self.settings.soulx_phoneset,
        ):
            validate_file(path)
        selected_device = self._select_device(device)
        with tempfile.TemporaryDirectory(prefix="soulx-mcp-") as temp:
            save_dir = Path(temp) / "result"
            command = [
                str(self.settings.soulx_python),
                "-m",
                "cli.inference",
                "--device",
                selected_device,
                "--model_path",
                str(self.settings.soulx_model_path),
                "--config",
                str(self.settings.soulx_config),
                "--prompt_wav_path",
                str(prompt_wav),
                "--prompt_metadata_path",
                str(prompt_metadata),
                "--target_metadata_path",
                str(target),
                "--phoneset_path",
                str(self.settings.soulx_phoneset),
                "--save_dir",
                str(save_dir),
                "--control",
                control,
                "--pitch_shift",
                str(int(pitch_shift)),
            ]
            if auto_shift:
                command.append("--auto_shift")
            if selected_device == "cuda":
                command.append("--fp16")
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            env["PATH"] = f"{self.settings.ffmpeg.parent};{env.get('PATH', '')}"
            result = subprocess.run(
                command,
                cwd=self.settings.soulx_home,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.settings.request_timeout_s,
            )
            if result.returncode != 0:
                tail = "\n".join(result.stderr.strip().splitlines()[-12:])
                raise AudioBackendError(f"SoulX-Singer failed:\n{tail}")
            raw = save_dir / "generated.wav"
            if not raw.is_file():
                raise AudioBackendError("SoulX-Singer did not produce generated.wav")
            destination = new_output_path(
                self.settings.output_dir,
                f"sing-{safe_stem(target.stem)}",
                output_format,
            )
            final = convert_audio(
                raw,
                destination,
                self.settings.ffmpeg,
                normalize_loudness=normalize_loudness,
            )
            return {
                "backend": "SoulX-Singer",
                "kind": "singing",
                "path": str(final),
                "duration_seconds": round(probe_duration(final), 3),
                "device": selected_device,
                "control": control,
                "pitch_shift": int(pitch_shift),
                "auto_shift": bool(auto_shift),
            }

    def sing_notes(
        self,
        *,
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
    ) -> dict[str, Any]:
        metadata = build_target_metadata(
            phonemes=phonemes,
            note_pitches=note_pitches,
            durations_ms=durations_ms,
            language=language,
            text=text,
        )
        with tempfile.TemporaryDirectory(prefix="soulx-notes-") as temp:
            target_path = Path(temp) / "target.json"
            target_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            return self.sing_metadata(
                target_metadata_path=str(target_path),
                prompt_wav_path=prompt_wav_path,
                prompt_metadata_path=prompt_metadata_path,
                device=device,
                control="score",
                pitch_shift=pitch_shift,
                auto_shift=auto_shift,
                output_format=output_format,
                normalize_loudness=normalize_loudness,
            )
