"""Unit tests for JSON validator and retry logic."""

import json
import pytest
from src.validator import validate_evaluation_json
from src.retry import evaluate_with_retry
from src.schema import Evaluation, FailedEvaluation


def test_validate_evaluation_json_success():
    """Test validator returns True for valid raw JSON string."""
    valid_json = json.dumps({
        "status": "ok",
        "engagement": {"score": 8, "evidence": ["Ex 1"]},
        "clarity": {"score": 9, "evidence": ["Ex 2"]},
        "pacing": {"score": 7, "evidence": ["Ex 3"]},
        "notable_moments": [],
        "recommendations": ["Do X"],
        "overall_feedback": "Good job.",
        "confidence": 0.9
    })

    is_valid, model, error = validate_evaluation_json(valid_json)
    assert is_valid is True
    assert isinstance(model, Evaluation)
    assert error is None
    assert model.engagement.score == 8


def test_validate_evaluation_json_syntax_error():
    """Test validator catches invalid JSON syntax."""
    bad_syntax = "{ 'engagement': { 'score': 8 } "  # Unclosed brace and invalid single quotes

    is_valid, model, error = validate_evaluation_json(bad_syntax)
    assert is_valid is False
    assert model is None
    assert "Invalid JSON syntax" in error


def test_validate_evaluation_json_schema_error():
    """Test validator catches schema type violation (e.g., string score)."""
    invalid_type = json.dumps({
        "engagement": {"score": "super_good", "evidence": ["Ex 1"]},
        "clarity": {"score": 9, "evidence": ["Ex 2"]},
        "pacing": {"score": 7, "evidence": ["Ex 3"]},
        "overall_feedback": "Good job.",
        "confidence": 0.9
    })

    is_valid, model, error = validate_evaluation_json(invalid_type)
    assert is_valid is False
    assert model is None
    assert "Schema validation error" in error


def test_retry_mechanism_mock():
    """Test evaluate_with_retry end-to-end execution in mock mode."""
    transcript_sample = "Tutor: What is a loop? Student: A repetition statement!"
    res_model, raw_str, usage, latency, attempts = evaluate_with_retry(
        transcript_text=transcript_sample,
        mock=True
    )

    assert isinstance(res_model, (Evaluation, FailedEvaluation))
    assert attempts >= 1
    assert usage["total_tokens"] > 0
    assert latency > 0
