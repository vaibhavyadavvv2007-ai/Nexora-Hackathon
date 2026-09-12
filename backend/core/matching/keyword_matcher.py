"""Concrete keyword matching engine.

Implements ``BaseKeywordMatcher`` with a four-tier cascade for explicit skill
matching and BM25-based contextual lexical relevance scoring.

Key invariants
--------------
* A resume skill can satisfy **at most one** requirement (duplicate suppression).
* BM25 lexical evidence is computed **independently** of the explicit
  matched/missing verdict and never changes it.
* ``RELATED_SKILLS`` edges produce ``MatchEvidence`` records tagged
  ``MatchType.PHRASE`` but do **not** flip a "missing" requirement to
  "matched".
"""

from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Set, Tuple

from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz

from backend.config.settings import Settings, get_settings
from backend.core.matching import BaseKeywordMatcher
from backend.core.matching.skill_taxonomy import (
    CANONICAL_ALIASES,
    get_aliases,
    get_related_canonicals,
    normalize_surface,
    resolve_canonical,
)
from backend.models.document import JobDescription, Resume
from backend.models.enums import MatchType, RequirementType, SectionType
from backend.models.evidence import EvidenceChunk, MatchEvidence
from backend.models.requirement import Requirement
from backend.models.skill import Skill


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9#+\.]+", re.IGNORECASE)


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer, lowercased."""
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _contains_phrase(haystack: str, needle: str) -> bool:
    """Case-insensitive phrase containment check."""
    return needle.lower() in haystack.lower()


# ---------------------------------------------------------------------------
# KeywordMatcher
# ---------------------------------------------------------------------------


class KeywordMatcher(BaseKeywordMatcher):
    """Deterministic keyword matching engine with four-tier cascade and BM25."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

    # ------------------------------------------------------------------
    # Explicit skill matching  (required / preferred coverage)
    # ------------------------------------------------------------------

    def match_explicit_skills(
        self,
        resume_skills: List[Skill],
        jd_requirements: List[Requirement],
    ) -> Tuple[List[Skill], List[Requirement]]:
        """Four-tier cascade: exact → alias → phrase → fuzzy.

        Returns ``(matched_skills, missing_requirements)``.
        Each requirement is matched **at most once** (first tier wins).
        """
        matched_skills: List[Skill] = []
        missing_requirements: List[Requirement] = []

        # Set of canonical names already consumed from resume
        consumed_resume_canonicals: Set[str] = set()
        # Track requirement ids that have been matched
        matched_req_ids: Set[str] = set()

        # Pre-compute resume canonical names for fast lookup
        resume_canonical_set: Set[str] = set()
        resume_surface_set: Set[str] = set()
        resume_raw_text_tokens: Set[str] = set()

        for sk in resume_skills:
            canon = normalize_surface(sk.canonical_name)
            resume_canonical_set.add(canon)
            resume_surface_set.add(normalize_surface(sk.surface_form))
            # Also resolve the surface form to a canonical
            resolved = resolve_canonical(sk.surface_form)
            if resolved:
                resume_canonical_set.add(resolved)

        for req in jd_requirements:
            if req.type not in (RequirementType.REQUIRED, RequirementType.PREFERRED):
                continue
            if not getattr(req, "is_skill_matchable", True):
                continue

            req_canon = normalize_surface(req.canonical_name)
            match_skill = self._try_match_requirement(
                req, req_canon, resume_skills, resume_canonical_set,
                resume_surface_set, consumed_resume_canonicals,
            )

            if match_skill is not None:
                matched_skills.append(match_skill)
                matched_req_ids.add(req.id)
                consumed_resume_canonicals.add(match_skill.canonical_name)
            else:
                missing_requirements.append(req)

        return matched_skills, missing_requirements

    def _try_match_requirement(
        self,
        req: Requirement,
        req_canon: str,
        resume_skills: List[Skill],
        resume_canonical_set: Set[str],
        resume_surface_set: Set[str],
        consumed: Set[str],
    ) -> Optional[Skill]:
        """Try matching a single requirement through the four-tier cascade."""

        # --- Tier 1: Exact canonical match ---
        if req_canon in resume_canonical_set and req_canon not in consumed:
            surface = self._find_surface_for_canonical(req_canon, resume_skills)
            return Skill(
                canonical_name=req_canon,
                surface_form=surface or req_canon,
                match_type=MatchType.EXACT,
                confidence=1.0,
            )

        # --- Tier 2: Alias match ---
        req_aliases = get_aliases(req_canon)
        for alias in req_aliases:
            normed_alias = normalize_surface(alias)
            if normed_alias in resume_canonical_set and normed_alias not in consumed:
                surface = self._find_surface_for_canonical(normed_alias, resume_skills)
                return Skill(
                    canonical_name=req_canon,
                    surface_form=surface or alias,
                    match_type=MatchType.ALIAS,
                    confidence=0.95,
                )
            # Check if any resume skill's surface form matches the alias
            if normed_alias in resume_surface_set and normed_alias not in consumed:
                return Skill(
                    canonical_name=req_canon,
                    surface_form=alias,
                    match_type=MatchType.ALIAS,
                    confidence=0.95,
                )

        # Also check if resume has a skill whose canonical resolves to req_canon
        for sk in resume_skills:
            resolved = resolve_canonical(sk.surface_form)
            if resolved and normalize_surface(resolved) == req_canon:
                if normalize_surface(sk.canonical_name) not in consumed:
                    return Skill(
                        canonical_name=req_canon,
                        surface_form=sk.surface_form,
                        match_type=MatchType.ALIAS,
                        confidence=0.95,
                    )

        # --- Tier 3: Phrase containment ---
        for sk in resume_skills:
            sk_canon = normalize_surface(sk.canonical_name)
            if sk_canon in consumed:
                continue
            if _contains_phrase(sk.surface_form, req.name) or _contains_phrase(
                req.name, sk.surface_form
            ):
                return Skill(
                    canonical_name=req_canon,
                    surface_form=sk.surface_form,
                    match_type=MatchType.PHRASE,
                    confidence=0.85,
                )

        # --- Tier 4: Fuzzy match ---
        threshold = self._settings.FUZZY_MATCH_THRESHOLD
        best_score = 0.0
        best_skill: Optional[Skill] = None
        for sk in resume_skills:
            sk_canon = normalize_surface(sk.canonical_name)
            if sk_canon in consumed:
                continue
            score = fuzz.token_sort_ratio(req_canon, sk_canon)
            if score >= threshold and score > best_score:
                best_score = score
                best_skill = sk

        if best_skill is not None:
            return Skill(
                canonical_name=req_canon,
                surface_form=best_skill.surface_form,
                match_type=MatchType.FUZZY,
                confidence=round(best_score / 100.0, 3),
            )

        return None

    @staticmethod
    def _find_surface_for_canonical(
        canonical: str, resume_skills: List[Skill]
    ) -> Optional[str]:
        """Find the first resume skill whose canonical matches and return its surface form."""
        for sk in resume_skills:
            if normalize_surface(sk.canonical_name) == canonical:
                return sk.surface_form
        return None

    # ------------------------------------------------------------------
    # BM25 contextual lexical relevance  (independent of coverage)
    # ------------------------------------------------------------------

    def compute_lexical_evidence(
        self,
        resume: Resume,
        jd: JobDescription,
    ) -> List[MatchEvidence]:
        """Compute BM25-based lexical relevance between JD requirements and resume evidence.

        This is **independent** of the explicit matched/missing verdict.
        """
        if not resume.evidence_chunks or not jd.requirements:
            return []

        corpus_texts = [chunk.text for chunk in resume.evidence_chunks]
        tokenized_corpus = [_tokenize(t) for t in corpus_texts]

        if not tokenized_corpus or all(len(t) == 0 for t in tokenized_corpus):
            return []

        # Lucene BM25 calculation (guarantees non-negative IDF for any N >= 1)
        num_docs = len(tokenized_corpus)
        doc_lengths = [len(doc) for doc in tokenized_corpus]
        avg_doc_len = (sum(doc_lengths) / num_docs) if num_docs > 0 else 1.0
        if avg_doc_len == 0:
            avg_doc_len = 1.0

        # Term document frequencies
        doc_freqs: Dict[str, int] = {}
        doc_term_counts: List[Dict[str, int]] = []
        for doc in tokenized_corpus:
            counts: Dict[str, int] = {}
            for token in doc:
                counts[token] = counts.get(token, 0) + 1
            doc_term_counts.append(counts)
            for token in counts:
                doc_freqs[token] = doc_freqs.get(token, 0) + 1

        k1 = 1.5
        b = 0.75
        evidences: List[MatchEvidence] = []
        seen_pairs: Set[Tuple[str, str]] = set()

        for req in jd.requirements:
            query_text = req.source_text or req.name
            query_tokens = _tokenize(query_text)
            if not query_tokens:
                continue

            unique_query_tokens = list(dict.fromkeys(query_tokens))

            # Compute theoretical max score for normalization
            max_possible_score = 0.0
            idfs: Dict[str, float] = {}
            for qt in unique_query_tokens:
                n_qt = doc_freqs.get(qt, 0)
                # Lucene IDF: ln(1 + (N - n + 0.5) / (n + 0.5)) -> strictly >= 0
                idf = math.log(1.0 + (num_docs - n_qt + 0.5) / (n_qt + 0.5))
                idfs[qt] = idf
                max_possible_score += idf * (k1 + 1.0)

            if max_possible_score <= 0:
                continue

            # Score each evidence chunk
            chunk_scores: List[Tuple[int, float]] = []
            for doc_idx, counts in enumerate(doc_term_counts):
                d_len = doc_lengths[doc_idx]
                len_norm = 1.0 - b + b * (d_len / avg_doc_len)
                score = 0.0
                for qt in unique_query_tokens:
                    tf = counts.get(qt, 0)
                    if tf > 0:
                        tf_component = (tf * (k1 + 1.0)) / (tf + k1 * len_norm)
                        score += idfs[qt] * tf_component
                if score > 0:
                    norm_score = min(score / max_possible_score, 1.0)
                    chunk_scores.append((doc_idx, norm_score))

            if not chunk_scores:
                continue

            # Sort chunks by relevance descending and record evidence
            chunk_scores.sort(key=lambda x: x[1], reverse=True)
            for doc_idx, norm_score in chunk_scores:
                if norm_score < 0.05:
                    continue
                chunk = resume.evidence_chunks[doc_idx]
                pair_key = (req.id, chunk.id)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                evidences.append(
                    MatchEvidence(
                        requirement=req,
                        evidence=chunk,
                        match_type=MatchType.LEXICAL,
                        confidence=round(norm_score, 4),
                        similarity=None,
                    )
                )

        return evidences
