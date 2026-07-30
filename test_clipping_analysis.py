import struct
import wave
from io import BytesIO

from app.services.clipping_analysis import calculate_clipping


def make_wav(samples: list[float], sample_rate: int = 8_000) -> bytes:
    """Create a mono 16-bit WAV from normalized sample amplitudes."""
    frames = b"".join(
        struct.pack("<h", int(max(-1.0, min(1.0, sample)) * 32_767))
        for sample in samples
    )
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)
    return buffer.getvalue()


def test_clipping_analysis_rates_unclipped_audio_as_excellent() -> None:
    result = calculate_clipping(make_wav([0.5] * 1_000))

    assert result.percentage == 0.0
    assert result.score == 100.0
    assert result.classification == "Excellent"


def test_clipping_analysis_rates_occasional_clips_as_good() -> None:
    result = calculate_clipping(make_wav([1.0] + [0.5] * 999))

    assert result.percentage == 0.1
    assert result.score == 98.0
    assert result.classification == "Good"


def test_clipping_analysis_rates_limited_clipping_as_fair() -> None:
    result = calculate_clipping(make_wav([1.0] * 10 + [0.5] * 990))

    assert result.percentage == 1.0
    assert result.score == 80.0
    assert result.classification == "Fair"


def test_clipping_analysis_rates_sustained_clipping_as_poor() -> None:
    result = calculate_clipping(make_wav([1.0] * 50 + [0.5] * 950))

    assert result.percentage == 5.0
    assert result.score == 0.0
    assert result.classification == "Poor"
