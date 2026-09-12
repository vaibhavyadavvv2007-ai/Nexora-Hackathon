"""Concrete candidate ranker with deterministic tie-breaking rules.

Ranks candidate evaluations by final score descending, applying deterministic
tie-breakers on equal scores.
"""

from __future__ import annotations

from typing import List
from backend.core.ranking import BaseRanker
from backend.models.evaluation import CandidateEvaluation


class Ranker(BaseRanker):
    """Ranks candidate evaluations deterministically and assigns 1-indexed ranks."""

    def rank_candidates(
        self, evaluations: List[CandidateEvaluation]
    ) -> List[CandidateEvaluation]:
        """Rank candidates deterministically by final score with explicit tie-breaking rules.

        Tie-break hierarchy:
            1. Final Score (descending)
            2. Required Skill Coverage (descending)
            3. Semantic Requirement Alignment (descending)
            4. Contextual Lexical Relevance (descending)
            5. Candidate ID (ascending for absolute determinism)

        Args:
            evaluations: List of evaluated candidate dossiers.

        Returns:
            Sorted list with 1-indexed `rank` assigned to each evaluation.
        """
        if not evaluations:
            return []

        def sort_key(eval_item: CandidateEvaluation):
            scores = eval_item.scores
            final_score = scores.final_score if scores.final_score is not None else -1.0
            req_cov = scores.required_skill_coverage if scores.required_skill_coverage is not None else -1.0
            sem_align = scores.semantic_requirement_alignment if scores.semantic_requirement_alignment is not None else -1.0
            lex_rel = scores.contextual_lexical_relevance if scores.contextual_lexical_relevance is not None else -1.0
            pref_cov = scores.preferred_skill_coverage if scores.preferred_skill_coverage is not None else -1.0
            return (-final_score, -req_cov, -sem_align, -lex_rel, -pref_cov, eval_item.candidate_id)

        sorted_evals = sorted(evaluations, key=sort_key)

        for rank_idx, eval_item in enumerate(sorted_evals, start=1):
            eval_item.rank = rank_idx

        return sorted_evals
