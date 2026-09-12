"""Deterministic, template-based candidate and pairwise explanation generator.

Strictly factual:
- Never invents skills or hallucinates evidence.
- Explicitly cites matched skills, missing required skills, and top evidence chunks.
- Computes contrastive deltas directly from stored evaluation dossiers.
- Zero LLM usage.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set
from backend.core.explanations import BaseExplainer, PairwiseComparisonResult
from backend.app.schemas.evaluation import MissingSkillsDiff, PairwiseComparisonResponse
from backend.models.evaluation import CandidateEvaluation
from backend.models.evidence import EvidenceChunk


class TemplateExplainer(BaseExplainer):
    """Deterministic, template-driven explainer producing auditable justifications."""

    def explain_candidate(self, evaluation: CandidateEvaluation) -> str:
        """Generate a factual, evidence-backed explanation for a single candidate dossier."""
        name = evaluation.candidate_name or f"Candidate {evaluation.candidate_id}"
        rank_str = f"Rank #{evaluation.rank}" if evaluation.rank else "Evaluated"
        score_pct = f"{(evaluation.final_score or 0.0) * 100:.1f}%"
        req_pct = f"{(evaluation.required_coverage or 0.0) * 100:.1f}%"
        sem_pct = f"{(evaluation.semantic_score or 0.0) * 100:.1f}%"
        lex_pct = f"{(evaluation.lexical_score or 0.0) * 100:.1f}%"

        parts = [
            f"{name} ({rank_str}) achieved an overall score of {score_pct}."
        ]

        # Matched required skills
        matched_names = [
            getattr(s, "name", None) or getattr(s, "surface_form", None) or getattr(s, "canonical_name", str(s))
            for s in evaluation.matched_required
        ]
        if matched_names:
            parts.append(
                f"Demonstrated explicit required skills: {', '.join(matched_names[:8])}"
                f"{' and more' if len(matched_names) > 8 else ''} ({req_pct} coverage)."
            )
        else:
            parts.append(f"No explicit required skills matched ({req_pct} coverage).")

        # Missing required requirements
        missing_names = [
            getattr(r, "name", None) or getattr(r, "canonical_name", str(r))
            for r in evaluation.missing_required
        ]
        if missing_names:
            parts.append(
                f"Missing required skills/criteria: {', '.join(missing_names[:6])}"
                f"{' and more' if len(missing_names) > 6 else ''}."
            )
        else:
            parts.append("Satisfied 100% of explicit required skills.")

        # Preferred skills
        matched_pref = [
            getattr(s, "name", None) or getattr(s, "surface_form", None) or getattr(s, "canonical_name", str(s))
            for s in evaluation.matched_preferred
        ]
        if matched_pref:
            parts.append(f"Preferred skills identified: {', '.join(matched_pref[:5])}.")

        # Multi-signal scores
        parts.append(
            f"Multi-signal alignment: Semantic relevance {sem_pct}, Contextual lexical match {lex_pct}."
        )

        return " ".join(parts)

    def explain_top_candidates(
        self,
        ranked_evaluations: List[CandidateEvaluation],
        top_k: int = 3
    ) -> Dict[str, str]:
        """Generate structured justifications for the top K ranked candidates."""
        justifications: Dict[str, str] = {}
        for candidate in ranked_evaluations[:top_k]:
            justifications[candidate.candidate_id] = self.explain_candidate(candidate)
        return justifications

    def compare_pairwise(
        self,
        candidate_a: CandidateEvaluation,
        candidate_b: CandidateEvaluation
    ) -> PairwiseComparisonResult:
        """Compare two candidates directly using stored evaluation records."""
        score_a = candidate_a.final_score or 0.0
        score_b = candidate_b.final_score or 0.0

        if score_a >= score_b:
            higher, lower = candidate_a, candidate_b
        else:
            higher, lower = candidate_b, candidate_a

        score_delta = round(abs(score_a - score_b), 4)
        req_delta = len(higher.matched_required) - len(lower.matched_required)

        decisive_factors: List[str] = []
        if req_delta > 0:
            decisive_factors.append(f"Higher required skill count (+{req_delta})")
        elif req_delta < 0:
            decisive_factors.append(f"Fewer required skills matched ({req_delta})")

        sem_diff = (higher.semantic_score or 0.0) - (lower.semantic_score or 0.0)
        if abs(sem_diff) >= 0.05:
            decisive_factors.append(f"Semantic requirement alignment delta ({sem_diff:+.1%})")

        lex_diff = (higher.lexical_score or 0.0) - (lower.lexical_score or 0.0)
        if abs(lex_diff) >= 0.05:
            decisive_factors.append(f"Contextual lexical relevance delta ({lex_diff:+.1%})")

        pref_delta = len(higher.matched_preferred) - len(lower.matched_preferred)
        if pref_delta != 0:
            decisive_factors.append(f"Preferred skills delta ({pref_delta:+d})")

        if not decisive_factors:
            decisive_factors.append("Tie-broken by deterministic criteria")

        explanation = (
            f"{higher.candidate_name} ranks higher than {lower.candidate_name} with a score "
            f"advantage of {score_delta * 100:.1f}%. Decisive drivers: {'; '.join(decisive_factors)}."
        )

        return PairwiseComparisonResult(
            higher_candidate_id=higher.candidate_id,
            lower_candidate_id=lower.candidate_id,
            score_delta=score_delta,
            required_skill_delta=req_delta,
            decisive_factors=decisive_factors,
            explanation=explanation,
        )

    def compare_pairwise_detailed(
        self,
        candidate_a: CandidateEvaluation,
        candidate_b: CandidateEvaluation
    ) -> PairwiseComparisonResponse:
        """Produce full contrastive comparison payload expected by the frontend."""
        score_a = candidate_a.final_score or 0.0
        score_b = candidate_b.final_score or 0.0
        score_delta = round(score_a - score_b, 4)

        req_count_a = len(candidate_a.matched_required)
        req_count_b = len(candidate_b.matched_required)
        req_delta = req_count_a - req_count_b

        sem_a = candidate_a.semantic_score or 0.0
        sem_b = candidate_b.semantic_score or 0.0
        sem_delta = round(sem_a - sem_b, 4)

        lex_a = candidate_a.lexical_score or 0.0
        lex_b = candidate_b.lexical_score or 0.0
        lex_delta = round(lex_a - lex_b, 4)

        winner_id = candidate_a.candidate_id if score_a >= score_b else candidate_b.candidate_id

        # Missing skills diff
        missing_a: Set[str] = {r.canonical_name for r in candidate_a.missing_required}
        missing_b: Set[str] = {r.canonical_name for r in candidate_b.missing_required}

        only_a_missing = sorted(list(missing_a - missing_b))
        only_b_missing = sorted(list(missing_b - missing_a))
        both_missing = sorted(list(missing_a & missing_b))

        # Advantages
        advantages_a: List[str] = []
        advantages_b: List[str] = []

        if req_count_a > req_count_b:
            advantages_a.append(f"Matches {req_count_a - req_count_b} more required skills")
        elif req_count_b > req_count_a:
            advantages_b.append(f"Matches {req_count_b - req_count_a} more required skills")

        if sem_delta > 0.03:
            advantages_a.append(f"+{sem_delta * 100:.1f}% higher semantic requirement alignment")
        elif sem_delta < -0.03:
            advantages_b.append(f"+{abs(sem_delta) * 100:.1f}% higher semantic requirement alignment")

        if lex_delta > 0.03:
            advantages_a.append(f"+{lex_delta * 100:.1f}% stronger contextual lexical relevance")
        elif lex_delta < -0.03:
            advantages_b.append(f"+{abs(lex_delta) * 100:.1f}% stronger contextual lexical relevance")

        pref_a = len(candidate_a.matched_preferred)
        pref_b = len(candidate_b.matched_preferred)
        if pref_a > pref_b:
            advantages_a.append(f"+{pref_a - pref_b} additional preferred skills matched")
        elif pref_b > pref_a:
            advantages_b.append(f"+{pref_b - pref_a} additional preferred skills matched")

        if only_b_missing:
            advantages_a.append(f"Possesses {', '.join(only_b_missing[:3])} which Candidate B lacks")
        if only_a_missing:
            advantages_b.append(f"Possesses {', '.join(only_a_missing[:3])} which Candidate A lacks")

        # Select representative evidence chunks
        key_evidence: List[EvidenceChunk] = []
        if candidate_a.evidence:
            key_evidence.append(candidate_a.evidence[0])
        if candidate_b.evidence:
            key_evidence.append(candidate_b.evidence[0])

        # Narrative explanation
        winner_name = candidate_a.candidate_name if winner_id == candidate_a.candidate_id else candidate_b.candidate_name
        loser_name = candidate_b.candidate_name if winner_id == candidate_a.candidate_id else candidate_a.candidate_name
        diff_pct = abs(score_delta) * 100

        explanation = (
            f"{winner_name} outperforms {loser_name} with an overall score advantage of {diff_pct:.1f}%. "
            f"Key differentiators: {winner_name} matches {max(req_count_a, req_count_b)} required skills "
            f"vs {min(req_count_a, req_count_b)}. "
            f"Semantic alignment difference is {abs(sem_delta) * 100:.1f}%."
        )

        return PairwiseComparisonResponse(
            candidate_a_id=candidate_a.candidate_id,
            candidate_b_id=candidate_b.candidate_id,
            winner_id=winner_id,
            score_delta=score_delta,
            required_skill_delta=req_delta,
            semantic_delta=sem_delta,
            lexical_delta=lex_delta,
            explanation=explanation,
            advantages_a=advantages_a,
            advantages_b=advantages_b,
            missing_skills_diff=MissingSkillsDiff(
                only_a_missing=only_a_missing,
                only_b_missing=only_b_missing,
                both_missing=both_missing,
            ),
            key_evidence_diff=key_evidence,
        )
