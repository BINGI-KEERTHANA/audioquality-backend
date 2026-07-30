"""RMS loudness analysis for decoded WAV recordings."""

from dataclasses import dataclass

import librosa
import numpy as np

from app.services.audio_analysis import DecodedAudio, decode_audio

QUIET_THRESHOLD_DBFS = -30.0
LOUD_THRESHOLD_DBFS = -8.0
MIN_SCORE_DBFS = -60.0


@dataclass(frozen=True)
class LoudnessAnalysis:
    """Normalized RMS loudness results for one recording."""

    score: float
    classification: str


def calculate_rms_loudness(audio_bytes: bytes) -> LoudnessAnalysis:
    """Return a 0-100 RMS loudness score and a human-readable classification.

    RMS energy is calculated with ``librosa.feature.rms``. The resulting dBFS
    level is normalized from -60 dBFS (score 0) to 0 dBFS (score 100).
    """
    return calculate_rms_loudness_from_audio(decode_audio(audio_bytes))


def calculate_rms_loudness_from_audio(audio: DecodedAudio) -> LoudnessAnalysis:
    """Calculate RMS loudness from already-decoded audio."""
    frame_length = min(2_048, audio.samples.shape[-1])
    rms_energy = float(
        np.mean(
            librosa.feature.rms(
                y=audio.samples, frame_length=frame_length, center=False
            )
        )
    )
    rms_dbfs = 20 * np.log10(max(rms_energy, np.finfo(float).tiny))
    score = float(np.clip((rms_dbfs - MIN_SCORE_DBFS) / -MIN_SCORE_DBFS * 100, 0, 100))

    if rms_dbfs < QUIET_THRESHOLD_DBFS:
        classification = "Too Quiet"
    elif rms_dbfs > LOUD_THRESHOLD_DBFS:
        classification = "Too Loud"
    else:
        classification = "Good"

    return LoudnessAnalysis(score=round(score, 2), classification=classification)
