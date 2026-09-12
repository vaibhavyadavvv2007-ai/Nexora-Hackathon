"""Concrete scorer for multi-signal component score calculation and fusion.

Formula:
    Final Score = w_req * Required Skill Coverage
                + w_sem * Semantic Requirement Alignment
                + w_lex * Contextual Lexical Relevance
                + w_pref * Preferred Skill Coverage

All weights are configurable and all component scores are normalized to [0, 1].
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set
from backend.config.settings import Settings, get_settings
from backend.core.ranking import BaseScorer
from backend.models.evaluation import ScoreStructure
from backend.models.evidence import MatchEvidence
from backend.models.requirement import Requirement
from backend.models.skill import Skill


class Scorer(BaseScorer):
    """Calculates component scores and weighted final score for candidate evaluation."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self._settings = settings or get_settings()
        if weights is not None:
            self.w_required = weights.get("required_skill_coverage", 0.35)
            self.w_semantic = weights.get("semantic_requirement_alignment", 0.35)
            self.w_lexical = weights.get("contextual_lexical_relevance", 0.20)
            self.w_preferred = weights.get("preferred_skill_coverage", 0.10)
        else:
            self.w_required = self._settings.WEIGHT_REQUIRED_SKILL_COVERAGE
            self.w_semantic = self._settings.WEIGHT_SEMANTIC_ALIGNMENT
            self.w_lexical = self._settings.WEIGHT_CONTEXTUAL_LEXICAL_RELEVANCE
            self.w_preferred = self._settings.WEIGHT_PREFERRED_SKILL_COVERAGE

    def calculate_score_breakdown(
        self,
        matched_required: List[Skill],
        all_required: List[Requirement],
        matched_preferred: List[Skill],
        all_preferred: List[Requirement],
        semantic_matches: List[MatchEvidence],
        keyword_matches: List[MatchEvidence],
    ) -> ScoreStructure:
        """Compute the component scores and fused final score bounded to [0, 1]."""

        # 1. Required Skill Coverage [0, 1]
        if all_required:
            req_coverage = min(len(matched_required) / len(all_required), 1.0)
        else:
            req_coverage = 0.0

        # 2. Preferred Skill Coverage [0, 1]
        if all_preferred:
            pref_coverage = min(len(matched_preferred) / len(all_preferred), 1.0)
        else:
            pref_coverage = 0.0

        # Target requirements for contextual/semantic relevance
        target_reqs = all_required + all_preferred
        target_req_ids = {r.id for r in target_reqs}

        # 3. Semantic Requirement Alignment [0, 1]
        # Strongest semantic similarity per requirement, averaged across target requirements
        if target_reqs:
            req_max_sim: Dict[str, float] = {r.id: 0.0 for r in target_reqs}
            for m in semantic_matches:
                sim = m.similarity if m.similarity is not None else m.confidence
                if m.requirement.id in req_max_sim:
                    if sim > req_max_sim[m.requirement.id]:
                        req_max_sim[m.requirement.id] = sim
            sem_alignment = sum(req_max_sim.values()) / len(target_reqs)
        elif semantic_matches:
            # Fallback if no explicit requirements in target_reqs
            sem_alignment = sum(
                m.similarity if m.similarity is not None else m.confidence
                for m in semantic_matches
            ) / len(semantic_matches)
        else:
            sem_alignment = 0.0

        sem_alignment = max(0.0, min(1.0, sem_alignment))

        # 4. Contextual Lexical Relevance [0, 1]
        # Strongest lexical match per requirement, averaged across target requirements
        if target_reqs:
            req_max_lex: Dict[str, float] = {r.id: 0.0 for r in target_reqs}
            for m in keyword_matches:
                if m.requirement.id in req_max_lex:
                    if m.confidence > req_max_lex[m.requirement.id]:
                        req_max_lex[m.requirement.id] = m.confidence
            lex_relevance = sum(req_max_lex.values()) / len(target_reqs)
        elif keyword_matches:
            lex_relevance = sum(m.confidence for m in keyword_matches) / len(keyword_matches)
        else:
            lex_relevance = 0.0

        lex_relevance = max(0.0, min(1.0, lex_relevance))

        # 5. Fused Final Score [0, 1]
        final_score = (
            self.w_required * req_coverage
            + self.w_semantic * sem_alignment
            + self.w_lexical * lex_relevance
            + self.w_preferred * pref_coverage
        )
        final_score = max(0.0, min(1.0, final_score))

        return ScoreStructure(
            required_skill_coverage=round(req_coverage, 4),
            semantic_requirement_alignment=round(sem_alignment, 4),
            contextual_lexical_relevance=round(lex_relevance, 4),
            preferred_skill_coverage=round(pref_coverage, 4),
            final_score=round(final_score, 4),
        )
