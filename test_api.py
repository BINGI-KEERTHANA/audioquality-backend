import asyncio
import wave
from io import BytesIO

import httpx

from app import main
from app.config import Settings

app = main.app


def make_wav(duration_seconds: float, sample_rate: int = 8_000) -> bytes:
    """Create a silent mono 16-bit WAV file for API testing."""
    frame_count = int(duration_seconds * sample_rate)
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count)
    return buffer.getvalue()


def post_analyze(files: dict[str, tuple[str, bytes, str]]) -> httpx.Response:
    """Call the ASGI app without relying on Starlette's sync test client."""

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post("/analyze", files=files)

    return asyncio.run(send_request())


def test_analyze_returns_wav_duration() -> None:
    response = post_analyze(
        files={"file": ("sample.wav", make_wav(1.0), "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "filename": "sample.wav",
        "duration_seconds": 1.0,
        "loudness_score": 0.0,
        "loudness_classification": "Too Quiet",
        "leading_silence_seconds": 1.0,
        "trailing_silence_seconds": 1.0,
        "total_silence_seconds": 1.0,
        "silence_score": 0.0,
        "silence_classification": "Poor",
        "noise_score": 100.0,
        "noise_level_db": -60.0,
        "noise_classification": "Excellent",
        "clipping_percentage": 0.0,
        "clipping_score": 100.0,
        "clipping_classification": "Excellent",
        "overall_quality_score": 55.0,
        "recommendation": "Re-record",
    }


def test_analyze_rejects_non_wav_file() -> None:
    response = post_analyze(
        files={"file": ("sample.mp3", b"audio", "audio/mpeg")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Only WAV files are supported."


def test_analyze_rejects_invalid_wav_data() -> None:
    response = post_analyze(
        files={"file": ("invalid.wav", b"not a WAV file", "audio/wav")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "The uploaded file is not a valid WAV audio file."
    )


def test_analyze_rejects_oversized_upload(monkeypatch) -> None:
    monkeypatch.setattr(
        main, "settings", Settings(max_upload_bytes=10, log_level="INFO")
    )

    response = post_analyze(
        files={"file": ("sample.wav", b"more than ten bytes", "audio/wav")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Upload exceeds the 10-byte size limit."


def test_health_returns_documented_response() -> None:
    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.get("/health")

    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_allows_the_local_frontend_origin() -> None:
    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.options(
                "/analyze",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "POST",
                },
            )

    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_api_allows_the_port_5174_frontend_origin() -> None:
    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.options(
                "/analyze",
                headers={
                    "Origin": "http://127.0.0.1:5174",
                    "Access-Control-Request-Method": "POST",
                },
            )

    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5174"


def test_api_allows_the_active_vite_origin() -> None:
    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.options(
                "/analyze",
                headers={
                    "Origin": "http://localhost:5177",
                    "Access-Control-Request-Method": "POST",
                },
            )

    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5177"
