from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class SensorSnapshot:
    typing_cpm: float
    typing_variability: float
    mouse_speed: float
    posture_score: float
    eye_focus_score: float
    stress_self_report: float


@dataclass
class AdaptationState:
    current_mode: str = "neutral"
    history: List[str] = field(default_factory=list)


class AdaptiveSoundEngine:
    """Simple rules engine with hysteresis for adaptive soundscape mode selection."""

    def __init__(self, dwell_required: int = 3) -> None:
        self.state = AdaptationState()
        self._candidate_buffer: List[str] = []
        self._dwell_required = dwell_required

    def infer_mode(self, snapshot: SensorSnapshot) -> str:
        focus_score = self._focus_score(snapshot)
        stress_score = self._stress_score(snapshot)

        if stress_score >= 0.7:
            candidate = "relax"
        elif focus_score >= 0.65 and stress_score < 0.5:
            candidate = "focus"
        else:
            candidate = "neutral"

        self._candidate_buffer.append(candidate)
        if len(self._candidate_buffer) > self._dwell_required:
            self._candidate_buffer.pop(0)

        if (
            len(self._candidate_buffer) == self._dwell_required
            and len(set(self._candidate_buffer)) == 1
            and self._candidate_buffer[-1] != self.state.current_mode
        ):
            self.state.current_mode = self._candidate_buffer[-1]
            self.state.history.append(self.state.current_mode)

        return self.state.current_mode

    @staticmethod
    def _focus_score(snapshot: SensorSnapshot) -> float:
        typing_consistency = max(0.0, 1.0 - snapshot.typing_variability)
        typing_level = min(snapshot.typing_cpm / 300.0, 1.0)
        scores = [
            typing_consistency * 0.3,
            typing_level * 0.2,
            snapshot.posture_score * 0.25,
            snapshot.eye_focus_score * 0.25,
        ]
        return max(0.0, min(sum(scores), 1.0))

    @staticmethod
    def _stress_score(snapshot: SensorSnapshot) -> float:
        agitation = min(snapshot.mouse_speed / 1000.0, 1.0)
        posture_drop = max(0.0, 1.0 - snapshot.posture_score)
        scores = [
            snapshot.stress_self_report * 0.5,
            agitation * 0.25,
            posture_drop * 0.15,
            snapshot.typing_variability * 0.1,
        ]
        return max(0.0, min(sum(scores), 1.0))


def mode_to_audio_params(mode: str) -> dict:
    presets = {
        "focus": {
            "volume": 0.28,
            "tempo": 62,
            "brightness": 0.35,
            "texture": "brown_noise",
            "transition_ms": 18000,
        },
        "neutral": {
            "volume": 0.22,
            "tempo": 55,
            "brightness": 0.5,
            "texture": "pink_noise",
            "transition_ms": 20000,
        },
        "relax": {
            "volume": 0.18,
            "tempo": 48,
            "brightness": 0.25,
            "texture": "ocean",
            "transition_ms": 24000,
        },
    }
    return presets.get(mode, presets["neutral"])
