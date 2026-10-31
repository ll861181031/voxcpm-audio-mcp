from __future__ import annotations

from typing import Sequence


def build_target_metadata(
    *,
    phonemes: Sequence[str],
    note_pitches: Sequence[int],
    durations_ms: Sequence[int],
    language: str = "Mandarin",
    text: str | None = None,
    index: str = "target",
) -> list[dict]:
    if not phonemes:
        raise ValueError("phonemes must not be empty")
    if len(phonemes) != len(note_pitches) or len(phonemes) != len(durations_ms):
        raise ValueError("phonemes, note_pitches, and durations_ms must have the same length")
    if any(value < 0 for value in durations_ms):
        raise ValueError("durations_ms must be non-negative")
    if any(not 0 <= value <= 127 for value in note_pitches):
        raise ValueError("note_pitches must be MIDI values between 0 and 127")

    total_ms = int(sum(durations_ms))
    if total_ms <= 0:
        raise ValueError("total duration must be greater than zero")
    text_value = text.strip() if text else " ".join(phonemes)
    note_type = [1 if phoneme == "<SP>" else 2 for phoneme in phonemes]
    return [
        {
            "index": index,
            "language": language,
            "time": [0, total_ms],
            "duration": " ".join(f"{value / 1000:.3f}" for value in durations_ms),
            "text": text_value,
            "phoneme": " ".join(phonemes),
            "note_pitch": " ".join(str(value) for value in note_pitches),
            "note_type": " ".join(str(value) for value in note_type),
        }
    ]
