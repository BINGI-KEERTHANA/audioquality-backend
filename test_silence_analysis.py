import struct
import wave
from io import BytesIO

import pytest

from app.services.silence_analysis import calculate_silence


def make_wav(segments: list[tuple[float, float]], sample_rate: int = 8_000) -> bytes:
    """Create a WAV from (duration_seconds, amplitude) segments."""
    frames = b"".join(
        struct.pack("<h", int(amplitude * 32_767)) * int(duration_seconds * sample_rate)
        for duration_seconds, amplitude in segments
    )
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)
    return buffer.getvalue()


def test_silence_analysis_detects_no_silence() -> None:
    result = calculate_silence(make_wav([(1.0, 0.5)]))

    assert result.leading_silence_seconds == 0.0
    assert result.trailing_silence_seconds == 0.0
    assert result.total_silence_seconds == 0.0
    assert result.score == 100.0
    assert result.classification == "Excellent"


def test_silence_analysis_detects_a_fully_silent_recording() -> None:
    result = calculate_silence(make_wav([(1.0, 0.0)]))

    assert result.leading_silence_seconds == 1.0
    assert result.trailing_silence_seconds == 1.0
    assert result.total_silence_seconds == 1.0
    assert result.score == 0.0
    assert result.classification == "Poor"


def test_silence_analysis_detects_leading_silence() -> None:
    result = calculate_silence(make_wav([(0.5, 0.0), (1.0, 0.5)]))

    assert result.leading_silence_seconds == pytest.approx(0.5, abs=0.1)
    assert result.trailing_silence_seconds == pytest.approx(0.0, abs=0.1)
    assert result.total_silence_seconds == pytest.approx(0.5, abs=0.1)
    assert result.classification == "Fair"


def test_silence_analysis_detects_trailing_silence() -> None:
    result = calculate_silence(make_wav([(1.0, 0.5), (0.5, 0.0)]))

    assert result.leading_silence_seconds == pytest.approx(0.0, abs=0.1)
    assert result.trailing_silence_seconds == pytest.approx(0.5, abs=0.1)
    assert result.total_silence_seconds == pytest.approx(0.5, abs=0.1)
    assert result.classification == "Fair"


def test_silence_analysis_rates_long_silence_as_poor() -> None:
    result = calculate_silence(make_wav([(2.0, 0.0), (0.5, 0.5)]))

    assert result.total_silence_seconds == pytest.approx(2.0, abs=0.1)
    assert result.score == pytest.approx(20.0, abs=4.0)
    assert result.classification == "Poor"
