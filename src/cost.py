"""Token usage calculation and CSV cost logger."""

import os
import csv
from datetime import datetime
from typing import Dict, Any

# Pricing matrix per 1,000,000 tokens (USD)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost in USD based on model pricing per 1M tokens."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o-mini"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


def log_cost_to_csv(
    transcript_name: str,
    model: str,
    status: str,
    attempts: int,
    usage: Dict[str, int],
    cost_usd: float,
    latency_ms: float,
    csv_path: str = "logs.csv"
) -> None:
    """Log token usage, cost estimates, and latency metadata to a CSV file."""
    file_exists = os.path.exists(csv_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header = [
        "transcript",
        "model",
        "timestamp",
        "status",
        "attempts",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cost_usd",
        "latency_ms"
    ]

    row = [
        transcript_name,
        model,
        timestamp,
        status,
        attempts,
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0),
        usage.get("total_tokens", 0),
        f"${cost_usd:.6f}",
        f"{latency_ms:.2f}"
    ]

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(row)
