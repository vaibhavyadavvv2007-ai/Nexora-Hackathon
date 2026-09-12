from typing import Any, List, Optional
from pydantic import BaseModel, Field, computed_field, model_validator
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
    explanation: str = Field(
        default="",
        description="Deterministic factual candidate evaluation justification"
    )

    @model_validator(mode="before")
    @classmethod
    def _remap_evidence_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "keyword_evidence" in data and "keyword_matches" not in data:
                data["keyword_matches"] = data.pop("keyword_evidence")
            if "semantic_evidence" in data and "semantic_matches" not in data:
                data["semantic_matches"] = data.pop("semantic_evidence")
        return data

    @computed_field
    @property
    def name(self) -> str:
        """Alias for candidate_name for frontend compatibility."""
        return self.candidate_name

    @computed_field
    @property
    def required_coverage(self) -> Optional[float]:
        """Convenience accessor for required skill coverage score."""
        return self.scores.required_skill_coverage

    @computed_field
    @property
    def preferred_coverage(self) -> Optional[float]:
        """Convenience accessor for preferred skill coverage score."""
        return self.scores.preferred_skill_coverage

    @computed_field
    @property
    def lexical_score(self) -> Optional[float]:
        """Convenience accessor for contextual lexical relevance score."""
        return self.scores.contextual_lexical_relevance

    @computed_field
    @property
    def semantic_score(self) -> Optional[float]:
        """Convenience accessor for semantic requirement alignment score."""
        return self.scores.semantic_requirement_alignment

    @computed_field
    @property
    def final_score(self) -> Optional[float]:
        """Convenience accessor for fused final score."""
        return self.scores.final_score

    @property
    def keyword_evidence(self) -> List[MatchEvidence]:
        """Convenience accessor for keyword matches evidence."""
        return self.keyword_matches

    @property
    def semantic_evidence(self) -> List[MatchEvidence]:
        """Convenience accessor for semantic matches evidence."""
        return self.semantic_matches
