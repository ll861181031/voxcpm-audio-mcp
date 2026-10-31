from voxcpm_audio_mcp.metadata import build_target_metadata


def test_build_twinkle_metadata():
    phonemes = [
        "<SP>",
        "zh_yi1", "zh_shan3", "zh_yi1", "zh_shan3",
        "zh_liang4", "zh_jing1", "zh_jing1",
        "<SP>",
        "zh_man3", "zh_tian1", "zh_dou1", "zh_shi4",
        "zh_xiao3", "zh_xing1", "zh_xing1",
    ]
    pitches = [0, 60, 60, 67, 67, 69, 69, 67, 0, 65, 65, 64, 64, 62, 62, 60]
    durations = [200, 350, 350, 350, 350, 350, 350, 500, 300, 350, 350, 350, 350, 350, 350, 600]
    result = build_target_metadata(
        phonemes=phonemes,
        note_pitches=pitches,
        durations_ms=durations,
        text="<SP> 一 闪 一 闪 亮 晶 晶 <SP> 满 天 都 是 小 星 星",
    )
    assert result[0]["time"] == [0, 5800]
    assert len(result[0]["duration"].split()) == len(phonemes)
    assert len(result[0]["note_pitch"].split()) == len(phonemes)
    assert result[0]["note_type"].split()[0] == "1"


def test_rejects_mismatched_lengths():
    import pytest

    with pytest.raises(ValueError):
        build_target_metadata(
            phonemes=["zh_ni3"],
            note_pitches=[60, 62],
            durations_ms=[300],
        )
