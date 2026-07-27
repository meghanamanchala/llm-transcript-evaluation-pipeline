# Production Engineering & Evaluation Report: AI Transcript Evaluator
**Bodhrik Placement Assessment — AI Engineer Track (Round 1 Task)**

---

## 1. Prompt & Schema Design & Failure Modes (`src/schema.py`, `src/evaluator.py`)

Evaluating teaching sessions requires transforming unstructured conversation transcripts into objective, reliable quantitative metrics. Free-form LLM outputs frequently suffer from metric hallucination, schema drift, and subjective score inflation. To guarantee absolute output reliability, this pipeline enforces a strict Pydantic v2 JSON Schema paired with structured outputs (`src/schema.py`), supporting both Google Gemini API (`GEMINI_API_KEY`) via OpenAI-compatible REST endpoints and OpenAI models (`OPENAI_API_KEY`).

### Key Architectural Schema Safeguards
- **Grounded Verbatim Evidence**: Every metric (`engagement`, `clarity`, `pacing`) mandates an array of exact transcript quotes (`evidence`). Forcing the LLM to supply empirical textual proof anchors scores in actual transcript dialogue, eliminating arbitrary score hallucination.
- **Strict Range Constraints**: Metric scores are bound to integers ($1 \le \text{score} \le 10$), preventing out-of-range float values (e.g., 8.5) or unbounded numbers.
- **Explicit Confidence Metric**: The model returns a normalized float ($0.0 \le \text{confidence} \le 1.0$) to flag transcript truncation, background noise, or ambiguity.
- **Structured Notable Moments**: Captures key session timestamps (e.g., Turn 4), categories (`misconception`, `breakthrough`), and quotes.

### Tested Failure Modes & Mitigation Strategies (`src/validator.py`, `src/retry.py`)

| Failure Scenario | Pipeline Behavior & Mitigation Strategy |
| :--- | :--- |
| **1. Invalid JSON Syntax** | Caught by `json.loads()` in `src/validator.py`. Triggers feedback retry loop with exact error position. |
| **2. Missing Schema Keys** | Pydantic flags missing required keys. System re-prompts LLM with specific missing field location trace. |
| **3. Type / Range Violations** | String scores or values $>10$ trigger Pydantic `ValidationError` feedback re-prompting to LLM. |
| **4. Empty Transcripts** | Detected prior to LLM call; returns zero-token `FailedEvaluation` without wasting API budget. |
| **5. Max Retry Exhaustion** | If 2 retries fail, returns a graceful `FailedEvaluation` (`status="failed"`) to preserve batch execution. |

---

## 2. Integrated Benchmarking Engine & Audit Queue (`src/benchmark.py`, `transcripts/ground_truth.json`)

To measure LLM evaluation quality against human standards, we implemented a dedicated benchmarking engine (`src/benchmark.py`) that evaluates live model outputs against a gold-standard ground truth dataset (`transcripts/ground_truth.json`).

### Codebase Benchmarking Implementation
1. **Ground Truth Dataset**: Annotated benchmark dataset (`transcripts/ground_truth.json`) containing human educator scores and verbatim evidence quotes.
2. **Mean Absolute Error (MAE Calculation)**: Computes mathematical deviation between LLM scores ($S_{\text{LLM}}$) and human consensus ($S_{\text{human}}$):
   $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |S_{\text{LLM}, i} - S_{\text{human}, i}|$$
3. **Quadratic Weighted Kappa (QWK)**: Calculates Cohen's Quadratic Weighted Kappa to assess ordinal inter-rater agreement, heavily penalizing large score mismatches.
4. **Evidence Precision & Recall**: Computes string-matching overlap between LLM-extracted quotes and human-annotated evidence spans.
5. **Automated Audit Queue (`outputs/audit_queue.json`)**: Any session metric where $|S_{\text{LLM}} - S_{\text{human}}| \ge 2$ is automatically flagged into `outputs/audit_queue.json` along with the LLM reasoning and human notes for continuous prompt refinement.

---

## 3. Cost/Latency Tradeoffs & High-Volume Video Processing (`src/cost.py`, `logs.csv`)

Single transcript runs execute in $<200\text{ms}$ in mock mode and $\sim 2–3\text{s}$ via Gemini API (`gemini-3.1-flash-lite`).

### Production Cost & Latency Optimizations
- **Multi-Provider & Model Cascade Architecture**: Route 100% of incoming transcripts to high-efficiency models like Google Gemini Flash (`gemini-2.5-flash` at $0.075/1M input tokens) or `gpt-4o-mini` ($0.15/1M). Cascade to higher-tier models (`gemini-2.5-pro` or `gpt-4o`) only if confidence falls below 0.85 or validation fails twice. Reduces API spend by ~85–90%.
- **Automatic Prompt Caching**: Keep system prompts static to leverage provider prompt caching, yielding up to a 50% discount on input token costs.
- **Async Parallel Worker Pools**: Process batch runs asynchronously via `asyncio`, Celery, or AWS SQS/Lambda worker pools rather than sequential loops.

### Processing Video at Real Volume (Architectural Modifications)
Sending raw HD video streams directly to multimodal LLMs is cost-prohibitive ($10–$30+ per hour of video) and high latency. For real volume production:
1. **Audio Pipeline Extraction & Fast STT**: Strip video tracks; process audio through high-throughput Speech-to-Text (Deepgram / Gemini Audio / Whisper API) with speaker diarization (Tutor vs. Student). Cost: ~\$0.004/min.
2. **Event-Driven Visual Keyframe Sampling**: Sample visual frames only during slide transitions, code editor changes, or screen-sharing events (using OpenCV scene-change detection). Avoid processing redundant 30 FPS video frames.
3. **Multimodal Hybrid Pass**: Run full transcript text through the fast text evaluator; send sampled keyframe images to visual LLMs (e.g. Gemini 2.5 Flash multimodal) solely when evaluating visual clarity (e.g. whiteboard notes, code syntax errors).
