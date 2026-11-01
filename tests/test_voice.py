import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from voxcpm_audio_mcp.audio import estimate_f0, shape_voice
from voxcpm_audio_mcp.presets import VoicePresetStore


def test_shape_voice_changes_pitch_and_duration():
    with tempfile.TemporaryDirectory() as temp:
        source = Path(temp) / "source.wav"
        destination = Path(temp) / "destination.wav"
        sample_rate = 24000
        time = np.arange(sample_rate, dtype=np.float32) / sample_rate
        audio = 0.2 * np.sin(2 * np.pi * 220 * time)
        sf.write(source, audio, sample_rate, subtype="PCM_16")

        result = shape_voice(
            source,
            destination,
            target_f0=330,
            tempo=1.25,
        )

        shaped, shaped_rate = sf.read(destination, dtype="float32")
        measured = estimate_f0(shaped, shaped_rate)
        assert abs(measured - 330) < 8
        assert result["duration_seconds"] < 0.9


def test_voice_preset_store_round_trip():
    with tempfile.TemporaryDirectory() as temp:
        store = VoicePresetStore(Path(temp) / "presets.json")
        saved = store.save(
            "cute-female",
            {
                "target_f0": 260,
                "tempo": 1.05,
                "cfg_value": 2.3,
                "inference_timesteps": 16,
                "control_instruction": "年轻可爱女声，清亮甜美。",
            },
        )
        assert saved["name"] == "cute-female"
        assert store.get("cute-female")["target_f0"] == 260
        assert store.list()["cute-female"]["tempo"] == 1.05
        assert store.delete("cute-female") == {"deleted": "cute-female"}
