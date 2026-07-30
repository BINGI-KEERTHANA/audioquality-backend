"""Clipping detection for decoded WAV recordings."""

from dataclasses import dataclass

import numpy as np

from app.services.audio_analysis import DecodedAudio, decode_audio

CLIPPING_THRESHOLD = 0.99


@dataclass(frozen=True)
class ClippingAnalysis:
    """Clipped-sample percentage and its quality assessment."""

    percentage: float
    score: float
    classification: str


def calculate_clipping(audio_bytes: bytes) -> ClippingAnalysis:
    """Detect near-full-scale samples and assess their clipping severity.

    Samples at 99% of full scale or higher are considered clipped. Each 1% of
    clipped samples deducts 20 points from the 100-point score, so occasional
    clips have a small penalty while sustained clipping quickly becomes Poor.
    Scores of 99.5+ are Excellent, 95+ Good, 80+ Fair, and lower scores Poor.
    """
    return calculate_clipping_from_audio(decode_audio(audio_bytes))


def calculate_clipping_from_audio(audio: DecodedAudio) -> ClippingAnalysis:
    """Detect clipping from already-decoded audio."""
    sample_count = audio.samples.size
    clipped_count = int(np.count_nonzero(np.abs(audio.samples) >= CLIPPING_THRESHOLD))
    clipping_percentage = (
        0.0 if sample_count == 0 else clipped_count / sample_count * 100
    )
    score = float(np.clip(100 - clipping_percentage * 20, 0, 100))

    if score >= 99.5:
        classification = "Excellent"
    elif score >= 95:
        classification = "Good"
    elif score >= 80:
        classification = "Fair"
    else:
        classification = "Poor"

    return ClippingAnalysis(
        percentage=float(round(clipping_percentage, 3)),
        score=float(round(score, 2)),
        classification=classification,
    )
