from __future__ import annotations

import argparse
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voxcpm_audio_mcp.audio import vram_info  # noqa: E402
from voxcpm_audio_mcp.backends import SoulXSingerBackend, VoxCPMBackend  # noqa: E402
from voxcpm_audio_mcp.config import Settings  # noqa: E402
from voxcpm_audio_mcp.presets import VoicePresetStore  # noqa: E402


settings = Settings.from_env()
speech = VoxCPMBackend(settings)
singing = SoulXSingerBackend(settings)
voice_presets = VoicePresetStore(settings.voice_presets_path)
synthesis_lock = threading.Lock()


def audio_url(path: str) -> str:
    return f"/audio/{quote(Path(path).name)}"


class DebugRequestHandler(BaseHTTPRequestHandler):
    server_version = "VoxCPMDebugWeb/0.5.0"

    def log_message(self, format: str, *args) -> None:
        sys.stdout.write(f"{self.address_string()} - {format % args}\n")

    def _send_json(self, value, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, exc: Exception, status: int = 500) -> None:
        self._send_json({"error": type(exc).__name__, "message": str(exc)}, status)

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            self._send_json({"error": "FileNotFound", "message": str(path)}, 404)
            return
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
        }.get(path.suffix.lower(), "application/octet-stream")
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _health(self) -> dict:
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

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    def do_GET(self) -> None:
        try:
            path = unquote(urlsplit(self.path).path)
            if path == "/api/health":
                self._send_json(self._health())
                return
            if path == "/api/presets":
                self._send_json({"presets": voice_presets.list()})
                return
            if path == "/api/logs":
                log_path = settings.log_dir / "mcp.jsonl"
                lines = log_path.read_text(encoding="utf-8").splitlines() if log_path.is_file() else []
                self._send_json({"lines": lines[-100:]})
                return
            if path.startswith("/audio/"):
                requested = (settings.output_dir / path[len("/audio/"):]).resolve()
                if not requested.is_relative_to(settings.output_dir.resolve()):
                    self._send_json({"error": "InvalidPath", "message": path}, 400)
                    return
                self._send_file(requested)
                return
            if path == "/":
                path = "/index.html"
            requested = (ROOT / "web" / path.lstrip("/")).resolve()
            if not requested.is_relative_to((ROOT / "web").resolve()):
                self._send_json({"error": "InvalidPath", "message": path}, 400)
                return
            self._send_file(requested)
        except Exception as exc:
            self._send_error_json(exc)

    def do_POST(self) -> None:
        try:
            path = unquote(urlsplit(self.path).path)
            body = self._read_body()
            if path == "/api/presets/save":
                result = voice_presets.save(
                    body["name"],
                    {key: value for key, value in body.items() if key not in {"name", "overwrite"}},
                    overwrite=bool(body.get("overwrite", False)),
                )
                self._send_json(result)
                return
            if path == "/api/presets/delete":
                self._send_json(voice_presets.delete(body["name"]))
                return
            if path == "/api/speak":
                with synthesis_lock:
                    result = speech.speak(
                        text=body["text"],
                        control_instruction=body.get("control_instruction", ""),
                        reference_audio_path=body.get("reference_audio_path"),
                        cfg_value=float(body.get("cfg_value", 2.2)),
                        inference_timesteps=int(body.get("inference_timesteps", 14)),
                        target_f0=body.get("target_f0"),
                        tempo=body.get("tempo"),
                        seed=body.get("seed"),
                        output_format=body.get("output_format", "mp3"),
                        normalize_loudness=bool(body.get("normalize_loudness", True)),
                    )
                result["url"] = audio_url(result["path"])
                self._send_json(result)
                return
            if path == "/api/sing":
                with synthesis_lock:
                    result = singing.sing_metadata(
                        target_metadata_path=body["target_metadata_path"],
                        prompt_wav_path=body.get("prompt_wav_path"),
                        prompt_metadata_path=body.get("prompt_metadata_path"),
                        device=body.get("device", "auto"),
                        control=body.get("control", "score"),
                        pitch_shift=int(body.get("pitch_shift", 0)),
                        auto_shift=bool(body.get("auto_shift", True)),
                        output_format=body.get("output_format", "mp3"),
                        normalize_loudness=bool(body.get("normalize_loudness", True)),
                    )
                result["url"] = audio_url(result["path"])
                self._send_json(result)
                return
            self._send_json({"error": "NotFound", "message": path}, 404)
        except Exception as exc:
            self._send_error_json(exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the VoxCPM Audio debug web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8810)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), DebugRequestHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"Debug web UI: {url}")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
