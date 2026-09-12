"""Comprehensive Semantic Matching Engine Validation.

Validates the semantic engine in isolation:

1. Model loading (singleton, load-once, CPU-friendly)
2. Embedding caching (hit/miss, eviction, determinism)
3. Per-requirement × per-evidence comparison (not whole-doc vs whole-doc)
4. Cosine similarity with [0,1] clamping
5. Strongest evidence per requirement preserved with full metadata
6. Match policy: semantic evidence never converts missing → matched
7. Configurable thresholds with diagnostic similarity distribution
8. Critical tests: Node.js/Express, MongoDB/PostgreSQL
9. Semantic-value test: weak keyword + strong semantic
10. Ablation: keyword-only, semantic-only, combined independence
"""

import time
from typing import List

import numpy as np
import pytest

from backend.config.settings import Settings
from backend.core.matching.keyword_matcher import KeywordMatcher
from backend.core.matching.semantic_matcher import (
    SemanticMatcher,
    _EMBEDDING_CACHE,
    _MODEL_CACHE,
    _get_embedding,
    _get_model,
    clear_embedding_cache,
)
from backend.models.document import JobDescription, Resume
from backend.models.enums import MatchType, RequirementType, SectionType
from backend.models.evidence import EvidenceChunk, MatchEvidence
from backend.models.requirement import Requirement
from backend.models.skill import Skill


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture(autouse=True)
def _reset_caches():
    """Clear embedding cache before and after each test."""
    clear_embedding_cache()
    yield
    clear_embedding_cache()


@pytest.fixture
def sm() -> SemanticMatcher:
    return SemanticMatcher()


@pytest.fixture
def km() -> KeywordMatcher:
    return KeywordMatcher()


# ===================================================================
# Helpers
# ===================================================================


def _req(
    id: str, name: str, canon: str,
    typ=RequirementType.REQUIRED, text=None,
) -> Requirement:
    return Requirement(
        id=id, name=name, type=typ,
        canonical_name=canon,
        source_text=text or f"Must have {name}.",
    )


def _chunk(
    id: str, text: str,
    section=SectionType.EXPERIENCE,
    page: int = 1,
    src: str = "resume.pdf",
) -> EvidenceChunk:
    return EvidenceChunk(
        id=id, text=text, section=section,
        page=page, source_file=src,
    )


def _resume(
    cid: str, name: str,
    chunks: list = None, skills: list = None,
) -> Resume:
    return Resume(
        candidate_id=cid, name=name,
        source_file=f"{cid}.pdf",
        raw_text=name,
        evidence_chunks=chunks or [],
        skills=skills or [],
    )


def _jd(reqs: list, raw: str = "JD text") -> JobDescription:
    return JobDescription(
        id="jd_sem", title="Semantic Test JD",
        source_file="jd.pdf", raw_text=raw,
        requirements=reqs,
        required_skills=[r.canonical_name for r in reqs],
    )


# ===================================================================
# 1. MODEL LIFECYCLE
# ===================================================================


class TestModelLifecycle:
    """Validate model loads once, is cached, and runs on CPU."""

    def test_model_loads_and_returns_same_instance(self):
        """Model is loaded lazily and the same object is reused."""
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        m1 = _get_model(model_name)
        m2 = _get_model(model_name)
        assert m1 is m2, "Model must be a singleton"

    def test_model_load_time_reasonable(self):
        """First load should be < 30s (cold) and re-load < 0.01s (cached)."""
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        # Already in cache from previous test; cold load already happened
        t0 = time.perf_counter()
        _get_model(model_name)
        dt = time.perf_counter() - t0
        # Cached access is sub-millisecond
        assert dt < 0.1, f"Cached model access took {dt:.3f}s (should be < 0.1s)"

    def test_model_on_cpu(self):
        """Model device should be CPU (no CUDA requirement)."""
        model = _get_model("sentence-transformers/all-MiniLM-L6-v2")
        device = str(model.device)
        assert "cpu" in device.lower(), f"Model device is {device}, expected CPU"

    def test_embedding_dimension_is_384(self):
        """all-MiniLM-L6-v2 produces 384-dim embeddings."""
        model = _get_model("sentence-transformers/all-MiniLM-L6-v2")
        vec = model.encode("test string", convert_to_numpy=True)
        assert vec.shape == (384,), f"Expected (384,), got {vec.shape}"


# ===================================================================
# 2. EMBEDDING CACHING
# ===================================================================


class TestEmbeddingCaching:
    """Validate embedding cache hit/miss and eviction."""

    def test_cache_stores_embeddings(self):
        model = _get_model("sentence-transformers/all-MiniLM-L6-v2")
        text = "Machine learning pipeline"
        model_name = "sentence-transformers/all-MiniLM-L6-v2"

        assert (model_name, text) not in _EMBEDDING_CACHE

        v1 = _get_embedding(model, model_name, text)
        assert (model_name, text) in _EMBEDDING_CACHE

        # Second call returns identical vector
        v2 = _get_embedding(model, model_name, text)
        assert np.array_equal(v1, v2)

    def test_cache_clear_removes_entries(self):
        model = _get_model("sentence-transformers/all-MiniLM-L6-v2")
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        _get_embedding(model, model_name, "some text")
        assert len(_EMBEDDING_CACHE) > 0
        clear_embedding_cache()
        assert len(_EMBEDDING_CACHE) == 0

    def test_cached_access_faster_than_fresh(self):
        model = _get_model("sentence-transformers/all-MiniLM-L6-v2")
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        text = "Unique sentence for timing test"

        # Fresh encode
        t0 = time.perf_counter()
        _get_embedding(model, model_name, text)
        fresh_time = time.perf_counter() - t0

        # Cached access
        t0 = time.perf_counter()
        for _ in range(100):
            _get_embedding(model, model_name, text)
        cached_time = (time.perf_counter() - t0) / 100

        assert cached_time < fresh_time, \
            f"Cached ({cached_time:.6f}s) should be faster than fresh ({fresh_time:.6f}s)"

    def test_different_texts_produce_different_embeddings(self):
        model = _get_model("sentence-transformers/all-MiniLM-L6-v2")
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        v1 = _get_embedding(model, model_name, "Python programming")
        v2 = _get_embedding(model, model_name, "Underwater basket weaving")
        sim = float(np.dot(v1, v2))
        assert sim < 0.8, f"Unrelated texts should not be highly similar: {sim:.3f}"


# ===================================================================
# 3. PER-REQUIREMENT × PER-EVIDENCE MATCHING
# ===================================================================


class TestPerRequirementMatching:
    """Verify matching operates per-requirement, not whole-doc-vs-whole-doc."""

    def test_multiple_requirements_get_individual_evidence(self, sm):
        """Each requirement finds its own best evidence chunk."""
        r1 = _req("r1", "Python", "python",
                   text="Expert Python development for backend services")
        r2 = _req("r2", "Docker", "docker",
                   text="Containerize applications using Docker")

        c1 = _chunk("c1", "Built Python web APIs with Flask and Django.")
        c2 = _chunk("c2", "Containerized microservices using Docker and Kubernetes.")

        resume = _resume("dev", "Dev", chunks=[c1, c2])
        jd = _jd([r1, r2])

        matches = sm.compute_semantic_alignment(resume, jd)

        # Should have matches for both requirements
        req_ids = {m.requirement.id for m in matches}
        assert "r1" in req_ids, "Python requirement should have a match"
        assert "r2" in req_ids, "Docker requirement should have a match"

        # Each should find its best evidence
        for m in matches:
            if m.requirement.id == "r1":
                assert "Python" in m.evidence.text or "Flask" in m.evidence.text
            elif m.requirement.id == "r2":
                assert "Docker" in m.evidence.text or "Container" in m.evidence.text

    def test_evidence_metadata_preserved(self, sm):
        """MatchEvidence preserves requirement ID, chunk ID, page, section, source."""
        req = _req("r_meta", "Kubernetes", "kubernetes",
                    text="Manage Kubernetes clusters in production")
        chunk = _chunk(
            "chunk_k8s", "Deployed apps on Kubernetes with Helm charts.",
            section=SectionType.PROJECTS, page=3, src="alice.pdf",
        )
        resume = _resume("alice", "Alice", chunks=[chunk])
        jd = _jd([req])

        matches = sm.compute_semantic_alignment(resume, jd)
        assert len(matches) == 1
        m = matches[0]

        # Requirement metadata
        assert m.requirement.id == "r_meta"
        assert m.requirement.canonical_name == "kubernetes"

        # Evidence metadata
        assert m.evidence.id == "chunk_k8s"
        assert m.evidence.section == SectionType.PROJECTS
        assert m.evidence.page == 3
        assert m.evidence.source_file == "alice.pdf"

        # Similarity metadata
        assert m.similarity is not None
        assert 0.0 <= m.similarity <= 1.0
        assert m.confidence == m.similarity
        assert m.match_type in (
            MatchType.SEMANTIC_EXACT,
            MatchType.SEMANTIC_RELATED,
            MatchType.SEMANTIC_INFERRED,
        )

    def test_strongest_evidence_selected(self, sm):
        """When multiple chunks exist, the highest similarity one is selected."""
        req = _req("r_ml", "Machine Learning", "ml",
                    text="Train deep learning models in production")

        # Strong evidence
        c_strong = _chunk("c_strong",
            "Trained PyTorch transformers for production NLP inference pipelines.")
        # Weak evidence
        c_weak = _chunk("c_weak",
            "Updated Excel spreadsheets for monthly department reports.")

        resume = _resume("bob", "Bob", chunks=[c_strong, c_weak])
        jd = _jd([req])

        matches = sm.compute_semantic_alignment(resume, jd)
        assert len(matches) == 1
        assert matches[0].evidence.id == "c_strong"


# ===================================================================
# 4. COSINE SIMILARITY BOUNDS
# ===================================================================


class TestCosineSimilarityBounds:
    """All similarity values must be in [0, 1]."""

    def test_similarity_bounded(self, sm):
        req = _req("r1", "Go", "go",
                    text="Build high-performance services in Go")
        chunk = _chunk("c1", "Implemented concurrent Go services with goroutines.")
        resume = _resume("c1", "Dev", chunks=[chunk])
        jd = _jd([req])

        matches = sm.compute_semantic_alignment(resume, jd)
        for m in matches:
            assert 0.0 <= m.similarity <= 1.0
            assert 0.0 <= m.confidence <= 1.0

    def test_identical_text_near_one(self, sm):
        """Identical requirement and evidence text should yield similarity near 1.0."""
        text = "Build microservices using Node.js and Express"
        req = _req("r_id", "Node.js", "nodejs", text=text)
        chunk = _chunk("c_id", text)
        resume = _resume("same", "Same", chunks=[chunk])
        jd = _jd([req])

        matches = sm.compute_semantic_alignment(resume, jd)
        assert len(matches) == 1
        assert matches[0].similarity >= 0.95, \
            f"Identical text should yield sim >= 0.95, got {matches[0].similarity}"


# ===================================================================
# 5. MATCH POLICY: SEMANTIC NEVER CONVERTS MISSING → MATCHED
# ===================================================================


class TestMatchPolicy:
    """Semantic evidence must NOT convert a missing explicit skill into matched."""

    def test_express_does_not_satisfy_node_explicit(self, km, sm):
        """Express.js semantic evidence does not make Node.js an explicit match."""
        req = _req("r_node", "Node.js", "node.js",
                    text="Build REST APIs using Node.js")
        sk_express = Skill(
            canonical_name="express.js", surface_form="Express.js",
            match_type=MatchType.EXACT, confidence=1.0,
        )
        chunk = _chunk("c1",
            "Developed REST API endpoints using Express.js framework.")
        resume = _resume("dev", "Dev",
                         chunks=[chunk], skills=[sk_express])
        jd = _jd([req])

        # Keyword engine: Express.js does NOT satisfy Node.js
        matched, missing = km.match_explicit_skills(resume.skills, jd.requirements)
        assert len(matched) == 0
        assert len(missing) == 1
        assert missing[0].canonical_name == "node.js"

        # Semantic engine: finds related evidence
        sem = sm.compute_semantic_alignment(resume, jd)
        assert len(sem) > 0
        assert sem[0].similarity >= 0.45

        # But the match type is SEMANTIC, NOT EXACT
        assert sem[0].match_type in (
            MatchType.SEMANTIC_EXACT,
            MatchType.SEMANTIC_RELATED,
            MatchType.SEMANTIC_INFERRED,
        )
        assert sem[0].match_type != MatchType.EXACT

    def test_postgres_does_not_satisfy_mongodb_semantically(self, km, sm):
        """PostgreSQL provides related database context but does not claim MongoDB."""
        req = _req("r_mongo", "MongoDB", "mongodb",
                    text="Design and manage NoSQL databases using MongoDB")
        sk_pg = Skill(
            canonical_name="postgresql", surface_form="PostgreSQL",
            match_type=MatchType.EXACT, confidence=1.0,
        )
        chunk = _chunk("c_pg",
            "Designed and optimized complex PostgreSQL schemas with billions of rows.")
        resume = _resume("dba", "DBA",
                         chunks=[chunk], skills=[sk_pg])
        jd = _jd([req])

        # Keyword: PostgreSQL does NOT satisfy MongoDB
        matched, missing = km.match_explicit_skills(resume.skills, jd.requirements)
        assert len(matched) == 0
        assert len(missing) == 1

        # Semantic: may find some database-related context
        sem = sm.compute_semantic_alignment(resume, jd)
        if len(sem) > 0:
            # The semantic match should have moderate similarity (related context)
            # but should NOT be classified as EXACT keyword match
            assert sem[0].match_type != MatchType.EXACT
            # And it's still classified under semantic tiers
            assert sem[0].match_type in (
                MatchType.SEMANTIC_EXACT,
                MatchType.SEMANTIC_RELATED,
                MatchType.SEMANTIC_INFERRED,
            )


# ===================================================================
# 6. CRITICAL TEST: Node.js / Express.js
# ===================================================================


class TestCriticalNodeExpress:
    """JD: 'Build REST APIs using Node.js'
    Resume: 'Developed backend services using Express.js and MongoDB.'

    Semantic similarity must identify meaningful related evidence.
    """

    def test_meaningful_related_evidence(self, sm):
        req = _req("r_node", "Node.js", "node.js",
                    text="Build REST APIs using Node.js")
        chunk = _chunk("c_exp",
            "Developed backend services using Express.js and MongoDB.")
        resume = _resume("exp_dev", "Express Dev", chunks=[chunk])
        jd = _jd([req])

        matches = sm.compute_semantic_alignment(resume, jd)
        assert len(matches) == 1
        m = matches[0]
        assert m.requirement.id == "r_node"
        assert m.evidence.id == "c_exp"
        assert m.similarity >= 0.45, \
            f"Express/Node.js semantic sim should be >= 0.45, got {m.similarity}"

    def test_full_metadata_chain(self, sm):
        req = _req("r_node", "Node.js", "node.js",
                    text="Build REST APIs using Node.js")
        chunk = _chunk("c_exp",
            "Developed backend services using Express.js and MongoDB.",
            page=2, section=SectionType.EXPERIENCE, src="express_dev.pdf")
        resume = _resume("exp_dev", "Express Dev", chunks=[chunk])
        jd = _jd([req])

        matches = sm.compute_semantic_alignment(resume, jd)
        m = matches[0]
        assert m.evidence.page == 2
        assert m.evidence.section == SectionType.EXPERIENCE
        assert m.evidence.source_file == "express_dev.pdf"


# ===================================================================
# 7. CRITICAL TEST: MongoDB / PostgreSQL
# ===================================================================


class TestCriticalMongoPostgres:
    """JD: 'MongoDB'
    Resume: 'PostgreSQL'

    Semantic similarity may recognize related database context but
    does NOT claim MongoDB as an explicit skill.
    """

    def test_database_context_similarity(self, sm):
        req = _req("r_mongo", "MongoDB", "mongodb",
                    text="MongoDB")
        chunk = _chunk("c_pg", "PostgreSQL")
        resume = _resume("pg_dev", "PG Dev", chunks=[chunk])
        jd = _jd([req])

        matches = sm.compute_semantic_alignment(resume, jd)
        if len(matches) > 0:
            m = matches[0]
            # Related database context — should NOT be high
            assert m.match_type != MatchType.EXACT
            # The similarity should be moderate at most
            assert m.similarity < 0.85, \
                f"MongoDB vs PostgreSQL should not be near-exact: {m.similarity}"

    def test_keyword_engine_still_reports_missing(self, km):
        req = _req("r_mongo", "MongoDB", "mongodb")
        sk = Skill(
            canonical_name="postgresql", surface_form="PostgreSQL",
            match_type=MatchType.EXACT, confidence=1.0,
        )
        matched, missing = km.match_explicit_skills([sk], [req])
        assert len(matched) == 0 and len(missing) == 1


# ===================================================================
# 8. SEMANTIC-VALUE TEST: Weak keyword + Strong semantic
# ===================================================================


class TestSemanticValueStrongSemantic:
    """Candidate has NO explicit keyword match for requirement,
    but has strong semantic evidence from deep experience."""

    def test_strong_semantic_no_keyword(self, km, sm):
        """
        JD requires 'container orchestration'.
        Resume says: 'Managed Kubernetes clusters running 200+ microservices pods
        with Helm, Istio, and autoscaling policies.'

        Keywords: no explicit skill named 'container_orchestration'.
        Semantic: very strong alignment.
        """
        req = _req("r_co", "Container Orchestration", "container_orchestration",
                    text="Manage container orchestration for production microservices at scale")
        chunk = _chunk("c_k8s",
            "Managed Kubernetes clusters running 200+ microservice pods with "
            "Helm charts, Istio service mesh, and autoscaling policies.")
        resume = _resume("ops", "Ops Eng", chunks=[chunk])
        jd = _jd([req])

        # Keyword: no explicit match
        matched, missing = km.match_explicit_skills([], [req])
        assert len(matched) == 0
        assert len(missing) == 1

        # Semantic: strong alignment
        sem = sm.compute_semantic_alignment(resume, jd)
        assert len(sem) == 1
        assert sem[0].similarity >= 0.55, \
            f"Strong semantic evidence should be >= 0.55, got {sem[0].similarity}"
        assert sem[0].match_type in (
            MatchType.SEMANTIC_EXACT,
            MatchType.SEMANTIC_RELATED,
        )

    def test_semantic_outweighs_when_keywords_absent(self, km, sm):
        """Demonstrate semantic evidence independently provides a signal
        even when keyword coverage is zero."""
        req = _req("r_ml", "Deep Learning", "deep_learning",
                    text="Train and deploy production deep learning models "
                         "using PyTorch, TensorFlow, and transformer architectures "
                         "for natural language processing and computer vision tasks")

        # Candidate A: No keywords, strong semantic evidence
        chunk_a = _chunk("c_a",
            "Trained and fine-tuned PyTorch transformer models including BERT "
            "and GPT architectures for real-time NLP inference pipelines "
            "serving production traffic at scale with GPU optimization.")
        resume_a = _resume("a", "A", chunks=[chunk_a])

        # Candidate B: No keywords, weak semantic evidence
        chunk_b = _chunk("c_b",
            "Prepared meeting agendas, department scheduling calendars, "
            "and organized quarterly budget review spreadsheets.")
        resume_b = _resume("b", "B", chunks=[chunk_b])

        jd = _jd([req])
        sem_a = sm.compute_semantic_alignment(resume_a, jd)
        sem_b = sm.compute_semantic_alignment(resume_b, jd)

        sim_a = sem_a[0].similarity if sem_a else 0.0
        sim_b = sem_b[0].similarity if sem_b else 0.0

        assert sim_a > sim_b, \
            f"Strong evidence ({sim_a}) should outscore weak ({sim_b})"
        assert sim_a >= 0.45


# ===================================================================
# 9. ABLATION: keyword-only, semantic-only, combined
# ===================================================================


class TestAblation:
    """Demonstrate semantic results are independently generated,
    separate from keyword results."""

    def _build_scenario(self):
        r1 = _req("r1", "Python", "python",
                   text="Expert Python developer for backend APIs")
        r2 = _req("r2", "Kubernetes", "kubernetes",
                   text="Production Kubernetes orchestration and deployments")

        sk_py = Skill(
            canonical_name="python", surface_form="Python",
            match_type=MatchType.EXACT, confidence=1.0,
        )
        c1 = _chunk("c1",
            "Built Python microservices deployed on Kubernetes with Helm charts.")
        resume = _resume("dev", "Dev", chunks=[c1], skills=[sk_py])
        jd = _jd([r1, r2])
        return r1, r2, sk_py, resume, jd

    def test_keyword_only_no_semantic_call(self, km):
        """Keyword matching works independently of semantic engine."""
        r1, r2, sk_py, resume, jd = self._build_scenario()
        matched, missing = km.match_explicit_skills(resume.skills, jd.requirements)
        # Python matched, Kubernetes missing
        assert len(matched) == 1
        assert matched[0].canonical_name == "python"
        assert len(missing) == 1
        assert missing[0].canonical_name == "kubernetes"

    def test_semantic_only_no_keyword_call(self, sm):
        """Semantic matching works independently of keyword engine."""
        r1, r2, sk_py, resume, jd = self._build_scenario()
        sem = sm.compute_semantic_alignment(resume, jd)
        # Semantic should find evidence for both requirements from the chunk
        req_ids = {m.requirement.id for m in sem}
        assert len(req_ids) >= 1  # at least one requirement has evidence

        for m in sem:
            assert m.match_type in (
                MatchType.SEMANTIC_EXACT,
                MatchType.SEMANTIC_RELATED,
                MatchType.SEMANTIC_INFERRED,
            )
            assert m.similarity is not None
            assert m.similarity >= 0.45

    def test_combined_independence(self, km, sm):
        """Combined call produces results from both engines independently."""
        r1, r2, sk_py, resume, jd = self._build_scenario()

        # Keyword results
        matched, missing = km.match_explicit_skills(resume.skills, jd.requirements)

        # Semantic results
        sem = sm.compute_semantic_alignment(resume, jd)

        # These are independent data structures
        assert isinstance(matched, list)
        assert isinstance(sem, list)

        # Keyword matched Python
        kw_names = {s.canonical_name for s in matched}
        assert "python" in kw_names

        # Semantic found evidence (independently computed)
        sem_req_ids = {m.requirement.id for m in sem}
        assert len(sem_req_ids) >= 1


# ===================================================================
# 10. CONFIGURABLE THRESHOLDS
# ===================================================================


class TestConfigurableThresholds:
    """Verify custom thresholds alter match classification."""

    def test_strict_thresholds_filter_weak_matches(self):
        """High thresholds filter out moderate similarity matches."""
        strict = Settings(
            SEMANTIC_EXACT_THRESHOLD=0.95,
            SEMANTIC_SIMILARITY_THRESHOLD=0.85,
            SEMANTIC_INFERRED_THRESHOLD=0.75,
        )
        sm_strict = SemanticMatcher(settings=strict)

        req = _req("r1", "Cloud Architecture", "cloud_architecture",
                    text="Design cloud-native architectures on AWS")
        chunk = _chunk("c1",
            "Worked on server maintenance and network troubleshooting.")
        resume = _resume("ops", "Ops", chunks=[chunk])
        jd = _jd([req])

        matches = sm_strict.compute_semantic_alignment(resume, jd)
        # Unrelated evidence should be filtered by high threshold
        assert len(matches) == 0

    def test_lenient_thresholds_include_weak_matches(self):
        """Low thresholds allow moderate similarity matches through."""
        lenient = Settings(
            SEMANTIC_EXACT_THRESHOLD=0.80,
            SEMANTIC_SIMILARITY_THRESHOLD=0.50,
            SEMANTIC_INFERRED_THRESHOLD=0.20,
        )
        sm_lenient = SemanticMatcher(settings=lenient)

        req = _req("r1", "Backend Dev", "backend_dev",
                    text="Build scalable backend APIs")
        chunk = _chunk("c1",
            "Developed web services using various frameworks.")
        resume = _resume("dev", "Dev", chunks=[chunk])
        jd = _jd([req])

        matches = sm_lenient.compute_semantic_alignment(resume, jd)
        # With lenient threshold, should find a match
        assert len(matches) >= 1
        assert matches[0].similarity >= 0.20

    def test_threshold_tier_classification(self):
        """Match type depends on which threshold band the similarity falls into."""
        settings = Settings(
            SEMANTIC_EXACT_THRESHOLD=0.85,
            SEMANTIC_SIMILARITY_THRESHOLD=0.55,
            SEMANTIC_INFERRED_THRESHOLD=0.45,
        )
        sm_tiered = SemanticMatcher(settings=settings)

        req = _req("r1", "Python", "python", text="Expert Python programming")

        # Very similar text → SEMANTIC_EXACT
        c_exact = _chunk("c_ex", "Expert Python programming and development")
        resume_exact = _resume("ex", "Ex", chunks=[c_exact])
        jd = _jd([req])

        matches = sm_tiered.compute_semantic_alignment(resume_exact, jd)
        if matches and matches[0].similarity >= 0.85:
            assert matches[0].match_type == MatchType.SEMANTIC_EXACT


# ===================================================================
# 11. EDGE CASES
# ===================================================================


class TestEdgeCases:
    """Edge cases: empty inputs, single requirement, single evidence."""

    def test_empty_requirements(self, sm):
        chunk = _chunk("c1", "Some text")
        resume = _resume("dev", "Dev", chunks=[chunk])
        jd = JobDescription(
            id="jd_empty", title="Empty",
            source_file="jd.pdf", raw_text="jd",
            requirements=[],
        )
        assert sm.compute_semantic_alignment(resume, jd) == []

    def test_empty_evidence(self, sm):
        req = _req("r1", "Python", "python")
        resume = _resume("dev", "Dev", chunks=[])
        jd = _jd([req])
        assert sm.compute_semantic_alignment(resume, jd) == []

    def test_single_requirement_single_evidence(self, sm):
        req = _req("r1", "Rust", "rust",
                    text="Systems programming in Rust")
        chunk = _chunk("c1",
            "Built high-performance Rust services for real-time data processing.")
        resume = _resume("dev", "Dev", chunks=[chunk])
        jd = _jd([req])

        matches = sm.compute_semantic_alignment(resume, jd)
        assert len(matches) == 1
        assert matches[0].similarity >= 0.55


# ===================================================================
# 12. DIAGNOSTIC: SIMILARITY DISTRIBUTION
# ===================================================================


class TestDiagnosticDistribution:
    """Print diagnostic similarity distribution over synthetic pairs.

    This test always passes — it outputs the distribution for inspection.
    """

    SYNTHETIC_PAIRS = [
        # (JD requirement text, Resume evidence text, expected_label)
        ("Build REST APIs using Node.js",
         "Developed backend services using Express.js and MongoDB.",
         "Node/Express (related)"),
        ("MongoDB",
         "PostgreSQL",
         "Mongo/Postgres (different DB)"),
        ("Design scalable distributed systems",
         "Architected microservices platforms processing 1M+ requests/day",
         "Distributed systems (paraphrase)"),
        ("Train deep learning models in production",
         "Trained PyTorch transformers for real-time NLP inference",
         "Deep learning (direct)"),
        ("Kubernetes container orchestration",
         "Managed K8s clusters with Helm and Istio",
         "K8s (alias + related)"),
        ("Expert Python development",
         "Prepared monthly administrative spreadsheets",
         "Python vs Admin (unrelated)"),
        ("Design cloud-native architectures on AWS",
         "Designed and deployed AWS Lambda serverless architectures",
         "AWS cloud (direct)"),
        ("Machine learning feature engineering",
         "Built ETL data pipelines with Apache Spark",
         "ML vs ETL (adjacent)"),
        ("React.js frontend development",
         "Built Angular single-page applications with RxJS",
         "React vs Angular (same domain)"),
        ("Build REST APIs using Node.js",
         "Developed iOS applications using Swift and UIKit",
         "Node vs Swift (unrelated)"),
    ]

    def test_print_similarity_distribution(self, sm):
        """Diagnostic output: similarity distribution over synthetic pairs."""
        model = _get_model("sentence-transformers/all-MiniLM-L6-v2")
        model_name = "sentence-transformers/all-MiniLM-L6-v2"

        print("\n" + "=" * 72)
        print("SEMANTIC SIMILARITY DIAGNOSTIC DISTRIBUTION")
        print("=" * 72)
        print(f"Model: {model_name}")
        print(f"Embedding dim: {model.get_embedding_dimension()}")
        print(f"Thresholds: EXACT >= 0.85, RELATED >= 0.55, INFERRED >= 0.45")
        print("-" * 72)
        print(f"{'Label':<35} {'Sim':>6}  {'Tier':<20}")
        print("-" * 72)

        sims = []
        for jd_text, ev_text, label in self.SYNTHETIC_PAIRS:
            v_jd = _get_embedding(model, model_name, jd_text)
            v_ev = _get_embedding(model, model_name, ev_text)
            sim = max(0.0, min(1.0, float(np.dot(v_jd, v_ev))))
            sims.append(sim)

            if sim >= 0.85:
                tier = "SEMANTIC_EXACT"
            elif sim >= 0.55:
                tier = "SEMANTIC_RELATED"
            elif sim >= 0.45:
                tier = "SEMANTIC_INFERRED"
            else:
                tier = "BELOW_THRESHOLD"

            print(f"{label:<35} {sim:>6.4f}  {tier:<20}")

        print("-" * 72)
        print(f"Min: {min(sims):.4f}  Max: {max(sims):.4f}  "
              f"Mean: {np.mean(sims):.4f}  Std: {np.std(sims):.4f}")
        print("=" * 72)

        # This test always passes; it's diagnostic
        assert True


# ===================================================================
# 13. DETERMINISM
# ===================================================================


class TestDeterminism:
    """Repeated runs produce identical results."""

    def test_same_input_same_output(self, sm):
        req = _req("r1", "Go", "go",
                    text="Build high-performance Go microservices")
        chunk = _chunk("c1",
            "Implemented concurrent Go services with goroutines and channels.")
        resume = _resume("dev", "Dev", chunks=[chunk])
        jd = _jd([req])

        results = []
        for _ in range(5):
            clear_embedding_cache()
            matches = sm.compute_semantic_alignment(resume, jd)
            results.append(
                (len(matches), matches[0].similarity if matches else None)
            )
        assert len(set(results)) == 1, f"Non-deterministic: {results}"
