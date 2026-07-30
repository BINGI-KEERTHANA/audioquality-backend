import pytest

from app.services.scoring import ScoringConfig, calculate_overall_quality


def test_overall_quality_accepts_strong_recording() -> None:
    result = calculate_overall_quality(
        duration_seconds=2.0,
        loudness_score=100,
        silence_score=100,
        noise_score=100,
        clipping_score=100,
    )

    assert result.score == 100.0
    assert result.recommendation == "Accept"


def test_overall_quality_applies_short_recording_penalty() -> None:
    result = calculate_overall_quality(
        duration_seconds=0.5,
        loudness_score=100,
        silence_score=100,
        noise_score=100,
        clipping_score=100,
    )

    assert result.score == 95.0
    assert result.recommendation == "Accept"


def test_overall_quality_recommends_review_for_mixed_results() -> None:
    result = calculate_overall_quality(
        duration_seconds=1.0,
        loudness_score=80,
        silence_score=60,
        noise_score=70,
        clipping_score=90,
    )

    assert result.score == 77.5
    assert result.recommendation == "Review"


def test_overall_quality_recommends_rerecord_for_poor_results() -> None:
    result = calculate_overall_quality(
        duration_seconds=1.0,
        loudness_score=0,
        silence_score=0,
        noise_score=0,
        clipping_score=0,
    )

    assert result.score == 10.0
    assert result.recommendation == "Re-record"


def test_scoring_configuration_rejects_invalid_weights() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        ScoringConfig(duration_weight=0.2)


def test_scoring_configuration_rejects_unordered_thresholds() -> None:
    with pytest.raises(ValueError, match="thresholds"):
        ScoringConfig(accept_threshold=50, review_threshold=60)
