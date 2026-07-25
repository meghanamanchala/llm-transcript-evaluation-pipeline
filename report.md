# Production Engineering & Evaluation Report

## 1. Prompt & Schema Design

Evaluating pedagogical quality requires transforming unstructured conversation transcripts into reliable, actionable quantitative data. Free-form LLM outputs often suffer from schema drift, hallucinated metrics, and subjective score inflation. To mitigate these risks, this pipeline enforces strict JSON Schema output paired with runtime Pydantic v2 validation (`src/schema.py`).

### Key Schema Mechanisms
- **Grounded Evidence Arrays**: Every metric (`engagement`, `clarity`, `pacing`) mandates a list of verbatim transcript quotes (`evidence`). Forcing the model to locate textual proof anchors numeric scores in empirical transcript artifacts, drastically suppressing hallucinations.
- **Strict Score Constraints**: Integer bounds ($1 \le \text{score} \le 10$) prevent invalid floating-point scores (e.g., 8.5) or unbounded ranges.
- **Model Confidence Score**: A normalized float ($0.0 \le \text{confidence} \le 1.0$) captures evaluation uncertainty when transcripts are truncated or ambiguous.

### Tested Failure Modes
The pipeline explicitly handles five failure scenarios: (1) Invalid JSON syntax, (2) Missing top-level keys, (3) Incorrect data types (e.g., string scores), (4) Out-of-bounds metrics, and (5) Empty transcript files. When validation fails, `src/retry.py` re-prompts the model with the exact Pydantic `ValidationError` trace. If max retries are exhausted, the pipeline generates a graceful `FailedEvaluation` fallback object (`status="failed"`), preserving system reliability without crashing batch workflows.

---

## 2. Benchmarking Strategy

To ensure LLM evaluations align with professional pedagogical standards, the evaluation system requires rigorous benchmarking against human educator consensus.

### Ground Truth Dataset Construction
1. **Annotated Benchmark Set**: Create a dataset of 100+ multi-subject tutoring session transcripts annotated by expert human educators.
2. **Multi-Rater Rubric**: Three independent educators score each transcript on engagement, clarity, and pacing while flagging key moments.

### Evaluation Metrics
- **Mean Absolute Error (MAE)**: Measures absolute numerical deviation between model scores ($S_{\text{LLM}}$) and human consensus ($S_{\text{human}}$).
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |S_{\text{LLM}, i} - S_{\text{human}, i}|$$
- **Cohen’s Weighted Kappa ($\kappa$)**: Evaluates ordinal inter-rater agreement while accounting for chance agreement.
- **Evidence Precision & Recall**: Measures whether quotes extracted by the LLM match human-annotated evidence spans.

Disagreements where $|S_{\text{LLM}} - S_{\text{human}}| \ge 2$ are routed to an audit queue to iteratively refine prompt guidelines and score calibration.

---

## 3. Cost & Latency Optimizations

While single-transcript evaluation runs sequentially in $<200\text{ms}$ in mock mode or $\sim 2-4\text{s}$ over HTTP, production scaling across millions of tutoring sessions requires infrastructure-level optimization.

```text
Incoming Transcript Queue ──> Async Workers ──> Tier 1: gpt-4o-mini (Fast / $0.15/1M)
                                                        │
                                                        ├── High Confidence (>=0.85) ──> Save & Cache Output
                                                        └── Low Confidence / Schema Retry ──> Tier 2: gpt-4o ($2.50/1M)
```

### Production Architecture Blueprint
1. **Asynchronous Parallel Worker Pools**: Transition from sequential iteration to asynchronous worker pools (`asyncio`, Celery, or AWS SQS / Lambda) capable of processing thousands of transcripts concurrently.
2. **Model Cascade Routing**: Route all incoming transcripts to a smaller, high-throughput model (`gpt-4o-mini`). Only fallback to a larger model (`gpt-4o`) if confidence falls below $0.85$ or schema validation fails twice.
3. **Prompt Prefix Caching**: Structure system prompts to leverage OpenAI’s automatic prompt caching, reducing input token billing by up to $50\%$ on static evaluator prompt prefixes.
4. **Embedding Caching & Deduplication**: Compute transcript embeddings to cache evaluation results for repeated or template-based sessions.
