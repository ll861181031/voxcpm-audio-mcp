from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class VoicePresetStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve()

    def _read(self) -> dict:
        if not self.path.is_file():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def list(self) -> dict:
        return self._read()

    def get(self, name: str) -> dict:
        data = self._read()
        if name not in data:
            raise KeyError(f"voice preset not found: {name}")
        return data[name]

    def save(self, name: str, preset: dict, *, overwrite: bool = False) -> dict:
        if not name.strip():
            raise ValueError("preset name must not be empty")
        if "/" in name or "\\" in name:
            raise ValueError("preset name must not contain path separators")

        data = self._read()
        existed = name in data
        if existed and not overwrite:
            raise ValueError(f"voice preset already exists: {name}")

        record = {
            **preset,
            "name": name,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        data[name] = record
        self._write(data)
        return {"name": name, "overwrote": existed, "preset": record}

    def delete(self, name: str) -> dict:
        data = self._read()
        if name not in data:
            raise KeyError(f"voice preset not found: {name}")
        del data[name]
        self._write(data)
        return {"deleted": name}
