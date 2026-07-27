"""Benchmarking module to evaluate LLM accuracy against human ground truth annotations."""

import json
import os
from typing import Dict, List, Any, Tuple


def calculate_mae(llm_scores: List[float], human_scores: List[float]) -> float:
    """Calculate Mean Absolute Error between LLM scores and human ground truth."""
    if not llm_scores or len(llm_scores) != len(human_scores):
        return 0.0
    total_diff = sum(abs(l - h) for l, h in zip(llm_scores, human_scores))
    return round(total_diff / len(llm_scores), 4)


def calculate_qwk(llm_scores: List[int], human_scores: List[int], min_score: int = 1, max_score: int = 10) -> float:
    """
    Calculate Quadratic Weighted Kappa (QWK) between ordinal scores.
    Measures agreement between AI and human raters, heavily penalizing large mismatches.
    """
    if not llm_scores or len(llm_scores) != len(human_scores):
        return 1.0
        
    N = len(llm_scores)
    num_categories = max_score - min_score + 1
    
    # Create observed weight matrix (quadratic penalty)
    weights = [[((i - j) ** 2) / ((num_categories - 1) ** 2) for j in range(num_categories)] for i in range(num_categories)]
    
    # Build histogram matrices
    O = [[0] * num_categories for _ in range(num_categories)]
    for l, h in zip(llm_scores, human_scores):
        l_idx = max(0, min(num_categories - 1, l - min_score))
        h_idx = max(0, min(num_categories - 1, h - min_score))
        O[l_idx][h_idx] += 1
        
    # Marginal distributions
    hist_l = [sum(O[i][j] for j in range(num_categories)) for i in range(num_categories)]
    hist_h = [sum(O[i][j] for i in range(num_categories)) for j in range(num_categories)]
    
    # Expected matrix under independence
    E = [[(hist_l[i] * hist_h[j]) / N for j in range(num_categories)] for i in range(num_categories)]
    
    num = sum(weights[i][j] * O[i][j] for i in range(num_categories) for j in range(num_categories))
    den = sum(weights[i][j] * E[i][j] for i in range(num_categories) for j in range(num_categories))
    
    if den == 0:
        return 1.0
        
    qwk = 1.0 - (num / den)
    return round(qwk, 4)


def calculate_evidence_precision_recall(llm_quotes: List[str], human_quotes: List[str]) -> Tuple[float, float]:
    """Calculate Precision and Recall of extracted verbatim evidence quotes."""
    if not llm_quotes or not human_quotes:
        return 0.0, 0.0

    # Substring matching for evidence quote overlap
    matches = 0
    for lq in llm_quotes:
        lq_clean = lq.strip().lower()
        if any(hq.strip().lower() in lq_clean or lq_clean in hq.strip().lower() for hq in human_quotes):
            matches += 1

    precision = matches / len(llm_quotes) if llm_quotes else 0.0
    recall = matches / len(human_quotes) if human_quotes else 0.0
    return round(precision, 4), round(recall, 4)


def benchmark_evaluations(
    outputs_dir: str = "outputs",
    ground_truth_path: str = "transcripts/ground_truth.json"
) -> Dict[str, Any]:
    """
    Run complete benchmarking suite comparing output JSONs against human ground truth dataset.
    Generates audit queue for session score differences >= 2.
    """
    if not os.path.exists(ground_truth_path):
        return {"status": "error", "message": f"Ground truth file not found at {ground_truth_path}"}

    with open(ground_truth_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    llm_all_scores = []
    human_all_scores = []
    all_llm_quotes = []
    all_human_quotes = []
    audit_queue = []

    for item in ground_truth:
        transcript_id = item["transcript"]
        output_file = os.path.join(outputs_dir, f"{transcript_id}.json")

        if not os.path.exists(output_file):
            continue

        with open(output_file, "r", encoding="utf-8") as f:
            eval_data = json.load(f)

        if eval_data.get("status") != "ok":
            audit_queue.append({
                "transcript": transcript_id,
                "reason": "Evaluation failed or errored",
                "data": eval_data
            })
            continue

        # Extract metric scores
        metrics = ["engagement", "clarity", "pacing"]
        for m in metrics:
            llm_score = eval_data.get(m, {}).get("score", 0)
            human_score = item.get(m, {}).get("score", 0)
            llm_all_scores.append(llm_score)
            human_all_scores.append(human_score)

            # Continuous Improvement: Flag differences >= 2 points for audit
            if abs(llm_score - human_score) >= 2:
                audit_queue.append({
                    "transcript": transcript_id,
                    "metric": m,
                    "llm_score": llm_score,
                    "human_score": human_score,
                    "diff": abs(llm_score - human_score),
                    "llm_reasoning": eval_data.get(m, {}).get("reasoning", ""),
                    "human_notes": item.get(m, {}).get("notes", "")
                })

            llm_quotes = eval_data.get(m, {}).get("evidence", [])
            human_quotes = item.get(m, {}).get("evidence", [])
            all_llm_quotes.extend(llm_quotes)
            all_human_quotes.extend(human_quotes)

    mae = calculate_mae(llm_all_scores, human_all_scores)
    qwk = calculate_qwk(llm_all_scores, human_all_scores)
    precision, recall = calculate_evidence_precision_recall(all_llm_quotes, all_human_quotes)

    # Save audit queue
    audit_path = os.path.join(outputs_dir, "audit_queue.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_queue, f, indent=2)

    return {
        "status": "success",
        "transcripts_benchmarked": len(ground_truth),
        "mae": mae,
        "mae_target_met": mae < 0.75,
        "qwk": qwk,
        "evidence_precision": precision,
        "evidence_recall": recall,
        "audit_flagged_count": len(audit_queue),
        "audit_queue_file": audit_path
    }
