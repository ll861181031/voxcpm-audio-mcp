---
name: voxcpm-audio
description: Generate local speech, emotional narration, and exact-melody singing with VoxCPM2 and SoulX-Singer MCP tools.
---

# VoxCPM Audio

Use this skill when the user asks to synthesize speech, clone a local voice, create emotional narration, or generate singing with controlled notes.

## Tool choice

- Use `health` before long jobs to check model paths, FFmpeg, VoxCPM2 readiness, and free VRAM.
- Use `speak` for one sentence or one paragraph.
- Use `speak_segments` for multi-paragraph narration where each paragraph needs a different emotion or pause.
- Use `save_voice_preset` when the user wants to keep a reusable voice.
- Use `sing_metadata` when a SoulX-Singer metadata JSON already exists.
- Use `sing_notes` when the user provides phonemes, MIDI note numbers, and durations.

## Speaking guidance

1. Keep `control_instruction` specific but not contradictory.
2. Include voice age, gender, timbre, emotion, pacing, volume, and pronunciation emphasis.
3. For emotional narration, split by meaning and use `speak_segments`.
4. Prefer `cfg_value` around `2.2` for normal speech and `2.3` to `2.5` for stronger emotion.
5. Use `inference_timesteps` around `14` for speech and `16` to `20` for expressive narration.
6. Do not clone a voice unless the user owns it or has explicit permission.
7. For numeric voice control, use `target_f0`, `tempo`, `cfg_value`, and `inference_timesteps`.
8. Save successful numeric settings with `save_voice_preset` before long sessions.

## Singing guidance

1. Ask for or derive phonemes, MIDI note numbers, and per-note durations.
2. Ensure the three arrays have the same length.
3. Use `<SP>` for rests.
4. Prefer `device=auto`; if VRAM is low, the tool will use CPU.
5. Use `pitch_shift` in semitones if the generated voice is too high or too low.
6. For a complete song, generate short sections first, verify timing and pitch, then assemble.

## GPU and cache

- Run `health` before GPU-heavy work.
- Do not start VoxCPM2 while another training job is using most VRAM.
- Generated audio is written to `AUDIO_OUTPUT_DIR`.
- Logs are written to `MCP_LOG_DIR/mcp.jsonl`.
- Use `scripts/manage_cache.ps1` to inspect or clean old audio.
- Use `scripts/show_logs.ps1` to inspect recent MCP activity.
