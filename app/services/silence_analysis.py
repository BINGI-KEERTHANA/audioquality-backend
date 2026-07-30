"""Silence detection for decoded WAV recordings."""

from dataclasses import dataclass

import librosa
import numpy as np

from app.services.audio_analysis import DecodedAudio, decode_audio

SILENCE_THRESHOLD_DB = 40


@dataclass(frozen=True)
class SilenceAnalysis:
    """Silence durations and an overall recording-silence assessment."""

    leading_silence_seconds: float
    trailing_silence_seconds: float
    total_silence_seconds: float
    score: float
    classification: str


def calculate_silence(audio_bytes: bytes) -> SilenceAnalysis:
    """Detect silent regions with librosa and return their durations.

    A frame is silent when it is at least 40 dB below the recording's peak.
    The score is the percentage of the recording that is non-silent:
    no silence is 100, while a fully silent recording is 0. Scores of 95+ are
    Excellent, 80+ Good, 60+ Fair, and lower scores are Poor.
    """
    return calculate_silence_from_audio(decode_audio(audio_bytes))


def calculate_silence_from_audio(audio: DecodedAudio) -> SilenceAnalysis:
    """Detect silent regions from already-decoded audio."""
    samples = audio.samples
    sample_rate = audio.sample_rate
    sample_count = samples.shape[-1]
    duration_seconds = sample_count / sample_rate if sample_rate else 0.0
    if np.max(np.abs(samples), initial=0.0) == 0:
        non_silent_intervals = np.empty((0, 2), dtype=int)
    else:
        non_silent_intervals = librosa.effects.split(
            samples,
            top_db=SILENCE_THRESHOLD_DB,
            frame_length=min(512, sample_count),
            hop_length=max(1, min(512, sample_count) // 4),
        )

    if len(non_silent_intervals) == 0:
        leading_silence = duration_seconds
        trailing_silence = duration_seconds
        total_silence = duration_seconds
    else:
        leading_silence = non_silent_intervals[0, 0] / sample_rate
        trailing_silence = (sample_count - non_silent_intervals[-1, 1]) / sample_rate
        non_silent_samples = sum(end - start for start, end in non_silent_intervals)
        total_silence = (sample_count - non_silent_samples) / sample_rate

    # Clamp rounding artefacts so every response stays within valid bounds.
    total_silence = float(np.clip(total_silence, 0, duration_seconds))
    score = (
        100.0 if duration_seconds == 0 else (1 - total_silence / duration_seconds) * 100
    )
    score = float(np.clip(score, 0, 100))

    if score >= 95:
        classification = "Excellent"
    elif score >= 80:
        classification = "Good"
    elif score >= 60:
        classification = "Fair"
    else:
        classification = "Poor"

    return SilenceAnalysis(
        leading_silence_seconds=float(round(leading_silence, 3)),
        trailing_silence_seconds=float(round(trailing_silence, 3)),
        total_silence_seconds=float(round(total_silence, 3)),
        score=float(round(score, 2)),
        classification=classification,
    )
