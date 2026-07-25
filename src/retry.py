"""Retry strategy module for handling malformed outputs and schema violations."""

import json
from typing import Tuple, Dict, Any, Union
from src.evaluator import evaluate_transcript
from src.validator import validate_evaluation_json
from src.schema import Evaluation, FailedEvaluation


def evaluate_with_retry(
    transcript_text: str,
    model: str = "gpt-4o-mini",
    prompt_path: str = "prompts/evaluator_prompt.md",
    max_attempts: int = 2,
    mock: bool = False
) -> Tuple[Union[Evaluation, FailedEvaluation], str, Dict[str, int], float, int]:
    """
    Evaluate transcript with automatic retry on schema validation failure.

    Returns:
        Tuple of (result_model, raw_response_str, combined_usage, total_latency_ms, attempts_used)
    """
    combined_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    total_latency = 0.0
    last_raw_response = ""
    last_error = ""

    for attempt in range(1, max_attempts + 1):
        extra_feedback = None
        if attempt > 1:
            extra_feedback = (
                f"Your previous response failed schema validation with error: {last_error}. "
                "Please fix the error and return ONLY valid JSON matching the schema."
            )

        raw_response, usage, latency = evaluate_transcript(
            transcript_text=transcript_text,
            model=model,
            prompt_path=prompt_path,
            mock=mock,
            extra_feedback_prompt=extra_feedback
        )

        last_raw_response = raw_response
        total_latency += latency
        for key in combined_usage:
            combined_usage[key] += usage.get(key, 0)

        is_valid, model_obj, error_msg = validate_evaluation_json(raw_response)

        if is_valid and isinstance(model_obj, Evaluation):
            return model_obj, raw_response, combined_usage, total_latency, attempt

        last_error = error_msg or "Unknown validation error"

    # Fallback if all retries fail: Return structured FailedEvaluation object without crashing
    failed_obj = FailedEvaluation(
        status="failed",
        error=f"Exhausted {max_attempts} attempts. Last error: {last_error}",
        attempts=max_attempts,
        raw_response=last_raw_response
    )
    return failed_obj, last_raw_response, combined_usage, total_latency, max_attempts
