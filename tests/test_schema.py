"""Unit tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError
from src.schema import Metric, Moment, Evaluation, FailedEvaluation


def test_metric_valid_score():
    """Test metric with valid score within 1-10 range."""
    metric = Metric(score=8, evidence=["Quote 1"], reasoning="Good engagement.")
    assert metric.score == 8
    assert metric.evidence == ["Quote 1"]


def test_metric_invalid_high_score():
    """Test metric score > 10 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        Metric(score=11, evidence=["Quote 1"])
    assert "score" in str(exc_info.value)


def test_metric_invalid_low_score():
    """Test metric score < 1 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        Metric(score=0, evidence=["Quote 1"])
    assert "score" in str(exc_info.value)


def test_evaluation_valid_structure():
    """Test complete valid Evaluation object."""
    eval_obj = Evaluation(
        engagement=Metric(score=9, evidence=["Good question"]),
        clarity=Metric(score=8, evidence=["Clear explanation"]),
        pacing=Metric(score=7, evidence=["Steady rate"]),
        notable_moments=[
            Moment(timestamp="Turn 1", category="breakthrough", quote="Aha!", event="Understood concept")
        ],
        recommendations=["Practice more"],
        overall_feedback="Great session overall.",
        confidence=0.92
    )
    assert eval_obj.status == "ok"
    assert eval_obj.engagement.score == 9
    assert eval_obj.confidence == 0.92


def test_evaluation_invalid_confidence():
    """Test evaluation confidence > 1.0 raises ValidationError."""
    with pytest.raises(ValidationError):
        Evaluation(
            engagement=Metric(score=9, evidence=["E1"]),
            clarity=Metric(score=8, evidence=["E2"]),
            pacing=Metric(score=7, evidence=["E3"]),
            overall_feedback="Summary",
            confidence=1.5
        )


def test_failed_evaluation_schema():
    """Test FailedEvaluation fallback model."""
    failed = FailedEvaluation(status="failed", error="Schema violation", attempts=2)
    assert failed.status == "failed"
    assert failed.attempts == 2
