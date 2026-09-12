from abc import ABC, abstractmethod
from typing import Dict, List
from pydantic import BaseModel, Field
from backend.models.evaluation import CandidateEvaluation


class PairwiseComparisonResult(BaseModel):
    """Deterministic comparison between two candidate evaluation dossiers."""
    higher_candidate_id: str
    lower_candidate_id: str
    score_delta: float
    required_skill_delta: int
    decisive_factors: List[str] = Field(default_factory=list)
    explanation: str


class BaseExplainer(ABC):
    """Abstract interface for deterministic, template-backed candidate explanations."""

    @abstractmethod
    def explain_candidate(self, evaluation: CandidateEvaluation) -> str:
        """Generate a factual, evidence-backed explanation for a single candidate dossier.

        Note:
            Must never invent skills or hallucinate evidence. Must explicitly cite
            matched skills, missing required skills, and top evidence.
        """
        raise NotImplementedError

    @abstractmethod
    def explain_top_candidates(
        self,
        ranked_evaluations: List[CandidateEvaluation],
        top_k: int = 3
    ) -> Dict[str, str]:
        """Generate structured justifications for the top K ranked candidates."""
        raise NotImplementedError

    @abstractmethod
    def compare_pairwise(
        self,
        candidate_a: CandidateEvaluation,
        candidate_b: CandidateEvaluation
    ) -> PairwiseComparisonResult:
        """Compare two candidates directly using stored evaluation records.

        Note:
            Must NOT delegate to an LLM or recalculate rankings. Directly evaluates
            the deltas in required skill coverage, semantic alignment, and keyword evidence.
        """
        raise NotImplementedError
