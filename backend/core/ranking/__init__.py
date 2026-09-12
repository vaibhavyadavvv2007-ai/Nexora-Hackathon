from abc import ABC, abstractmethod
from typing import List
from backend.models.document import JobDescription, Resume
from backend.models.evaluation import CandidateEvaluation, ScoreStructure
from backend.models.evidence import MatchEvidence
from backend.models.requirement import Requirement
from backend.models.skill import Skill


class BaseScorer(ABC):
    """Abstract interface for multi-signal component score calculation and normalization."""

    @abstractmethod
    def calculate_score_breakdown(
        self,
        matched_required: List[Skill],
        all_required: List[Requirement],
        matched_preferred: List[Skill],
        all_preferred: List[Requirement],
        semantic_matches: List[MatchEvidence],
        keyword_matches: List[MatchEvidence]
    ) -> ScoreStructure:
        """Compute the component scores and fused final score bounded to [0, 1].

        Formula:
            Final Score = 0.35 * Required Skill Coverage
                        + 0.35 * Semantic Requirement Alignment
                        + 0.20 * Contextual Lexical Relevance
                        + 0.10 * Preferred Skill Coverage

        Returns:
            Populated ScoreStructure instance.
        """
        raise NotImplementedError


class BaseRanker(ABC):
    """Abstract interface for candidate ranking and dossier compilation."""

    @abstractmethod
    def rank_candidates(
        self,
        evaluations: List[CandidateEvaluation]
    ) -> List[CandidateEvaluation]:
        """Rank candidates deterministically by final score with explicit tie-breaking rules.

        Args:
            evaluations: List of evaluated candidate dossiers.

        Returns:
            Sorted list with 1-indexed `rank` assigned to each evaluation.
        """
        raise NotImplementedError
