"""Pydantic schemas for tutoring session transcript evaluations."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Metric(BaseModel):
    """Evaluation metric containing a numeric score (1-10) and supporting evidence."""

    score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Integer score between 1 (poor) and 10 (exceptional)."
    )
    evidence: List[str] = Field(
        ...,
        description="Direct quotes or explicit evidence from the transcript supporting this score."
    )
    reasoning: Optional[str] = Field(
        default="",
        description="Brief qualitative rationale explaining the metric score."
    )


class Moment(BaseModel):
    """Notable event or moment captured during the tutoring session."""

    timestamp: str = Field(
        default="N/A",
        description="Timestamp or turn label (e.g., 'Turn 3', '03:15', 'N/A')."
    )
    category: str = Field(
        ...,
        description="Type of moment: 'misconception', 'breakthrough', 'question', 'disengagement', etc."
    )
    quote: str = Field(
        ...,
        description="Exact transcript quote representing the moment."
    )
    event: str = Field(
        ...,
        description="Brief summary or context explaining why this moment is notable."
    )


class Evaluation(BaseModel):
    """Complete evaluation report for a tutoring session transcript."""

    status: Literal["ok"] = Field(
        default="ok",
        description="Execution status indicator."
    )
    engagement: Metric = Field(
        ...,
        description="Evaluation of student active participation, question volume, and enthusiasm."
    )
    clarity: Metric = Field(
        ...,
        description="Evaluation of tutor explanation structure, analogies, and conceptual accuracy."
    )
    pacing: Metric = Field(
        ...,
        description="Evaluation of session progression speed and time allocated to concepts."
    )
    notable_moments: List[Moment] = Field(
        default_factory=list,
        description="Key moments such as breakthroughs, misconceptions, or key questions."
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable pedagogical recommendations for future sessions."
    )
    overall_feedback: str = Field(
        ...,
        description="Comprehensive summary feedback on the session dynamics."
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score in the evaluation accuracy (0.0 to 1.0)."
    )


class FailedEvaluation(BaseModel):
    """Fallback schema returned when transcript evaluation violates schema after max retries."""

    status: Literal["failed"] = "failed"
    error: str = Field(
        ...,
        description="Description of the validation or parsing failure."
    )
    attempts: int = Field(
        default=2,
        description="Number of attempts made before failing."
    )
    raw_response: Optional[str] = Field(
        default=None,
        description="Raw output produced by the LLM prior to validation failure."
    )
