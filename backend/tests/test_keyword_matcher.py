"""Tests for the Keyword Matching Engine.

Validates:
1. Exact keyword matching
2. Alias matching
3. Missing skill detection
4. PostgreSQL does not satisfy MongoDB
5. Express provides related evidence for Node.js (does not satisfy explicit requirement)
6. Duplicate suppression
7. Lexical BM25 evidence computed independently from explicit coverage
"""

import pytest
from backend.core.matching.keyword_matcher import KeywordMatcher
from backend.core.matching.skill_taxonomy import (
    get_aliases,
    get_related_canonicals,
    resolve_canonical,
)
from backend.models.document import JobDescription, Resume
from backend.models.enums import MatchType, RequirementType, SectionType
from backend.models.evidence import EvidenceChunk
from backend.models.requirement import Requirement
from backend.models.skill import Skill


@pytest.fixture
def keyword_matcher() -> KeywordMatcher:
    return KeywordMatcher()


def test_exact_keyword_matching(keyword_matcher: KeywordMatcher):
    """Test 1: Exact canonical keyword matching."""
    jd_req = Requirement(
        id="req_react",
        name="React",
        type=RequirementType.REQUIRED,
        canonical_name="react",
        source_text="Must have experience with React.",
    )
    resume_skill = Skill(
        canonical_name="react",
        surface_form="React",
        match_type=MatchType.EXACT,
        confidence=1.0,
    )

    matched, missing = keyword_matcher.match_explicit_skills(
        resume_skills=[resume_skill],
        jd_requirements=[jd_req],
    )

    assert len(matched) == 1
    assert len(missing) == 0
    assert matched[0].canonical_name == "react"
    assert matched[0].match_type == MatchType.EXACT


def test_alias_matching(keyword_matcher: KeywordMatcher):
    """Test 2: Alias matching resolves k8s -> kubernetes."""
    jd_req = Requirement(
        id="req_k8s",
        name="Kubernetes",
        type=RequirementType.REQUIRED,
        canonical_name="kubernetes",
        source_text="Requires hands-on Kubernetes orchestration experience.",
    )
    resume_skill = Skill(
        canonical_name="kubernetes",
        surface_form="k8s",
        match_type=MatchType.ALIAS,
        confidence=0.95,
    )

    matched, missing = keyword_matcher.match_explicit_skills(
        resume_skills=[resume_skill],
        jd_requirements=[jd_req],
    )

    assert len(matched) == 1
    assert len(missing) == 0
    assert matched[0].canonical_name == "kubernetes"


def test_missing_skill_detection(keyword_matcher: KeywordMatcher):
    """Test 3: Missing required skill is correctly identified."""
    jd_req = Requirement(
        id="req_mongo",
        name="MongoDB",
        type=RequirementType.REQUIRED,
        canonical_name="mongodb",
        source_text="Proficiency with MongoDB is required.",
    )
    resume_skill = Skill(
        canonical_name="python",
        surface_form="Python",
        match_type=MatchType.EXACT,
        confidence=1.0,
    )

    matched, missing = keyword_matcher.match_explicit_skills(
        resume_skills=[resume_skill],
        jd_requirements=[jd_req],
    )

    assert len(matched) == 0
    assert len(missing) == 1
    assert missing[0].id == "req_mongo"
    assert missing[0].canonical_name == "mongodb"


def test_postgresql_does_not_satisfy_mongodb(keyword_matcher: KeywordMatcher):
    """Test 4: PostgreSQL does NOT satisfy MongoDB requirement."""
    jd_req = Requirement(
        id="req_mongo",
        name="MongoDB",
        type=RequirementType.REQUIRED,
        canonical_name="mongodb",
        source_text="Experience with MongoDB required for document store management.",
    )
    resume_skill = Skill(
        canonical_name="postgresql",
        surface_form="PostgreSQL",
        match_type=MatchType.EXACT,
        confidence=1.0,
    )

    matched, missing = keyword_matcher.match_explicit_skills(
        resume_skills=[resume_skill],
        jd_requirements=[jd_req],
    )

    # MongoDB MUST be missing even though candidate knows PostgreSQL
    assert len(matched) == 0
    assert len(missing) == 1
    assert missing[0].id == "req_mongo"

    # Taxonomy verification
    assert resolve_canonical("postgresql") != resolve_canonical("mongodb")
    assert "postgresql" not in get_aliases("mongodb")
    assert "mongodb" not in get_aliases("postgresql")


def test_express_provides_related_evidence_not_explicit_node(keyword_matcher: KeywordMatcher):
    """Test 5: Express.js provides related evidence for Node.js, but does NOT satisfy explicit Node.js requirement."""
    jd_req = Requirement(
        id="req_node",
        name="Node.js",
        type=RequirementType.REQUIRED,
        canonical_name="node.js",
        source_text="Must have strong experience building services in Node.js.",
    )
    resume_skill = Skill(
        canonical_name="express.js",
        surface_form="Express.js",
        match_type=MatchType.EXACT,
        confidence=1.0,
    )

    matched, missing = keyword_matcher.match_explicit_skills(
        resume_skills=[resume_skill],
        jd_requirements=[jd_req],
    )

    # Express.js alone does NOT satisfy explicit Node.js requirement
    assert len(matched) == 0
    assert len(missing) == 1
    assert missing[0].id == "req_node"

    # But taxonomy confirms Express.js is a related technology providing evidence for Node.js
    related_to_express = get_related_canonicals("express.js")
    assert "node.js" in related_to_express


def test_duplicate_suppression(keyword_matcher: KeywordMatcher):
    """Test 8/suppression: Repeating the same skill does not duplicate matches."""
    jd_req = Requirement(
        id="req_python",
        name="Python",
        type=RequirementType.REQUIRED,
        canonical_name="python",
        source_text="Expert Python developer needed.",
    )
    resume_skills = [
        Skill(canonical_name="python", surface_form="Python", match_type=MatchType.EXACT, confidence=1.0),
        Skill(canonical_name="python", surface_form="py", match_type=MatchType.ALIAS, confidence=0.95),
        Skill(canonical_name="python", surface_form="python3", match_type=MatchType.ALIAS, confidence=0.95),
    ]

    matched, missing = keyword_matcher.match_explicit_skills(
        resume_skills=resume_skills,
        jd_requirements=[jd_req],
    )

    assert len(matched) == 1
    assert len(missing) == 0


def test_lexical_bm25_evidence_separate_from_coverage(keyword_matcher: KeywordMatcher):
    """BM25 contextual relevance calculates lexical evidence without altering missing status."""
    jd_req = Requirement(
        id="req_node",
        name="Node.js",
        type=RequirementType.REQUIRED,
        canonical_name="node.js",
        source_text="Build high performance REST APIs using Node.js backend services.",
    )
    chunk = EvidenceChunk(
        id="chk_01",
        text="Engineered high throughput REST APIs and backend services using Express and MongoDB.",
        section=SectionType.EXPERIENCE,
        page=1,
        confidence=1.0,
        source_file="resume.pdf",
    )
    resume = Resume(
        candidate_id="cand_1",
        name="Candidate One",
        source_file="resume.pdf",
        raw_text=chunk.text,
        evidence_chunks=[chunk],
    )
    jd = JobDescription(
        id="jd_1",
        title="Backend Dev",
        source_file="jd.pdf",
        raw_text=jd_req.source_text,
        requirements=[jd_req],
    )

    evidence_list = keyword_matcher.compute_lexical_evidence(resume, jd)

    # BM25 finds lexical relevance due to overlapping terms: "high", "REST", "APIs", "backend", "services"
    assert len(evidence_list) > 0
    assert evidence_list[0].match_type == MatchType.LEXICAL
    assert evidence_list[0].confidence > 0.0
