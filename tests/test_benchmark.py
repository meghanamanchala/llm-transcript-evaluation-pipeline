"""Unit tests for benchmarking module."""

from src.benchmark import calculate_mae, calculate_qwk, calculate_evidence_precision_recall, benchmark_evaluations


def test_calculate_mae():
    llm_scores = [8, 9, 8, 9, 8]
    human_scores = [8, 9, 8, 9, 8]
    assert calculate_mae(llm_scores, human_scores) == 0.0

    llm_scores_diff = [8, 8, 7, 9, 8]
    human_scores_diff = [8, 9, 8, 9, 8]
    # diffs: 0, 1, 1, 0, 0 => sum=2 / 5 = 0.4
    assert calculate_mae(llm_scores_diff, human_scores_diff) == 0.4


def test_calculate_qwk():
    llm_scores = [8, 9, 8, 9, 8]
    human_scores = [8, 9, 8, 9, 8]
    assert calculate_qwk(llm_scores, human_scores) == 1.0


def test_calculate_evidence_precision_recall():
    llm_quotes = ["enumerate() is a built-in helper", "prints the last item"]
    human_quotes = ["enumerate() is a built-in helper that takes a sequence", "prints the last item 'evan' five times"]
    precision, recall = calculate_evidence_precision_recall(llm_quotes, human_quotes)
    assert precision == 1.0
    assert recall == 1.0


def test_benchmark_evaluations_run():
    res = benchmark_evaluations()
    assert res["status"] == "success"
    assert "mae" in res
    assert "qwk" in res
    assert "evidence_precision" in res
    assert "evidence_recall" in res
