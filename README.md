# Adaptive Soundscapes for Productivity

A full-stack prototype that adapts ambient sound parameters in real time based on productivity and stress signals.

## Features

- Passive sensing from browser events:
  - typing cadence (CPM + variability)
  - mouse movement speed
- Manual sliders for posture, eye focus, and stress self-report.
- Adaptive mode inference with hysteresis:
  - `focus`
  - `neutral`
  - `relax`
- Gradual Web Audio transitions (volume + filter brightness).

## Architecture

- **Backend**: FastAPI rules engine and adaptation endpoint.
- **Frontend**: Single-page UI with event capture + ambient audio synthesis.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

Open: `http://127.0.0.1:8000`

## API

### `POST /api/adapt`

Request body:

```json
{
  "typing_cpm": 140,
  "typing_variability": 0.3,
  "mouse_speed": 250,
  "posture_score": 0.7,
  "eye_focus_score": 0.75,
  "stress_self_report": 0.2
}
```

Response:

```json
{
  "mode": "focus",
  "audio": {
    "volume": 0.28,
    "tempo": 62,
    "brightness": 0.35,
    "texture": "brown_noise",
    "transition_ms": 18000
  },
  "history": ["focus"]
}
```

## Tests

```bash
pytest -q
```
