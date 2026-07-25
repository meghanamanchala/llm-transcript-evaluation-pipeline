"""LLM Evaluator module for calling OpenAI API or mock generator."""

import os
import json
import time
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def load_system_prompt(prompt_path: str = "prompts/evaluator_prompt.md") -> str:
    """Load system prompt from file path."""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "You are an expert AI teaching evaluator. Return valid JSON evaluation."


def generate_mock_evaluation(transcript_text: str) -> str:
    """Generate a realistic mock JSON evaluation matching transcript content for dry-run mode."""
    if "Python" in transcript_text or "enumerate" in transcript_text:
        data = {
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
    elif "SQL" in transcript_text or "JOIN" in transcript_text:
        data = {
            "status": "ok",
            "engagement": {
                "score": 9,
                "evidence": [
                    "I have 20 customers in my customers table, but the query result only returns 11 rows!",
                    "What if I want those NULL amounts to display as $0.00 in the output?"
                ],
                "reasoning": "Student brought a real database bug and immediately tested suggestions in real time."
            },
            "clarity": {
                "score": 9,
                "evidence": [
                    "What join type 'preserves' all records from the left-hand table regardless of whether there's a match on the right?"
                ],
                "reasoning": "Tutor used Socratic questioning to help student deduce the difference between INNER and LEFT JOIN."
            },
            "pacing": {
                "score": 8,
                "evidence": [
                    "Steady pacing that allowed student to run SQL queries step by step."
                ],
                "reasoning": "Pacing was well balanced between conceptual explanation and query refinement."
            },
            "notable_moments": [
                {
                    "timestamp": "Turn 3",
                    "category": "misconception",
                    "quote": "half of my customers completely disappeared from the result set!",
                    "event": "Student discovered that INNER JOIN excludes unmatched customer rows."
                },
                {
                    "timestamp": "Turn 11",
                    "category": "breakthrough",
                    "quote": "Now all 20 rows are showing up! But for customers who haven't bought anything... NULL",
                    "event": "Student verified correct LEFT JOIN output and NULL handling."
                }
            ],
            "recommendations": [
                "Spend a minute explaining RIGHT JOIN vs FULL OUTER JOIN for completeness.",
                "Encourage student to draw Venn diagrams for complex multi-table joins."
            ],
            "overall_feedback": "Great tutoring session. The student mastered SQL join semantics and NULL handling with COALESCE.",
            "confidence": 0.94
        }
    elif "Binary Search" in transcript_text:
        data = {
            "status": "ok",
            "engagement": {
                "score": 8,
                "evidence": [
                    "Wait... left stays 4 forever! It's stuck in an infinite loop!",
                    "So left should be mid + 1!"
                ],
                "reasoning": "Student stepped through execution line by line to identify infinite loop behavior."
            },
            "clarity": {
                "score": 9,
                "evidence": [
                    "Once you inspect arr[mid] and know arr[mid] < target, the target MUST lie strictly to the right of mid."
                ],
                "reasoning": "Tutor provided clear explanation of search space reduction and inclusive loop bounds."
            },
            "pacing": {
                "score": 8,
                "evidence": [
                    "Appropriate speed, methodical dry-running of algorithm steps."
                ],
                "reasoning": "Allowed sufficient time to trace array index boundaries."
            },
            "notable_moments": [
                {
                    "timestamp": "Turn 6",
                    "category": "breakthrough",
                    "quote": "Since we already checked arr[mid]... why are we keeping mid in our search range?",
                    "event": "Student independently deduced why mid + 1 is required to prevent infinite loops."
                }
            ],
            "recommendations": [
                "Prompt student to consider potential integer overflow with (left + right) // 2 in other languages.",
                "Add practice with duplicate elements in sorted arrays."
            ],
            "overall_feedback": "Excellent algorithm debugging session. The student gained intuitive mastery over binary search bounds.",
            "confidence": 0.96
        }
    elif "React" in transcript_text or "useEffect" in transcript_text:
        data = {
            "status": "ok",
            "engagement": {
                "score": 9,
                "evidence": [
                    "browser tab freezes, fan starts spinning like a jet engine, and console floods with thousands of API requests",
                    "Wait... options state object changes... which triggers useEffect because options is in the dependency array!"
                ],
                "reasoning": "Student vividly described the bug symptom and actively traced React render state cycles."
            },
            "clarity": {
                "score": 9,
                "evidence": [
                    "creating a new object literal... creates a new object reference in memory every single time"
                ],
                "reasoning": "Tutor explained object reference equality in JS and shallow state comparisons in React."
            },
            "pacing": {
                "score": 9,
                "evidence": [
                    "Quickly identified infinite loop, explained reference equality, and verified fix."
                ],
                "reasoning": "Fast-paced yet thorough problem solving session."
            },
            "notable_moments": [
                {
                    "timestamp": "Turn 6",
                    "category": "breakthrough",
                    "quote": "Oh my gosh, I was updating the exact state variable that my effect was listening to!",
                    "event": "Student recognized the state-effect feedback loop bug."
                }
            ],
            "recommendations": [
                "Introduce ESLint react-hooks/exhaustive-deps rule to catch dependency issues automatically.",
                "Discuss useMemo / useCallback for stabilizing object dependencies."
            ],
            "overall_feedback": "Outstanding React hook debugging session. Solved an infinite re-render bug with clear explanation.",
            "confidence": 0.97
        }
    else:
        data = {
            "status": "ok",
            "engagement": {
                "score": 8,
                "evidence": [
                    "Honestly, I don't really know. It's just a formula to me right now.",
                    "Oh! I get the words, but on tests I get confused..."
                ],
                "reasoning": "Student expressed initial confusion freely and engaged actively with physical shopping cart analogies."
            },
            "clarity": {
                "score": 9,
                "evidence": [
                    "imagine pushing an empty cart vs cart filled with heavy cases of canned soup"
                ],
                "reasoning": "Tutor built intuitive physical models for F=ma before introducing algebraic manipulation."
            },
            "pacing": {
                "score": 8,
                "evidence": [
                    "Pacing was steady, moving from qualitative cart analogy to net force calculations."
                ],
                "reasoning": "Seamless progression from conceptual intuition to quantitative physics problem solving."
            },
            "notable_moments": [
                {
                    "timestamp": "Turn 7",
                    "category": "breakthrough",
                    "quote": "2/2 = 1! So acceleration doesn't change at all!",
                    "event": "Student connected physical cart intuition with mathematical ratio cancellation."
                }
            ],
            "recommendations": [
                "Continue using physical analogies for force vectors.",
                "Introduce free-body diagrams for complex multi-force scenarios."
            ],
            "overall_feedback": "Highly effective conceptual physics session. Transformed formula memorization into genuine physical intuition.",
            "confidence": 0.93
        }
    return json.dumps(data, indent=2)


def evaluate_transcript(
    transcript_text: str,
    model: str = "gpt-4o-mini",
    prompt_path: str = "prompts/evaluator_prompt.md",
    mock: bool = False,
    extra_feedback_prompt: Optional[str] = None
) -> Tuple[str, Dict[str, int], float]:
    """
    Call OpenAI Chat Completion API (or mock generator) to evaluate transcript.

    Returns:
        Tuple of (raw_response_str, usage_dict, latency_ms)
    """
    start_time = time.time()
    api_key = os.getenv("OPENAI_API_KEY")

    if mock or not api_key or not OPENAI_AVAILABLE:
        time.sleep(0.15)  # Simulate network latency
        raw_response = generate_mock_evaluation(transcript_text)
        latency_ms = round((time.time() - start_time) * 1000, 2)
        # Approximate token counts based on text length (~4 chars per token)
        input_tokens = len(transcript_text) // 4 + 400
        output_tokens = len(raw_response) // 4
        usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
        return raw_response, usage, latency_ms

    client = OpenAI(api_key=api_key)
    system_prompt = load_system_prompt(prompt_path)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Please evaluate the following tutoring transcript:\n\n{transcript_text}"}
    ]

    if extra_feedback_prompt:
        messages.append({
            "role": "user",
            "content": f"Correction Required: {extra_feedback_prompt}"
        })

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.2
    )

    raw_response = response.choices[0].message.content or "{}"
    latency_ms = round((time.time() - start_time) * 1000, 2)

    usage = {
        "input_tokens": getattr(response.usage, "prompt_tokens", 0),
        "output_tokens": getattr(response.usage, "completion_tokens", 0),
        "total_tokens": getattr(response.usage, "total_tokens", 0)
    }

    return raw_response, usage, latency_ms
