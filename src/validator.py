"""JSON and Pydantic schema validator module."""

import json
from typing import Tuple, Optional, Union
from pydantic import ValidationError
from src.schema import Evaluation, FailedEvaluation


def validate_evaluation_json(raw_json_str: str) -> Tuple[bool, Optional[Union[Evaluation, FailedEvaluation]], Optional[str]]:
    """
    Validate raw JSON string against the Evaluation Pydantic model.

    Returns:
        Tuple of (is_valid: bool, parsed_model_or_none, error_message_or_none)
    """
    if not raw_json_str or not raw_json_str.strip():
        return False, None, "Raw response is empty or null."

    try:
        data = json.loads(raw_json_str)
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON syntax: {str(e)}"

    # If the response explicitly represents a failed evaluation status
    if isinstance(data, dict) and data.get("status") == "failed":
        try:
            failed_model = FailedEvaluation.model_validate(data)
            return False, failed_model, failed_model.error
        except ValidationError:
            pass

    try:
        evaluation = Evaluation.model_validate(data)
        return True, evaluation, None
    except ValidationError as ve:
        error_details = []
        for err in ve.errors():
            loc = " -> ".join(str(item) for item in err["loc"])
            msg = err["msg"]
            error_details.append(f"Field '{loc}': {msg}")
        full_error_msg = "; ".join(error_details)
        return False, None, f"Schema validation error: {full_error_msg}"
