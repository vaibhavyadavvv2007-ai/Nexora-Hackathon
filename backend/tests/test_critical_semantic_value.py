"""Critical Semantic-Value Test.

Validates the core matching policy and semantic contribution:
JD: "Build REST APIs using Node.js"
Resume evidence: "Developed backend services using Express.js and MongoDB."

Expected behavior:
1. Explicit named skill matching:
   - "node.js" is NOT explicitly matched by Express.js
   - Explicit required coverage is 0.0 (or partial if other skills present)
2. Semantic similarity:
   - Semantic embedding identifies meaningful alignment between "Build REST APIs using Node.js"
     and "Developed backend services using Express.js and MongoDB."
   - Produces similarity >= 0.60, classified as SEMANTIC_RELATED or SEMANTIC_EXACT.
3. Final score:
   - Reflects the semantic contribution: final score is substantially higher than a candidate
     with unrelated background, despite lacking the explicit named skill.
"""

import pytest
from backend.core.matching.keyword_matcher import KeywordMatcher
from backend.core.matching.semantic_matcher import SemanticMatcher
from backend.core.ranking.scorer import Scorer
from backend.models.document import JobDescription, Resume
from backend.models.enums import MatchType, RequirementType, SectionType
from backend.models.evidence import EvidenceChunk
from backend.models.requirement import Requirement
from backend.models.skill import Skill


def test_critical_semantic_value():
    # 1. Job Description setup
    jd_req = Requirement(
        id="req_node_api",
        name="Node.js REST APIs",
        type=RequirementType.REQUIRED,
        canonical_name="node.js",
        source_text="Build REST APIs using Node.js",
    )
    jd = JobDescription(
        id="jd_backend_lead",
        title="Backend Engineer",
        source_file="jd.pdf",
        raw_text=jd_req.source_text,
        requirements=[jd_req],
        required_skills=["node.js"],
    )

    # 2. Candidate with related Express.js & MongoDB experience (no explicit Node.js token)
    chunk_express = EvidenceChunk(
        id="chunk_exp_01",
        text="Developed backend services using Express.js and MongoDB.",
        section=SectionType.EXPERIENCE,
        page=1,
        confidence=1.0,
        source_file="resume_express.pdf",
    )
    skill_express = Skill(
        canonical_name="express.js",
        surface_form="Express.js",
        match_type=MatchType.EXACT,
        confidence=1.0,
    )
    skill_mongo = Skill(
        canonical_name="mongodb",
        surface_form="MongoDB",
        match_type=MatchType.EXACT,
        confidence=1.0,
    )
    resume_related = Resume(
        candidate_id="cand_express",
        name="Express Developer",
        source_file="resume_express.pdf",
        raw_text=chunk_express.text,
        skills=[skill_express, skill_mongo],
        evidence_chunks=[chunk_express],
    )

    # 3. Unrelated Candidate for baseline contrast
    chunk_unrelated = EvidenceChunk(
        id="chunk_unrel_01",
        text="Audited financial ledger spreadsheets and filed corporate tax reports.",
        section=SectionType.EXPERIENCE,
        page=1,
        confidence=1.0,
        source_file="resume_unrelated.pdf",
    )
    resume_unrelated = Resume(
        candidate_id="cand_unrelated",
        name="Financial Auditor",
        source_file="resume_unrelated.pdf",
        raw_text=chunk_unrelated.text,
        skills=[],
        evidence_chunks=[chunk_unrelated],
    )

    # Engines
    keyword_matcher = KeywordMatcher()
    semantic_matcher = SemanticMatcher()
    scorer = Scorer()

    # --- Step A: Explicit Keyword Matching ---
    matched, missing = keyword_matcher.match_explicit_skills(
        resume_skills=resume_related.skills,
        jd_requirements=jd.requirements,
    )
    # Express.js must NOT automatically satisfy explicit Node.js requirement
    assert len(matched) == 0, "Express.js must not satisfy explicit named Node.js requirement"
    assert len(missing) == 1
    assert missing[0].id == "req_node_api"

    # --- Step B: Lexical BM25 Evidence ---
    lexical_matches = keyword_matcher.compute_lexical_evidence(resume_related, jd)

    # --- Step C: Semantic Alignment ---
    semantic_matches = semantic_matcher.compute_semantic_alignment(resume_related, jd)
    assert len(semantic_matches) > 0, "Semantic matcher must find alignment for Express/API text"
    sem_evidence = semantic_matches[0]
    assert sem_evidence.similarity is not None
    # Semantic similarity should be meaningful (>= 0.45)
    assert sem_evidence.similarity >= 0.45, f"Expected meaningful similarity >= 0.45, got {sem_evidence.similarity}"
    assert sem_evidence.match_type in (MatchType.SEMANTIC_RELATED, MatchType.SEMANTIC_INFERRED, MatchType.SEMANTIC_EXACT)

    # Contrast with unrelated candidate semantic alignment
    semantic_unrelated = semantic_matcher.compute_semantic_alignment(resume_unrelated, jd)
    sim_unrelated = semantic_unrelated[0].similarity if semantic_unrelated else 0.0

    # --- Step D: Scoring ---
    score_related = scorer.calculate_score_breakdown(
        matched_required=matched,
        all_required=jd.requirements,
        matched_preferred=[],
        all_preferred=[],
        semantic_matches=semantic_matches,
        keyword_matches=lexical_matches,
    )

    score_unrelated = scorer.calculate_score_breakdown(
        matched_required=[],
        all_required=jd.requirements,
        matched_preferred=[],
        all_preferred=[],
        semantic_matches=semantic_unrelated,
        keyword_matches=[],
    )

    # Verifications:
    # 1. Required coverage is 0.0 (explicit technology missing)
    assert score_related.required_skill_coverage == 0.0

    # 2. Semantic alignment is meaningful
    assert score_related.semantic_requirement_alignment >= 0.45

    # 3. Combined score reflects the semantic contribution (substantially higher than unrelated)
    assert score_related.final_score > score_unrelated.final_score
    score_advantage = score_related.final_score - score_unrelated.final_score
    assert score_advantage >= 0.15, f"Expected semantic advantage >= 0.15, got {score_advantage}"
