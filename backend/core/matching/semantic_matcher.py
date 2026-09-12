"""Concrete semantic matching engine using sentence-transformers.

Uses ``all-MiniLM-L6-v2`` to embed JD requirement texts and resume evidence
chunks, then computes cosine similarity to find the strongest evidence per
requirement.

Key invariants
--------------
* Semantic evidence **never** flips a "missing" explicit skill to "matched".
  It only contributes to the ``semantic_requirement_alignment`` score component.
* Embeddings are cached via ``functools.lru_cache`` to avoid recomputation
  within a batch.
* No LLM is used — only local sentence embeddings.
"""

from __future__ import annotations

import functools
from typing import Dict, List, Optional, Tuple

import numpy as np

from backend.config.settings import Settings, get_settings
from backend.core.matching import BaseSemanticMatcher
from backend.models.document import JobDescription, Resume
from backend.models.enums import MatchType
from backend.models.evidence import EvidenceChunk, MatchEvidence
from backend.models.requirement import Requirement


# ---------------------------------------------------------------------------
# Singleton model loader
# ---------------------------------------------------------------------------

_MODEL_CACHE: Dict[str, object] = {}


def _get_model(model_name: str):
    """Lazily load and cache the SentenceTransformer model."""
    if model_name not in _MODEL_CACHE:
        from sentence_transformers import SentenceTransformer

        _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
    return _MODEL_CACHE[model_name]


# ---------------------------------------------------------------------------
# Embedding cache  (text -> numpy vector)
# ---------------------------------------------------------------------------

# Module-level cache keyed on (model_name, text) so identical strings
# encountered across resumes are never re-encoded.
_EMBEDDING_CACHE: Dict[Tuple[str, str], np.ndarray] = {}

_MAX_CACHE_SIZE = 10_000  # safety cap


def _get_embedding(model, model_name: str, text: str) -> np.ndarray:
    """Return a cached embedding vector for *text*."""
    key = (model_name, text)
    if key not in _EMBEDDING_CACHE:
        if len(_EMBEDDING_CACHE) >= _MAX_CACHE_SIZE:
            # Simple eviction: clear half
            keys = list(_EMBEDDING_CACHE.keys())
            for k in keys[: len(keys) // 2]:
                del _EMBEDDING_CACHE[k]
        vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        _EMBEDDING_CACHE[key] = vec
    return _EMBEDDING_CACHE[key]


def clear_embedding_cache() -> None:
    """Explicitly clear the embedding cache between evaluation batches."""
    _EMBEDDING_CACHE.clear()


# ---------------------------------------------------------------------------
# SemanticMatcher
# ---------------------------------------------------------------------------


class SemanticMatcher(BaseSemanticMatcher):
    """Local sentence-transformer semantic alignment engine."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._model_name = self._settings.EMBEDDING_MODEL

    def _model(self):
        return _get_model(self._model_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_semantic_alignment(
        self,
        resume: Resume,
        jd: JobDescription,
    ) -> List[MatchEvidence]:
        """Embed JD requirements and resume evidence, return top matches."""

        requirements = jd.requirements
        evidence_chunks = resume.evidence_chunks

        if not requirements or not evidence_chunks:
            return []

        model = self._model()

        # Embed all requirement source texts
        req_texts = [r.source_text or r.name for r in requirements]
        req_embeddings = np.array(
            [_get_embedding(model, self._model_name, t) for t in req_texts]
        )

        # Embed all evidence chunk texts
        ev_texts = [c.text for c in evidence_chunks]
        ev_embeddings = np.array(
            [_get_embedding(model, self._model_name, t) for t in ev_texts]
        )

        # Cosine similarity matrix  (requirements × evidence)
        # Embeddings are already L2-normalised so dot product == cosine sim.
        sim_matrix = req_embeddings @ ev_embeddings.T  # shape (R, E)

        # Thresholds
        exact_thresh = self._settings.SEMANTIC_EXACT_THRESHOLD
        related_thresh = self._settings.SEMANTIC_SIMILARITY_THRESHOLD
        inferred_thresh = self._settings.SEMANTIC_INFERRED_THRESHOLD

        results: List[MatchEvidence] = []

        for req_idx, req in enumerate(requirements):
            sims = sim_matrix[req_idx]
            # Find the strongest evidence for this requirement
            best_ev_idx = int(np.argmax(sims))
            raw_sim = float(sims[best_ev_idx])

            if raw_sim < inferred_thresh:
                continue  # below minimum threshold

            best_sim = max(0.0, min(1.0, raw_sim))

            # Classify match tier
            if best_sim >= exact_thresh:
                match_type = MatchType.SEMANTIC_EXACT
            elif best_sim >= related_thresh:
                match_type = MatchType.SEMANTIC_RELATED
            else:
                match_type = MatchType.SEMANTIC_INFERRED

            results.append(
                MatchEvidence(
                    requirement=req,
                    evidence=evidence_chunks[best_ev_idx],
                    match_type=match_type,
                    confidence=round(best_sim, 4),
                    similarity=round(best_sim, 4),
                )
            )

        return results
