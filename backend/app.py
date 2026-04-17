from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.adaptation import AdaptiveSoundEngine, SensorSnapshot, mode_to_audio_params

app = FastAPI(title="Adaptive Soundscapes API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = AdaptiveSoundEngine(dwell_required=3)


class SensorPayload(BaseModel):
    typing_cpm: float = Field(ge=0, le=800)
    typing_variability: float = Field(ge=0, le=1)
    mouse_speed: float = Field(ge=0, le=3000)
    posture_score: float = Field(ge=0, le=1)
    eye_focus_score: float = Field(ge=0, le=1)
    stress_self_report: float = Field(ge=0, le=1)


@app.post("/api/adapt")
def adapt(payload: SensorPayload):
    snapshot = SensorSnapshot(**payload.model_dump())
    mode = engine.infer_mode(snapshot)
    audio = mode_to_audio_params(mode)
    return {
        "mode": mode,
        "audio": audio,
        "history": engine.state.history[-10:],
    }


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
