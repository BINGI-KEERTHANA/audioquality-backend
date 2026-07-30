import struct
import wave
from io import BytesIO

from app.services.noise_analysis import calculate_background_noise


def make_wav(segments: list[tuple[float, float]], sample_rate: int = 8_000) -> bytes:
    """Create a WAV from (duration_seconds, constant amplitude) segments."""
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


def test_noise_analysis_rates_silence_as_excellent() -> None:
    result = calculate_background_noise(make_wav([(1.0, 0.0)]))

    assert result.level_db == -60.0
    assert result.score == 100.0
    assert result.classification == "Excellent"


def test_noise_analysis_rates_low_noise_as_good() -> None:
    result = calculate_background_noise(make_wav([(1.0, 0.005), (1.0, 0.5)]))

    assert -48 < result.level_db < -44
    assert 65 <= result.score < 85
    assert result.classification == "Good"


def test_noise_analysis_rates_moderate_noise_as_fair() -> None:
    result = calculate_background_noise(make_wav([(1.0, 0.02), (1.0, 0.5)]))

    assert -36 < result.level_db < -32
    assert 40 <= result.score < 65
    assert result.classification == "Fair"


def test_noise_analysis_rates_high_noise_as_poor() -> None:
    result = calculate_background_noise(make_wav([(1.0, 0.2), (1.0, 0.5)]))

    assert result.level_db > -16
    assert result.score < 40
    assert result.classification == "Poor"
