import struct
import wave
from io import BytesIO

import pytest

from app.services.loudness_analysis import calculate_rms_loudness


def make_constant_wav(amplitude: float, sample_rate: int = 8_000) -> bytes:
    """Create a one-second mono 16-bit WAV at a constant amplitude."""
    sample_value = int(amplitude * 32_767)
    frames = struct.pack("<h", sample_value) * sample_rate
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)
    return buffer.getvalue()


def test_rms_loudness_classifies_silence_as_too_quiet() -> None:
    result = calculate_rms_loudness(make_constant_wav(0.0))

    assert result.score == 0.0
    assert result.classification == "Too Quiet"


def test_rms_loudness_classifies_moderate_signal_as_good() -> None:
    result = calculate_rms_loudness(make_constant_wav(0.1))

    assert result.score == pytest.approx(66.67, abs=0.1)
    assert result.classification == "Good"


def test_rms_loudness_classifies_strong_signal_as_too_loud() -> None:
    result = calculate_rms_loudness(make_constant_wav(0.8))

    assert result.score > 90
    assert result.classification == "Too Loud"
