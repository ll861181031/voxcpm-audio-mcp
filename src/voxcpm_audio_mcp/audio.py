from __future__ import annotations

import re
import shutil
import subprocess
import json
from datetime import datetime, timezone
import tempfile
import time
import urllib.request
from pathlib import Path
import math


def validate_file(path: str | Path, suffixes: set[str] | None = None) -> Path:
    value = Path(path).expanduser().resolve()
    if not value.is_file():
        raise FileNotFoundError(f"File not found: {value}")
    if suffixes and value.suffix.lower() not in suffixes:
        allowed = ", ".join(sorted(suffixes))
        raise ValueError(f"Unsupported file type {value.suffix!r}; expected: {allowed}")
    return value


def safe_stem(value: str, fallback: str = "audio") -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", value, flags=re.UNICODE).strip("_")
    return (cleaned[:48] or fallback)


def new_output_path(output_dir: Path, stem: str, suffix: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = suffix.lower().lstrip(".")
    if suffix not in {"wav", "mp3"}:
        raise ValueError("output_format must be wav or mp3")
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return output_dir / f"{safe_stem(stem)}_{timestamp}.{suffix}"


def _run(command: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def convert_audio(
    source: str | Path,
    destination: str | Path,
    ffmpeg: str | Path,
    *,
    normalize_loudness: bool = True,
    sample_rate: int = 48000,
    timeout: int = 120,
) -> Path:
    source = validate_file(source, {".wav", ".mp3", ".flac", ".ogg", ".m4a"})
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = validate_file(ffmpeg, {".exe"})
    suffix = destination.suffix.lower()
    if suffix not in {".wav", ".mp3"}:
        raise ValueError("destination must end in .wav or .mp3")

    filters = []
    if normalize_loudness:
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=10")
    command = [str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", "-i", str(source)]
    if filters:
        command.extend(["-af", ",".join(filters)])
    command.extend(["-ar", str(sample_rate)])
    if suffix == ".wav":
        command.extend(["-c:a", "pcm_s24le"])
    else:
        command.extend(["-codec:a", "libmp3lame", "-b:a", "192k"])
    command.append(str(destination))
    _run(command, timeout=timeout)
    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError(f"Audio conversion failed: {destination}")
    return destination


def probe_duration(path: str | Path, ffprobe: str | Path | None = None) -> float:
    path = validate_file(path)
    if ffprobe is None:
        import soundfile as sf

        with sf.SoundFile(str(path)) as handle:
            return float(len(handle) / handle.samplerate)
    result = _run(
        [
            str(ffprobe),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    return float(result.stdout.strip())


def concat_wavs(
    paths: list[Path],
    pauses_ms: list[int],
    destination: Path,
    *,
    sample_rate: int = 48000,
) -> Path:
    import numpy as np
    import soundfile as sf

    if len(paths) != len(pauses_ms):
        raise ValueError("paths and pauses_ms must have the same length")
    chunks = []
    for index, path in enumerate(paths):
        audio, sr = sf.read(str(path), dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sr != sample_rate:
            raise ValueError(f"Unexpected sample rate {sr} in {path}")
        chunks.append(audio)
        if index < len(paths) - 1 and pauses_ms[index] > 0:
            chunks.append(np.zeros(int(sample_rate * pauses_ms[index] / 1000), dtype=np.float32))
    destination.parent.mkdir(parents=True, exist_ok=True)
    sf.write(destination, np.concatenate(chunks), sample_rate, subtype="PCM_24")
    return destination


def estimate_f0(audio, sample_rate: int) -> float | None:
    import librosa
    import numpy as np

    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    f0, voiced_flags, _ = librosa.pyin(
        audio,
        fmin=60,
        fmax=500,
        sr=sample_rate,
        frame_length=2048,
        hop_length=512,
    )
    voiced = f0[np.isfinite(f0) & voiced_flags]
    if voiced.size == 0:
        return None
    return float(np.median(voiced))


def shape_voice(
    source: str | Path,
    destination: str | Path,
    *,
    target_f0: float | None = None,
    tempo: float = 1.0,
) -> dict:
    import librosa
    import numpy as np
    import soundfile as sf

    if target_f0 is not None and not 50 <= target_f0 <= 500:
        raise ValueError("target_f0 must be between 50 and 500 Hz")
    if not 0.5 <= tempo <= 2.0:
        raise ValueError("tempo must be between 0.5 and 2.0")

    source_path = validate_file(source, {".wav", ".mp3", ".flac", ".ogg", ".m4a"})
    destination_path = Path(destination).resolve()
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    audio, sample_rate = sf.read(str(source_path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if audio.size == 0:
        raise ValueError("audio is empty")

    measured_f0 = estimate_f0(audio, sample_rate)
    pitch_shift_semitones = None
    if target_f0 is not None:
        if measured_f0 is None:
            raise ValueError("could not estimate source F0")
        pitch_shift_semitones = 12 * math.log2(target_f0 / measured_f0)
        audio = librosa.effects.pitch_shift(
            y=audio,
            sr=sample_rate,
            n_steps=pitch_shift_semitones,
        )

    if tempo != 1.0:
        audio = librosa.effects.time_stretch(y=audio, rate=tempo)

    sf.write(destination_path, audio, sample_rate, subtype="PCM_24")
    return {
        "measured_f0": measured_f0,
        "target_f0": target_f0,
        "pitch_shift_semitones": pitch_shift_semitones,
        "tempo": tempo,
        "sample_rate": sample_rate,
        "duration_seconds": round(len(audio) / sample_rate, 3),
    }


def vram_free_mb(nvidia_smi: str = "nvidia-smi") -> int | None:
    return vram_info(nvidia_smi)["free_mb"]


def vram_info(nvidia_smi: str = "nvidia-smi") -> dict:
    try:
        import pynvml

        pynvml.nvmlInit()
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            free_mb = int(pynvml.nvmlDeviceGetMemoryInfo(handle).free // 1024**2)
            return {"free_mb": free_mb, "error": None, "path": "NVML"}
        finally:
            pynvml.nvmlShutdown()
    except Exception:
        pass

    try:
        import shutil
        from pathlib import Path
        import subprocess

        executable = shutil.which(nvidia_smi) or nvidia_smi
        if not Path(executable).is_file() and Path(r"C:\Windows\System32\nvidia-smi.exe").is_file():
            executable = r"C:\Windows\System32\nvidia-smi.exe"
        command = [
            executable,
            "--query-gpu=memory.free",
            "--format=csv,noheader,nounits",
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return {
                "free_mb": None,
                "error": f"nvidia-smi exited {result.returncode}: {result.stderr.strip()}",
                "path": executable,
            }
        return {"free_mb": int(result.stdout.strip().splitlines()[0]), "error": None, "path": executable}
    except Exception:
        import traceback

        return {"free_mb": None, "error": traceback.format_exc(), "path": nvidia_smi}


def http_ready(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/config", timeout=timeout):
            return True
    except Exception:
        return False


def append_log(log_dir: Path, event: str, data: dict) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **data,
    }
    path = log_dir / "mcp.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def copy_result(source: str | Path, destination: Path) -> Path:
    source = validate_file(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination
