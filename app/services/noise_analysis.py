"""Background-noise estimation for decoded WAV recordings."""

from dataclasses import dataclass

import librosa
import numpy as np

from app.services.audio_analysis import DecodedAudio, decode_audio

NOISE_PERCENTILE = 10
MIN_NOISE_LEVEL_DBFS = -60.0
MAX_NOISE_LEVEL_DBFS = -10.0


@dataclass(frozen=True)
class NoiseAnalysis:
    """Estimated background-noise floor and its quality assessment."""

    score: float
    level_db: float
    classification: str


def calculate_background_noise(audio_bytes: bytes) -> NoiseAnalysis:
    """Estimate the background-noise floor from the recording's quietest frames.

    The 10th percentile of librosa RMS frame energies is used as a noise-floor
    estimate. The score maps -60 dBFS (or quieter) to 100 and -10 dBFS (or
    louder) to 0, so lower background noise produces a higher score. Scores
    of 85+ are Excellent, 65+ Good, 40+ Fair, and lower scores are Poor.
    """
    return calculate_background_noise_from_audio(decode_audio(audio_bytes))


def calculate_background_noise_from_audio(audio: DecodedAudio) -> NoiseAnalysis:
    """Estimate the noise floor from already-decoded audio."""
    frame_length = min(512, audio.samples.shape[-1])
    hop_length = max(1, frame_length // 4)
    frame_rms = librosa.feature.rms(
        y=audio.samples,
        frame_length=frame_length,
        hop_length=hop_length,
        center=False,
    )
    noise_rms = float(np.percentile(frame_rms, NOISE_PERCENTILE))
    noise_level_db = 20 * np.log10(max(noise_rms, np.finfo(float).tiny))
    noise_level_db = float(max(noise_level_db, MIN_NOISE_LEVEL_DBFS))

    score = (
        (MAX_NOISE_LEVEL_DBFS - noise_level_db)
        / (MAX_NOISE_LEVEL_DBFS - MIN_NOISE_LEVEL_DBFS)
        * 100
    )
    score = float(np.clip(score, 0, 100))

    if score >= 85:
        classification = "Excellent"
    elif score >= 65:
        classification = "Good"
    elif score >= 40:
        classification = "Fair"
    else:
        classification = "Poor"

    return NoiseAnalysis(
        score=float(round(score, 2)),
        level_db=float(round(noise_level_db, 2)),
        classification=classification,
    )
