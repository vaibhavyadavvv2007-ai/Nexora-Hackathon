"""Ranking engine orchestrator for multi-signal matching, score fusion, and ranking.

Coordinates:
- KeywordMatcher (explicit skill matching & BM25 contextual lexical relevance)
- SemanticMatcher (local sentence-transformer cosine similarity alignment)
- Scorer (component normalization and configurable score fusion)
- Ranker (deterministic tie-breaking and 1-indexed rank assignment)

Modes supported:
- COMBINED: 0.35 * Req + 0.35 * Sem + 0.20 * Lex + 0.10 * Pref
- KEYWORD_ONLY: Evaluates explicit skills and lexical relevance (semantic weight = 0)
- SEMANTIC_ONLY: Evaluates semantic alignment only (keyword weights = 0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional

from backend.config.settings import Settings, get_settings
from backend.core.matching.keyword_matcher import KeywordMatcher
from backend.core.matching.semantic_matcher import SemanticMatcher
from backend.core.ranking.ranker import Ranker
from backend.core.ranking.scorer import Scorer
from backend.models.document import JobDescription, Resume
from backend.models.enums import RequirementType
from backend.models.evaluation import CandidateEvaluation, ScoreStructure
from backend.models.evidence import MatchEvidence
from backend.models.requirement import Requirement
from backend.models.skill import Skill


class EvaluationMode(str, Enum):
    """Evaluation signal fusion modes."""
    COMBINED = "combined"
    KEYWORD_ONLY = "keyword-only"
    SEMANTIC_ONLY = "semantic-only"


@dataclass
class ModeSummary:
    """Summary of ranking results for a single evaluation mode."""
    mode: str
    full_ranking: List[CandidateEvaluation]
    top_3: List[CandidateEvaluation]
    score_distribution: Dict[str, float]


@dataclass
class PositionChange:
    """Tracks position shift of a candidate across evaluation modes."""
    candidate_id: str
    candidate_name: str
    rank_combined: int
    rank_keyword_only: int
    rank_semantic_only: int
    delta_vs_keyword: int  # rank_keyword_only - rank_combined (positive = combined improved rank)
    delta_vs_semantic: int  # rank_semantic_only - rank_combined (positive = combined improved rank)


@dataclass
class AblationReport:
    """Complete ablation study report across all evaluation modes."""
    job_id: str
    job_title: str
    total_candidates: int
    modes: Dict[str, ModeSummary]
    position_changes: List[PositionChange]

    def get_top_3(self, mode: EvaluationMode | str) -> List[CandidateEvaluation]:
        key = mode.value if isinstance(mode, EvaluationMode) else mode
        return self.modes[key].top_3


def compute_distribution_stats(scores: List[float]) -> Dict[str, float]:
    """Compute summary statistics for a list of scores."""
    if not scores:
        return {"count": 0.0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "median": 0.0}

    n = len(scores)
    mean_val = sum(scores) / n
    variance = sum((s - mean_val) ** 2 for s in scores) / n if n > 1 else 0.0
    std_val = math.sqrt(variance)
    sorted_scores = sorted(scores)
    median_val = (
        sorted_scores[n // 2]
        if n % 2 != 0
        else (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2.0
    )

    return {
        "count": float(n),
        "mean": round(mean_val, 4),
        "std": round(std_val, 4),
        "min": round(min(scores), 4),
        "max": round(max(scores), 4),
        "median": round(median_val, 4),
    }


class RankingEngine:
    """Unified matching, score fusion, and candidate ranking engine."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        keyword_matcher: Optional[KeywordMatcher] = None,
        semantic_matcher: Optional[SemanticMatcher] = None,
        scorer: Optional[Scorer] = None,
        ranker: Optional[Ranker] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self.keyword_matcher = keyword_matcher or KeywordMatcher(self._settings)
        self.semantic_matcher = semantic_matcher or SemanticMatcher(self._settings)
        self.scorer = scorer or Scorer(self._settings)
        self.ranker = ranker or Ranker()

        # Build specialized scorers for ablation modes
        self._combined_scorer = self.scorer

        # Keyword-only: semantic weight = 0, remaining weights normalized to sum to 1.0
        w_req = self._settings.WEIGHT_REQUIRED_SKILL_COVERAGE
        w_lex = self._settings.WEIGHT_CONTEXTUAL_LEXICAL_RELEVANCE
        w_pref = self._settings.WEIGHT_PREFERRED_SKILL_COVERAGE
        kw_total = w_req + w_lex + w_pref
        if kw_total > 0:
            kw_weights = {
                "required_skill_coverage": round(w_req / kw_total, 4),
                "semantic_requirement_alignment": 0.0,
                "contextual_lexical_relevance": round(w_lex / kw_total, 4),
                "preferred_skill_coverage": round(w_pref / kw_total, 4),
            }
        else:
            kw_weights = {
                "required_skill_coverage": 0.55,
                "semantic_requirement_alignment": 0.0,
                "contextual_lexical_relevance": 0.35,
                "preferred_skill_coverage": 0.10,
            }
        self._keyword_scorer = Scorer(self._settings, weights=kw_weights)

        # Semantic-only: keyword weights = 0, semantic weight = 1.0
        sem_weights = {
            "required_skill_coverage": 0.0,
            "semantic_requirement_alignment": 1.0,
            "contextual_lexical_relevance": 0.0,
            "preferred_skill_coverage": 0.0,
        }
        self._semantic_scorer = Scorer(self._settings, weights=sem_weights)

    def evaluate_candidate(
        self,
        resume: Resume,
        jd: JobDescription,
        mode: EvaluationMode = EvaluationMode.COMBINED,
    ) -> CandidateEvaluation:
        """Evaluate a single candidate against a Job Description under the specified mode.

        Invariants enforced:
        1. Explicit named skill matching is authoritative for matched_required/missing_required.
        2. Semantic similarity never converts a missing named technology to an explicit match.
        3. Lexical relevance is independent of explicit coverage.
        4. All component scores and the final score are bounded to [0, 1].
        """
        all_required = [r for r in jd.requirements if r.type == RequirementType.REQUIRED]
        all_preferred = [r for r in jd.requirements if r.type == RequirementType.PREFERRED]

        # Explicit skill-matchable requirements for coverage denominators
        matchable_required = [r for r in all_required if getattr(r, "is_skill_matchable", True)]
        matchable_preferred = [r for r in all_preferred if getattr(r, "is_skill_matchable", True)]
        coverage_required = matchable_required if matchable_required else all_required
        coverage_preferred = matchable_preferred if matchable_preferred else all_preferred

        # 1. Explicit keyword matching
        matched_req, missing_req = self.keyword_matcher.match_explicit_skills(
            resume.skills, coverage_required
        )

        # Prevent double-counting: skills claimed by required are not reused for preferred
        matched_req_canonicals = {s.canonical_name for s in matched_req}
        remaining_skills = [
            s for s in resume.skills if s.canonical_name not in matched_req_canonicals
        ]
        matched_pref, _ = self.keyword_matcher.match_explicit_skills(
            remaining_skills, coverage_preferred
        )

        # 2. Contextual lexical evidence (BM25)
        keyword_matches = self.keyword_matcher.compute_lexical_evidence(resume, jd)

        # 3. Semantic alignment (SentenceTransformer)
        if mode != EvaluationMode.KEYWORD_ONLY:
            semantic_matches = self.semantic_matcher.compute_semantic_alignment(resume, jd)
        else:
            semantic_matches = []

        # 4. Score fusion based on evaluation mode
        if mode == EvaluationMode.COMBINED:
            scores = self._combined_scorer.calculate_score_breakdown(
                matched_required=matched_req,
                all_required=coverage_required,
                matched_preferred=matched_pref,
                all_preferred=coverage_preferred,
                semantic_matches=semantic_matches,
                keyword_matches=keyword_matches,
            )
        elif mode == EvaluationMode.KEYWORD_ONLY:
            scores = self._keyword_scorer.calculate_score_breakdown(
                matched_required=matched_req,
                all_required=coverage_required,
                matched_preferred=matched_pref,
                all_preferred=coverage_preferred,
                semantic_matches=[],
                keyword_matches=keyword_matches,
            )
        elif mode == EvaluationMode.SEMANTIC_ONLY:
            scores = self._semantic_scorer.calculate_score_breakdown(
                matched_required=[],
                all_required=coverage_required,
                matched_preferred=[],
                all_preferred=coverage_preferred,
                semantic_matches=semantic_matches,
                keyword_matches=[],
            )
        else:
            raise ValueError(f"Unsupported evaluation mode: {mode}")

        return CandidateEvaluation(
            candidate_id=resume.candidate_id,
            candidate_name=resume.name,
            scores=scores,
            matched_required=matched_req,
            matched_preferred=matched_pref,
            missing_required=missing_req,
            semantic_matches=semantic_matches,
            keyword_matches=keyword_matches,
            evidence=list(resume.evidence_chunks),
            rank=None,
        )

    def evaluate_and_rank_batch(
        self,
        resumes: List[Resume],
        jd: JobDescription,
        mode: EvaluationMode = EvaluationMode.COMBINED,
    ) -> List[CandidateEvaluation]:
        """Evaluate a batch of candidate resumes and rank them deterministically.

        Tie-breaking hierarchy:
        1. final_score (descending)
        2. required_skill_coverage (descending)
        3. semantic_requirement_alignment (descending)
        4. contextual_lexical_relevance (descending)
        5. preferred_skill_coverage (descending)
        6. candidate_id (ascending)
        """
        evaluations = [
            self.evaluate_candidate(resume, jd, mode=mode)
            for resume in resumes
        ]
        return self.ranker.rank_candidates(evaluations)

    def run_ablation_study(
        self,
        resumes: List[Resume],
        jd: JobDescription,
    ) -> AblationReport:
        """Run an ablation study comparing KEYWORD_ONLY, SEMANTIC_ONLY, and COMBINED modes.

        Returns full ranking, top 3, score distribution, and rank delta comparison.
        """
        modes_summary: Dict[str, ModeSummary] = {}
        rank_lookup: Dict[str, Dict[str, int]] = {
            EvaluationMode.COMBINED.value: {},
            EvaluationMode.KEYWORD_ONLY.value: {},
            EvaluationMode.SEMANTIC_ONLY.value: {},
        }

        candidate_names: Dict[str, str] = {r.candidate_id: r.name for r in resumes}

        for eval_mode in [
            EvaluationMode.COMBINED,
            EvaluationMode.KEYWORD_ONLY,
            EvaluationMode.SEMANTIC_ONLY,
        ]:
            ranked = self.evaluate_and_rank_batch(resumes, jd, mode=eval_mode)
            scores = [e.scores.final_score for e in ranked if e.scores.final_score is not None]
            dist = compute_distribution_stats(scores)
            top_3 = ranked[:3]

            for item in ranked:
                if item.rank is not None:
                    rank_lookup[eval_mode.value][item.candidate_id] = item.rank

            modes_summary[eval_mode.value] = ModeSummary(
                mode=eval_mode.value,
                full_ranking=ranked,
                top_3=top_3,
                score_distribution=dist,
            )

        # Compute position changes
        position_changes: List[PositionChange] = []
        for cand_id, name in candidate_names.items():
            r_comb = rank_lookup[EvaluationMode.COMBINED.value].get(cand_id, 0)
            r_kw = rank_lookup[EvaluationMode.KEYWORD_ONLY.value].get(cand_id, 0)
            r_sem = rank_lookup[EvaluationMode.SEMANTIC_ONLY.value].get(cand_id, 0)

            position_changes.append(
                PositionChange(
                    candidate_id=cand_id,
                    candidate_name=name,
                    rank_combined=r_comb,
                    rank_keyword_only=r_kw,
                    rank_semantic_only=r_sem,
                    delta_vs_keyword=r_kw - r_comb,
                    delta_vs_semantic=r_sem - r_comb,
                )
            )

        # Sort position changes by combined rank
        position_changes.sort(key=lambda p: p.rank_combined)

        return AblationReport(
            job_id=jd.id,
            job_title=jd.title,
            total_candidates=len(resumes),
            modes=modes_summary,
            position_changes=position_changes,
        )
