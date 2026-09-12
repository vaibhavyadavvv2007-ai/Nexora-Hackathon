from typing import List, Optional
from pydantic import BaseModel, Field
from backend.models.evidence import EvidenceChunk, MatchEvidence
from backend.models.requirement import Requirement
from backend.models.skill import Skill


class ScoreStructure(BaseModel):
    """Component score breakdown for candidate ranking."""
    required_skill_coverage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Coverage of explicit named required skills [0, 1]"
    )
    semantic_requirement_alignment: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Semantic requirement-to-evidence alignment [0, 1]"
    )
    contextual_lexical_relevance: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="BM25 lexical context relevance [0, 1]"
    )
    preferred_skill_coverage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Coverage of explicit named preferred skills [0, 1]"
    )
    final_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Fused overall candidate score [0, 1]"
    )


class CandidateEvaluation(BaseModel):
    """Full structured evaluation dossier for an individual candidate."""
    candidate_id: str = Field(..., description="Unique applicant ID matching Resume.candidate_id")
    candidate_name: str = Field(..., description="Candidate display name")
    scores: ScoreStructure = Field(default_factory=ScoreStructure, description="Calculated component scores")
    matched_required: List[Skill] = Field(
        default_factory=list,
        description="Authoritative list of explicitly matched required skills"
    )
    matched_preferred: List[Skill] = Field(
        default_factory=list,
        description="Authoritative list of explicitly matched preferred skills"
    )
    missing_required: List[Requirement] = Field(
        default_factory=list,
        description="Authoritative list of missing required requirements"
    )
    semantic_matches: List[MatchEvidence] = Field(
        default_factory=list,
        description="Evidence matches identified by semantic engine"
    )
    keyword_matches: List[MatchEvidence] = Field(
        default_factory=list,
        description="Evidence matches identified by keyword/lexical engine"
    )
    evidence: List[EvidenceChunk] = Field(
        default_factory=list,
        description="All extracted candidate evidence chunks cited in evaluation"
    )
    rank: Optional[int] = Field(default=None, ge=1, description="Final candidate rank (1-indexed)")
