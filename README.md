# Audio Quality Assessment Backend

FastAPI service for WAV-based audio-quality analysis. It reports duration, RMS
loudness, silence, background noise, and clipping; additional quality metrics
will be added incrementally.

## Setup

Requires Python 3.10 or newer. Run these commands from this `backend/`
directory.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run locally

```bash
uvicorn app.main:app --reload
```

The interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Endpoint

`POST /analyze` accepts one multipart form field named `file`. The file must be a WAV file.

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "file=@/path/to/audio.wav;type=audio/wav"
```

Current response:

```json
{
  "filename": "audio.wav",
  "duration_seconds": 1.0,
  "loudness_score": 66.67,
  "loudness_classification": "Good",
  "leading_silence_seconds": 0.0,
  "trailing_silence_seconds": 0.0,
  "total_silence_seconds": 0.0,
  "silence_score": 100.0,
  "silence_classification": "Excellent",
  "noise_score": 100.0,
  "noise_level_db": -60.0,
  "noise_classification": "Excellent",
  "clipping_percentage": 0.0,
  "clipping_score": 100.0,
  "clipping_classification": "Excellent",
  "overall_quality_score": 91.67,
  "recommendation": "Accept"
}
```

Status codes:

- `200` — analysis completed.
- `413` — the upload exceeds `MAX_UPLOAD_BYTES`.
- `415` — the form field is not a WAV upload.
- `422` — the file cannot be decoded as valid WAV audio.
- `500` — an unexpected analysis failure occurred; details are logged server-side.

## Configuration

Configuration is supplied through environment variables:

- `MAX_UPLOAD_BYTES`: maximum accepted upload size in bytes (default: `26214400`, or 25 MiB).
- `LOG_LEVEL`: standard Python log level (default: `INFO`).
- `CORS_ORIGINS`: comma-separated allowed browser origins (default:
  `http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5177,http://127.0.0.1:5177`).

For example:

```bash
MAX_UPLOAD_BYTES=10485760 LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

`loudness_score` is the recording's RMS level mapped from -60 dBFS (0) to
0 dBFS (100). The classification is `Too Quiet` below -30 dBFS, `Good` from
-30 dBFS through -8 dBFS, and `Too Loud` above -8 dBFS.

Silence is detected with librosa using a 40 dB threshold below the recording's
peak level. `total_silence_seconds` includes leading, trailing, and internal
silent regions. `silence_score` is the percentage of the recording that is
non-silent: 95–100 is `Excellent`, 80–94.99 is `Good`, 60–79.99 is `Fair`, and
anything lower is `Poor`.

Background noise is estimated from the quietest 10% of librosa RMS frames.
`noise_level_db` is the estimated noise floor in dBFS, capped at -60 dBFS.
`noise_score` maps -60 dBFS or quieter to 100 and -10 dBFS or louder to 0:
85–100 is `Excellent`, 65–84.99 is `Good`, 40–64.99 is `Fair`, and anything
lower is `Poor`.

Clipping is detected with NumPy when an audio sample reaches at least 99% of
full scale. `clipping_percentage` is the percentage of detected samples.
`clipping_score` deducts 20 points per 1% of clipped samples: scores of 99.5+
are `Excellent`, 95–99.49 are `Good`, 80–94.99 are `Fair`, and lower scores
are `Poor`.

## Overall quality score

`overall_quality_score` combines duration (10%), loudness (25%), silence
(20%), background noise (25%), and clipping (20%). Duration reaches its full
component score at one second. A score of 80 or higher returns `Accept`,
60–79.99 returns `Review`, and lower scores return `Re-record`.

## Architecture

```text
app/
├── main.py                 FastAPI routes, validation, error mapping, logging
├── config.py               Environment-based runtime settings
├── models.py               Request/response API contracts
└── services/
    ├── audio_analysis.py   One-time WAV decoding and duration calculation
    ├── loudness_analysis.py
    ├── silence_analysis.py
    ├── noise_analysis.py
    ├── clipping_analysis.py
    └── scoring.py          Configurable weighted overall score
```

The endpoint decodes an upload once and passes the reusable audio data to each
analysis service. Individual service functions also retain byte-upload entry
points for focused unit testing.

## Test

```bash
pytest
```

The suite covers HTTP response and error contracts, each analysis metric,
scoring thresholds/configuration invariants, and upload-size validation.
