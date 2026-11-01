from voxcpm_audio_mcp.server import resolve_speech_preset


def test_speech_defaults_match_expressive_preset():
    resolved = resolve_speech_preset(
        voice_preset=None,
        control_instruction=None,
        reference_audio_path=None,
        cfg_value=None,
        inference_timesteps=None,
        target_f0=None,
        tempo=None,
    )

    assert resolved["target_f0"] == 260
    assert resolved["tempo"] == 1.05
    assert resolved["cfg_value"] == 2.3
    assert resolved["inference_timesteps"] == 16
