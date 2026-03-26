from backend.adaptation import AdaptiveSoundEngine, SensorSnapshot


def test_focus_mode_after_dwell():
    engine = AdaptiveSoundEngine(dwell_required=2)
    snap = SensorSnapshot(
        typing_cpm=220,
        typing_variability=0.15,
        mouse_speed=180,
        posture_score=0.85,
        eye_focus_score=0.9,
        stress_self_report=0.1,
    )
    assert engine.infer_mode(snap) == "neutral"
    assert engine.infer_mode(snap) == "focus"


def test_relax_mode_when_stressed():
    engine = AdaptiveSoundEngine(dwell_required=1)
    snap = SensorSnapshot(
        typing_cpm=60,
        typing_variability=0.8,
        mouse_speed=1500,
        posture_score=0.2,
        eye_focus_score=0.2,
        stress_self_report=1.0,
    )
    assert engine.infer_mode(snap) == "relax"
