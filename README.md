# AI Teaching Transcript Evaluation Pipeline

An automated, production-grade LLM evaluation pipeline that parses tutoring session transcripts, enforces strict JSON schema validation via Pydantic, handles malformed outputs using error-guided retry loops, logs token usage and estimated API costs, and exports standardized evaluation metrics.

---

## Architecture Overview

```text
                                  +-----------------------+
                                  |   transcripts/*.txt   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |     src/runner.py     |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |   prompts/evaluator   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |    src/evaluator.py   |
                                  |  (OpenAI / Mock API)  |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |    src/validator.py   |
                                  +-----+-----------+-----+
                                        |           |
                              Valid JSON|           |Schema Violation
                                        v           v
                          +---------------+       +------------------+
                          | Pydantic      |       |  src/retry.py    |
                          | Evaluation    |       |  (Feedback retry)|
                          +-------+-------+       +--------+---------+
                                  |                        |
                                  +-----------+------------+
                                              |
                     +------------------------+------------------------+
                     |                        |                        |
                     v                        v                        v
            outputs/<name>.json     outputs/raw/<name>_raw.json     logs.csv
            (Validated Output)           (Raw LLM JSON)           (Cost & Latency)
```

---

## Key Features

1. **Structured Output Enforcement**: Powered by OpenAI JSON response formatting and Pydantic v2 schemas (`Engagement`, `Clarity`, `Pacing`, `NotableMoments`, `Confidence`).
2. **Resilient Validation & Error-Guided Retries**: 2-stage retry mechanism. When a schema violation occurs, the system re-prompts the LLM with the exact `ValidationError` trace. If max attempts are reached, it outputs a non-crashing `FailedEvaluation` fallback object.
3. **Observability & Cost Logging**: Tracks `input_tokens`, `output_tokens`, `total_tokens`, latency (ms), and computes USD costs against an up-to-date model pricing matrix, appending all metadata to `logs.csv`.
4. **CLI Flexibility**: Command-line arguments for model switching (`--model gpt-4o-mini`, `--model gpt-4o`), single-file evaluation (`--single`), custom transcript directories, and dry-run offline testing (`--mock`).
5. **Raw Output Auditability**: Preserves both validated Pydantic JSON outputs in `outputs/` and unmodified raw LLM strings in `outputs/raw/` for auditing and prompt engineering.

---

## Directory Structure

```text
ai-teaching-evaluator/
│
├── transcripts/              # Input tutoring session transcripts (.txt)
│   ├── transcript1.txt       # Python For-Loops & enumerate debugging
│   ├── transcript2.txt       # SQL INNER vs LEFT JOIN debugging
│   ├── transcript3.txt       # Binary Search boundary conditions
│   ├── transcript4.txt       # React useEffect infinite loop debugging
│   └── transcript5.txt       # Physics: Newton's 2nd Law intuition
│
├── outputs/                  # Validated JSON evaluation results
│   ├── raw/                  # Unmodified raw LLM responses for debugging
│   │   ├── transcript1_raw.json
│   │   └── ...
│   ├── transcript1.json
│   └── ...
│
├── prompts/
│   └── evaluator_prompt.md   # System prompt with schema rules & grounded evidence
│
├── src/
│   ├── __init__.py
│   ├── schema.py             # Pydantic models (Metric, Moment, Evaluation)
│   ├── evaluator.py          # OpenAI API client & mock generator
│   ├── validator.py          # Pydantic schema validation & syntax parsing
│   ├── cost.py               # Token counter, cost calculator & CSV logger
│   ├── runner.py             # CLI runner for batch execution
│   └── retry.py              # 2-attempt error feedback retry logic
│
├── tests/
│   ├── __init__.py
│   ├── test_schema.py        # Unit tests for Pydantic bounds & validation
│   └── test_validator.py     # Unit tests for JSON parsing & retry handling
│
├── logs.csv                  # Execution metadata log (tokens, cost, latency)
├── README.md                 # Setup & architecture documentation
├── report.md                 # 300-500 word AI production report
├── requirements.txt          # Python dependencies
└── .env.example              # Environment variables template
```

---

## Setup & Installation

### 1. Prerequisites
- **Python 3.11+** installed.
- (Optional) OpenAI API Key.

### 2. Virtual Environment Setup
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```
Edit `.env` and insert your OpenAI API key:
```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

---

## Usage

### Batch Run All Transcripts
To process all transcripts in `transcripts/`:
```bash
python -m src.runner
```

### Dry-Run / Mock Mode (Offline Testing)
To test the full pipeline offline without incurring API charges:
```bash
python -m src.runner --mock
```

### Switch Models via CLI
```bash
python -m src.runner --model gpt-4o
```

### Process a Single Transcript
```bash
python -m src.runner --single transcripts/transcript1.txt
```

---

## Running Unit Tests

Run the complete test suite with `pytest`:
```bash
pytest tests/ -v
```

Expected output:
```text
tests/test_schema.py ......                                              [ 60%]
tests/test_validator.py ....                                             [100%]
10 passed in 1.51s
```

---

## Sample JSON Output

`outputs/transcript1.json`:
```json
{
  "status": "ok",
  "engagement": {
    "score": 8,
    "evidence": [
      "Yeah... it just prints the last item 'evan' five times next to each item!",
      "Wait, what if I wanted the numbering to start at 1 instead of 0 for a user-facing list?"
    ],
    "reasoning": "The student actively shared their broken code attempt and asked proactive follow-up questions."
  },
  "clarity": {
    "score": 9,
    "evidence": [
      "enumerate() is a built-in helper that takes a sequence and yields pairs of (index, item) automatically as you iterate."
    ],
    "reasoning": "The tutor clearly explained the difference between range(len()) and enumerate with concise syntax examples."
  },
  "pacing": {
    "score": 9,
    "evidence": [
      "Moved efficiently from diagnosing the -1 index bug to range(len()) and introducing enumerate."
    ],
    "reasoning": "Excellent progression speed, allowing the student to experiment with custom start parameters."
  },
  "notable_moments": [
    {
      "timestamp": "Turn 4",
      "category": "misconception",
      "quote": "I thought -1 meant 'the current item minus one step' or something?",
      "event": "Student vocalized misunderstanding of negative list indexing in Python loops."
    },
    {
      "timestamp": "Turn 8",
      "category": "breakthrough",
      "quote": "Oh, wow. You don't have to write items[index] at all?",
      "event": "Student understood tuple unpacking provided by Python enumerate function."
    }
  ],
  "recommendations": [
    "Encourage student to write a short code snippet independently before revealing syntax.",
    "Reinforce positive learning behaviors like asking about optional parameters."
  ],
  "overall_feedback": "Highly effective session. The tutor helped the student overcome indexing confusion and adopt Pythonic conventions.",
  "confidence": 0.95
}
```

---

## Cost Logging Sample (`logs.csv`)

| transcript | model | timestamp | status | attempts | input_tokens | output_tokens | total_tokens | cost_usd | latency_ms |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| transcript1 | gpt-4o-mini | 2026-07-25 10:30:15 | ok | 1 | 1239 | 400 | 1639 | $0.000455 | 150.8 |
| transcript2 | gpt-4o-mini | 2026-07-25 10:30:15 | ok | 1 | 1180 | 395 | 1575 | $0.000434 | 150.7 |
| transcript3 | gpt-4o-mini | 2026-07-25 10:30:15 | ok | 1 | 1320 | 441 | 1761 | $0.000473 | 150.8 |
| transcript4 | gpt-4o-mini | 2026-07-25 10:30:16 | ok | 1 | 1210 | 403 | 1613 | $0.000415 | 150.8 |
| transcript5 | gpt-4o-mini | 2026-07-25 10:30:16 | ok | 1 | 1150 | 383 | 1533 | $0.000391 | 150.6 |
