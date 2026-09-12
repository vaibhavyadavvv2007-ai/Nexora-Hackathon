"""FastAPI request and response schemas for candidate evaluation and ranking."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.models.document import JobDescription
from backend.models.evaluation import CandidateEvaluation
from backend.models.evidence import EvidenceChunk


class FailedUploadItem(BaseModel):
    """Details of a failed file upload or parsing operation."""
    filename: str
    reason: str


class ResumeBatchUploadResponse(BaseModel):
    """Response returned after uploading a batch of candidate resumes."""
    uploaded: int = Field(..., description="Number of successfully stored resumes")
    failed: List[FailedUploadItem] = Field(
        default_factory=list,
        description="List of files that failed validation or upload"
    )
    job_id: Optional[str] = Field(default=None, description="Associated job description ID")
    files: Optional[List[str]] = Field(
        default_factory=list,
        description="Filenames of successfully uploaded resumes"
    )


class StartAnalysisResponse(BaseModel):
    """Response returned when triggering pipeline evaluation."""
    task_id: str = Field(..., description="Unique asynchronous task identifier")
    status: str = Field(default="processing", description="Initial execution state")


class ProcessingStatusResponse(BaseModel):
    """Telemetry and progress status for a running or completed evaluation pipeline."""
    stage: str = Field(
        default="idle",
        description="Pipeline stage: idle | uploading | parsing | matching | ranking | complete | error"
    )
    progress: int = Field(default=0, ge=0, le=100, description="Percentage complete (0-100)")
    message: str = Field(default="Ready", description="Human-readable progress description")
    jd_processed: bool = Field(default=False, description="Whether the JD has been parsed")
    resumes_processed: int = Field(default=0, ge=0, description="Number of resumes parsed")
    resumes_total: int = Field(default=0, ge=0, description="Total resumes in batch")
    semantic_model_status: str = Field(
        default="idle",
        description="Semantic engine state: idle | loading | encoding | ready | error"
    )
    keyword_engine_status: str = Field(
        default="idle",
        description="Keyword engine state: idle | indexing | matching | ready | error"
    )
    ranking_status: str = Field(
        default="idle",
        description="Ranking status: idle | computing | complete | error"
    )
    failed_resumes: List[FailedUploadItem] = Field(
        default_factory=list,
        description="Resumes that failed during extraction or parsing"
    )


class EvaluationResultResponse(BaseModel):
    """Complete ranked candidates payload for a job description."""
    job_description: JobDescription = Field(..., description="Evaluated job description")
    candidates: List[CandidateEvaluation] = Field(
        default_factory=list,
        description="Ranked candidate evaluation dossiers"
    )
    processing_time_ms: int = Field(default=0, ge=0, description="Elapsed pipeline runtime in ms")
    model_version: str = Field(default="nexora-engine-v1.0", description="Pipeline engine version")
    failed_candidates: Optional[List[FailedUploadItem]] = Field(
        default=None,
        description="Candidates excluded due to parsing errors"
    )


class MissingSkillsDiff(BaseModel):
    """Granular diff of missing required skills between two candidates."""
    only_a_missing: List[str] = Field(default_factory=list)
    only_b_missing: List[str] = Field(default_factory=list)
    both_missing: List[str] = Field(default_factory=list)


class PairwiseComparisonResponse(BaseModel):
    """Structured contrastive comparison between Candidate A and Candidate B."""
    candidate_a_id: str
    candidate_b_id: str
    winner_id: str
    score_delta: float = Field(..., description="Score difference (candidate_a.final_score - candidate_b.final_score)")
    required_skill_delta: int = Field(
        ...,
        description="Required skill match difference (len(a.matched_required) - len(b.matched_required))"
    )
    semantic_delta: float = Field(
        ...,
        description="Semantic alignment score difference (a.semantic_score - b.semantic_score)"
    )
    lexical_delta: Optional[float] = Field(
        default=None,
        description="Lexical score difference (a.lexical_score - b.lexical_score)"
    )
    explanation: str = Field(..., description="Factual, deterministic comparative narrative")
    advantages_a: List[str] = Field(default_factory=list, description="Specific advantages of Candidate A")
    advantages_b: List[str] = Field(default_factory=list, description="Specific advantages of Candidate B")
    missing_skills_diff: Optional[MissingSkillsDiff] = Field(
        default=None,
        description="Comparison of missing requirements"
    )
    key_evidence_diff: Optional[List[EvidenceChunk]] = Field(
        default_factory=list,
        description="Representative differentiating evidence chunks"
    )
