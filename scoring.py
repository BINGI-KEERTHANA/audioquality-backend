"""Overall audio-quality scoring from individual analysis results."""

from dataclasses import dataclass

DURATION_WEIGHT = 0.10
LOUDNESS_WEIGHT = 0.25
SILENCE_WEIGHT = 0.20
NOISE_WEIGHT = 0.25
CLIPPING_WEIGHT = 0.20
MIN_ANALYSIS_DURATION_SECONDS = 1.0


@dataclass(frozen=True)
class ScoringConfig:
    """Weights and recommendation thresholds for overall quality scoring."""

    duration_weight: float = DURATION_WEIGHT
    loudness_weight: float = LOUDNESS_WEIGHT
    silence_weight: float = SILENCE_WEIGHT
    noise_weight: float = NOISE_WEIGHT
    clipping_weight: float = CLIPPING_WEIGHT
    min_analysis_duration_seconds: float = MIN_ANALYSIS_DURATION_SECONDS
    accept_threshold: float = 80.0
    review_threshold: float = 60.0

    def __post_init__(self) -> None:
        weights = (
            self.duration_weight,
            self.loudness_weight,
            self.silence_weight,
            self.noise_weight,
            self.clipping_weight,
        )
        if any(weight < 0 for weight in weights) or abs(sum(weights) - 1) > 1e-9:
            raise ValueError("Scoring weights must be non-negative and sum to 1.")
        if self.min_analysis_duration_seconds <= 0:
            raise ValueError("Minimum analysis duration must be positive.")
        if not 0 <= self.review_threshold <= self.accept_threshold <= 100:
            raise ValueError("Recommendation thresholds must be ordered within 0-100.")


DEFAULT_SCORING_CONFIG = ScoringConfig()


@dataclass(frozen=True)
class OverallQuality:
    """Combined quality score and the corresponding next-step recommendation."""

    score: float
    recommendation: str


def calculate_overall_quality(
    *,
    duration_seconds: float,
    loudness_score: float,
    silence_score: float,
    noise_score: float,
    clipping_score: float,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> OverallQuality:
    """Combine analysis scores into a 0-100 score and recommended action.

    Duration receives 10% of the result and reaches its full score at one
    second, ensuring very short recordings are flagged without penalising
    longer recordings. The remaining weights prioritise intelligibility and
    recording defects: loudness and noise 25% each, silence 20%, clipping 20%.
    """
    duration_score = min(
        max(duration_seconds, 0) / config.min_analysis_duration_seconds * 100, 100
    )
    weighted_score = (
        duration_score * config.duration_weight
        + _clamp_score(loudness_score) * config.loudness_weight
        + _clamp_score(silence_score) * config.silence_weight
        + _clamp_score(noise_score) * config.noise_weight
        + _clamp_score(clipping_score) * config.clipping_weight
    )
    score = float(round(weighted_score, 2))

    if score >= config.accept_threshold:
        recommendation = "Accept"
    elif score >= config.review_threshold:
        recommendation = "Review"
    else:
        recommendation = "Re-record"

    return OverallQuality(score=score, recommendation=recommendation)


def _clamp_score(score: float) -> float:
    """Keep a component score inside the scoring engine's 0-100 range."""
    return min(max(score, 0), 100)
