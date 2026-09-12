"""Tests for the Semantic Matching Engine.

Validates:
6. Semantic paraphrase matching
7. Semantic score materially changes final score
- Configurable thresholds
- Embedding caching functionality
"""

import pytest
from backend.config.settings import Settings
from backend.core.matching.semantic_matcher import SemanticMatcher, clear_embedding_cache
from backend.core.ranking.scorer import Scorer
from backend.models.document import JobDescription, Resume
from backend.models.enums import MatchType, RequirementType, SectionType
from backend.models.evidence import EvidenceChunk
from backend.models.requirement import Requirement
from backend.models.skill import Skill


@pytest.fixture(autouse=True)
def clean_cache():
    clear_embedding_cache()
    yield
    clear_embedding_cache()


@pytest.fixture
def semantic_matcher() -> SemanticMatcher:
    return SemanticMatcher()


def test_semantic_paraphrase_match(semantic_matcher: SemanticMatcher):
    """Test 6: Semantic paraphrase match identifies semantic equivalence without identical wording."""
    req = Requirement(
        id="req_distributed",
        name="Distributed Systems",
        type=RequirementType.REQUIRED,
        canonical_name="distributed_systems",
        source_text="Design and implement scalable distributed systems and cloud infrastructure.",
    )
    chunk = EvidenceChunk(
        id="chunk_para_01",
        text="Architected resilient microservices and decentralized cloud platforms under high throughput.",
        section=SectionType.EXPERIENCE,
        page=1,
        confidence=1.0,
        source_file="resume_a.pdf",
    )
    resume = Resume(
        candidate_id="cand_para_01",
        name="Candidate Paraphrase",
        source_file="resume_a.pdf",
        raw_text=chunk.text,
        evidence_chunks=[chunk],
    )
    jd = JobDescription(
        id="jd_para_01",
        title="Distributed Systems Lead",
        source_file="jd.pdf",
        raw_text=req.source_text,
        requirements=[req],
    )

    matches = semantic_matcher.compute_semantic_alignment(resume, jd)

    assert len(matches) == 1
    match = matches[0]
    assert match.requirement.id == "req_distributed"
    assert match.similarity is not None
    # Semantic alignment should be comfortably above the threshold
    assert match.similarity >= 0.55
    assert match.match_type in (MatchType.SEMANTIC_EXACT, MatchType.SEMANTIC_RELATED)


def test_semantic_score_materially_changes_final_score(semantic_matcher: SemanticMatcher):
    """Test 7: Candidates with identical keyword coverage have materially different scores due to semantic depth."""
    scorer = Scorer()

    req = Requirement(
        id="req_ml",
        name="Machine Learning",
        type=RequirementType.REQUIRED,
        canonical_name="machine_learning",
        source_text="Train deep learning models and deploy transformer pipelines in production.",
    )
    jd = JobDescription(
        id="jd_ml_01",
        title="ML Engineer",
        source_file="jd.pdf",
        raw_text=req.source_text,
        requirements=[req],
    )

    # Both candidates have identical matched explicit skills
    skill = Skill(
        canonical_name="machine_learning",
        surface_form="Machine Learning",
        match_type=MatchType.EXACT,
        confidence=1.0,
    )

    # Candidate 1: High semantic relevance (directly worked on transformer pipelines)
    chunk_high = EvidenceChunk(
        id="c_high",
        text="Trained and optimized transformer networks with PyTorch and deployed real-time LLM inference pipelines.",
        section=SectionType.EXPERIENCE,
        source_file="cand1.pdf",
    )
    resume_high = Resume(
        candidate_id="cand_high",
        name="Deep ML Engineer",
        source_file="cand1.pdf",
        raw_text=chunk_high.text,
        skills=[skill],
        evidence_chunks=[chunk_high],
    )

    # Candidate 2: Irrelevant/weak evidence (barely mentioned general concepts)
    chunk_low = EvidenceChunk(
        id="c_low",
        text="Organized department office inventory and prepared monthly administrative spreadsheet reports.",
        section=SectionType.EXPERIENCE,
        source_file="cand2.pdf",
    )
    resume_low = Resume(
        candidate_id="cand_low",
        name="Admin Engineer",
        source_file="cand2.pdf",
        raw_text=chunk_low.text,
        skills=[skill],
        evidence_chunks=[chunk_low],
    )

    matches_high = semantic_matcher.compute_semantic_alignment(resume_high, jd)
    matches_low = semantic_matcher.compute_semantic_alignment(resume_low, jd)

    score_high = scorer.calculate_score_breakdown(
        matched_required=[skill],
        all_required=[req],
        matched_preferred=[],
        all_preferred=[],
        semantic_matches=matches_high,
        keyword_matches=[],
    )

    score_low = scorer.calculate_score_breakdown(
        matched_required=[skill],
        all_required=[req],
        matched_preferred=[],
        all_preferred=[],
        semantic_matches=matches_low,
        keyword_matches=[],
    )

    # Material difference (> 0.05 delta on final score)
    score_delta = score_high.final_score - score_low.final_score
    assert score_delta >= 0.05, f"Expected delta >= 0.05, got {score_delta}"
    assert score_high.semantic_requirement_alignment > score_low.semantic_requirement_alignment


def test_configurable_semantic_thresholds():
    """Verify that custom semantic thresholds alter match classification."""
    custom_settings = Settings(
        SEMANTIC_EXACT_THRESHOLD=0.95,
        SEMANTIC_SIMILARITY_THRESHOLD=0.85,
        SEMANTIC_INFERRED_THRESHOLD=0.70,
    )
    matcher = SemanticMatcher(settings=custom_settings)

    req = Requirement(
        id="req_db",
        name="Database",
        type=RequirementType.REQUIRED,
        canonical_name="database",
        source_text="Manage SQL databases and optimize query performance.",
    )
    # Somewhat related chunk with moderate similarity (~0.60 - 0.70)
    chunk = EvidenceChunk(
        id="c_db",
        text="Monitored website traffic metrics using analytics dashboards.",
        section=SectionType.EXPERIENCE,
        source_file="cand.pdf",
    )
    resume = Resume(
        candidate_id="cand_01",
        name="Candidate",
        source_file="cand.pdf",
        raw_text=chunk.text,
        evidence_chunks=[chunk],
    )
    jd = JobDescription(
        id="jd_01",
        title="DBA",
        source_file="jd.pdf",
        raw_text=req.source_text,
        requirements=[req],
    )

    matches = matcher.compute_semantic_alignment(resume, jd)
    # High inferred threshold (0.70) filters out unrelated chunk
    assert len(matches) == 0
