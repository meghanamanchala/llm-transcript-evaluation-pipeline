"""CLI Runner for batch processing tutoring session transcript evaluations."""

import os
import glob
import json
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

from src.retry import evaluate_with_retry
from src.cost import calculate_cost, log_cost_to_csv

load_dotenv()

RICH_AVAILABLE = False
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def print_log(message: str, style: str = "info") -> None:
    """Print styled console messages."""
    if RICH_AVAILABLE:
        color = "green" if style == "success" else "red" if style == "error" else "cyan"
        console.print(f"[{color}]{message}[/{color}]")
    else:
        print(message)


def process_single_transcript(
    file_path: str,
    output_dir: str,
    model: str,
    mock: bool = False
) -> Dict[str, Any]:
    """Process a single transcript file through evaluation, validation, saving, and logging."""
    base_name = os.path.basename(file_path)
    transcript_id = os.path.splitext(base_name)[0]

    with open(file_path, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    print_log(f"Processing transcript: {base_name} (Model: {model})...", "info")

    result_model, raw_response, usage, latency_ms, attempts = evaluate_with_retry(
        transcript_text=transcript_text,
        model=model,
        mock=mock
    )

    # 1. Save validated JSON output
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, f"{transcript_id}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(result_model.model_dump_json(indent=2))

    # 2. Save raw LLM response for debugging
    raw_dir = os.path.join(output_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    raw_file = os.path.join(raw_dir, f"{transcript_id}_raw.json")
    with open(raw_file, "w", encoding="utf-8") as f:
        f.write(raw_response)

    # 3. Calculate cost & log metrics
    cost_usd = calculate_cost(model, usage.get("input_tokens", 0), usage.get("output_tokens", 0))
    status_str = getattr(result_model, "status", "ok")

    log_cost_to_csv(
        transcript_name=transcript_id,
        model=model,
        status=status_str,
        attempts=attempts,
        usage=usage,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
        csv_path="logs.csv"
    )

    status_indicator = "[OK]" if status_str == "ok" else "[FAILED]"
    print_log(
        f"SUCCESS: Saved {base_name} -> {out_file} {status_indicator} "
        f"| Tokens: {usage.get('total_tokens', 0)} | Cost: ${cost_usd:.6f} | Latency: {latency_ms:.1f}ms | Attempts: #{attempts}",
        "success" if status_str == "ok" else "error"
    )

    return {
        "transcript": transcript_id,
        "status": status_str,
        "attempts": attempts,
        "tokens": usage.get("total_tokens", 0),
        "cost": cost_usd,
        "latency_ms": latency_ms
    }


def run_batch(
    transcripts_dir: str = "transcripts",
    output_dir: str = "outputs",
    model: str = "gpt-4o-mini",
    mock: bool = False,
    single_file: str = None
) -> None:
    """Run batch evaluation across all transcript files."""
    if single_file:
        files = [single_file]
    else:
        files = sorted(glob.glob(os.path.join(transcripts_dir, "*.txt")))

    if not files:
        print_log(f"No transcript files found in '{transcripts_dir}'.", "error")
        return

    print_log(f"Starting evaluation runner across {len(files)} transcript(s)...", "info")

    summary_stats = []
    for file_path in files:
        stats = process_single_transcript(
            file_path=file_path,
            output_dir=output_dir,
            model=model,
            mock=mock
        )
        summary_stats.append(stats)

    print_log("\nBatch evaluation run completed successfully!", "success")

    if RICH_AVAILABLE:
        table = Table(title="Transcript Evaluation Execution Summary")
        table.add_column("Transcript", style="cyan")
        table.add_column("Status", style="bold green")
        table.add_column("Attempts", justify="right")
        table.add_column("Tokens", justify="right")
        table.add_column("Cost (USD)", justify="right")
        table.add_column("Latency (ms)", justify="right")

        total_cost = 0.0
        total_tokens = 0
        for s in summary_stats:
            total_cost += s["cost"]
            total_tokens += s["tokens"]
            status_style = "green" if s["status"] == "ok" else "red"
            table.add_row(
                s["transcript"],
                f"[{status_style}]{s['status']}[/{status_style}]",
                str(s["attempts"]),
                f"{s['tokens']:,}",
                f"${s['cost']:.6f}",
                f"{s['latency_ms']:.1f}"
            )
        console.print(table)
        console.print(f"[bold gold1]Total Cost: ${total_cost:.6f} | Total Tokens: {total_tokens:,}[/bold gold1]\n")


def main() -> None:
    """Main CLI entrypoint."""
    default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    parser = argparse.ArgumentParser(
        description="LLM Transcript Evaluation Pipeline Runner"
    )
    parser.add_argument(
        "--transcripts-dir",
        type=str,
        default="transcripts",
        help="Directory containing transcript txt files."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Directory for saving validated JSON outputs."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=default_model,
        help=f"OpenAI model name (default: {default_model})."
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run offline mock evaluation without making network API calls."
    )
    parser.add_argument(
        "--single",
        type=str,
        default=None,
        help="Path to a single transcript file to evaluate."
    )

    args = parser.parse_args()

    run_batch(
        transcripts_dir=args.transcripts_dir,
        output_dir=args.output_dir,
        model=args.model,
        mock=args.mock,
        single_file=args.single
    )


if __name__ == "__main__":
    main()
