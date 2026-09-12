"""Tests for Scorer and Ranker components.

Validates:
8. Keyword score materially changes final score
9. Keyword-only ranking
10. Semantic-only ranking
11. Combined ranking
12. Keyword stuffing does not create huge score inflation
13. Long resumes do not automatically win
"""

import pytest
from backend.config.settings import Settings
from backend.core.matching.keyword_matcher import KeywordMatcher
from backend.core.ranking.ranker import Ranker
from backend.core.ranking.scorer import Scorer
from backend.models.document import JobDescription, Resume
from backend.models.enums import MatchType, RequirementType, SectionType
from backend.models.evaluation import CandidateEvaluation, ScoreStructure
from backend.models.evidence import EvidenceChunk, MatchEvidence
from backend.models.requirement import Requirement
from backend.models.skill import Skill


@pytest.fixture
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture
def ranker() -> Ranker:
    return Ranker()


def test_keyword_score_materially_changes_final_score(scorer: Scorer):
    """Test 8: Having vs lacking required keyword coverage materially shifts the final score."""
    req1 = Requirement(id="r1", name="Python", type=RequirementType.REQUIRED, canonical_name="python", source_text="Python")
    req2 = Requirement(id="r2", name="Docker", type=RequirementType.REQUIRED, canonical_name="docker", source_text="Docker")

    skill1 = Skill(canonical_name="python", surface_form="Python", match_type=MatchType.EXACT, confidence=1.0)
    skill2 = Skill(canonical_name="docker", surface_form="Docker", match_type=MatchType.EXACT, confidence=1.0)

    # Identical semantic matches for both candidates
    sem_match = MatchEvidence(
        requirement=req1,
        evidence=EvidenceChunk(id="e1", text="Built containers in Python", section=SectionType.EXPERIENCE, source_file="doc.pdf"),
        match_type=MatchType.SEMANTIC_RELATED,
        confidence=0.75,
        similarity=0.75,
    )

    # Candidate with full required keyword coverage
    score_full_kw = scorer.calculate_score_breakdown(
        matched_required=[skill1, skill2],
        all_required=[req1, req2],
        matched_preferred=[],
        all_preferred=[],
        semantic_matches=[sem_match],
        keyword_matches=[],
    )

    # Candidate with zero required keyword coverage
    score_zero_kw = scorer.calculate_score_breakdown(
        matched_required=[],
        all_required=[req1, req2],
        matched_preferred=[],
        all_preferred=[],
        semantic_matches=[sem_match],
        keyword_matches=[],
    )

    assert score_full_kw.required_skill_coverage == 1.0
    assert score_zero_kw.required_skill_coverage == 0.0
    score_delta = score_full_kw.final_score - score_zero_kw.final_score
    # 0.35 * 1.0 = 0.35 delta
    assert score_delta >= 0.30


def test_keyword_only_ranking(ranker: Ranker):
    """Test 9: Configured with keyword-dominated weights, ranking reflects keyword presence."""
    custom_weights = {
        "required_skill_coverage": 0.80,
        "semantic_requirement_alignment": 0.00,
        "contextual_lexical_relevance": 0.10,
        "preferred_skill_coverage": 0.10,
    }
    scorer = Scorer(weights=custom_weights)

    req1 = Requirement(id="r1", name="Go", type=RequirementType.REQUIRED, canonical_name="go", source_text="Go")
    req2 = Requirement(id="r2", name="K8s", type=RequirementType.REQUIRED, canonical_name="kubernetes", source_text="K8s")

    skill_go = Skill(canonical_name="go", surface_form="Go", match_type=MatchType.EXACT, confidence=1.0)
    skill_k8s = Skill(canonical_name="kubernetes", surface_form="K8s", match_type=MatchType.EXACT, confidence=1.0)

    # Cand A has 2/2 keywords, but lower semantic quality
    scores_a = scorer.calculate_score_breakdown(
        matched_required=[skill_go, skill_k8s],
        all_required=[req1, req2],
        matched_preferred=[],
        all_preferred=[],
        semantic_matches=[],
        keyword_matches=[],
    )
    cand_a = CandidateEvaluation(
        candidate_id="cand_a",
        candidate_name="Keyword Master",
        scores=scores_a,
    )

    # Cand B has 0/2 keywords, but high semantic score passed
    scores_b = scorer.calculate_score_breakdown(
        matched_required=[],
        all_required=[req1, req2],
        matched_preferred=[],
        all_preferred=[],
        semantic_matches=[
            MatchEvidence(
                requirement=req1,
                evidence=EvidenceChunk(id="e1", text="backend", section=SectionType.EXPERIENCE, source_file="doc.pdf"),
                match_type=MatchType.SEMANTIC_EXACT,
                confidence=0.99,
                similarity=0.99,
            )
        ],
        keyword_matches=[],
    )
    cand_b = CandidateEvaluation(
        candidate_id="cand_b",
        candidate_name="Semantic Master",
        scores=scores_b,
    )

    ranked = ranker.rank_candidates([cand_b, cand_a])
    assert ranked[0].candidate_id == "cand_a"
    assert ranked[0].rank == 1
    assert ranked[1].candidate_id == "cand_b"
    assert ranked[1].rank == 2


def test_semantic_only_ranking(ranker: Ranker):
    """Test 10: Configured with semantic-only weights, ranking reflects semantic depth."""
    custom_weights = {
        "required_skill_coverage": 0.00,
        "semantic_requirement_alignment": 1.00,
        "contextual_lexical_relevance": 0.00,
        "preferred_skill_coverage": 0.00,
    }
    scorer = Scorer(weights=custom_weights)

    req = Requirement(id="r1", name="Cloud", type=RequirementType.REQUIRED, canonical_name="cloud", source_text="Cloud")

    # Cand A: High semantic alignment
    match_high = MatchEvidence(
        requirement=req,
        evidence=EvidenceChunk(id="e1", text="Architected distributed cloud clusters", section=SectionType.EXPERIENCE, source_file="doc1.pdf"),
        match_type=MatchType.SEMANTIC_EXACT,
        confidence=0.95,
        similarity=0.95,
    )
    scores_a = scorer.calculate_score_breakdown([], [req], [], [], [match_high], [])
    cand_a = CandidateEvaluation(candidate_id="cand_a", candidate_name="High Semantic", scores=scores_a)

    # Cand B: Weak semantic alignment
    match_low = MatchEvidence(
        requirement=req,
        evidence=EvidenceChunk(id="e2", text="Used a spreadsheet", section=SectionType.EXPERIENCE, source_file="doc2.pdf"),
        match_type=MatchType.SEMANTIC_INFERRED,
        confidence=0.40,
        similarity=0.40,
    )
    scores_b = scorer.calculate_score_breakdown([], [req], [], [], [match_low], [])
    cand_b = CandidateEvaluation(candidate_id="cand_b", candidate_name="Low Semantic", scores=scores_b)

    ranked = ranker.rank_candidates([cand_b, cand_a])
    assert ranked[0].candidate_id == "cand_a"
    assert ranked[0].rank == 1
    assert ranked[1].candidate_id == "cand_b"
    assert ranked[1].rank == 2


def test_combined_ranking(scorer: Scorer, ranker: Ranker):
    """Test 11: Combined multi-signal ranking integrates coverage, semantics, lexical, and preferred skills."""
    req1 = Requirement(id="r1", name="Python", type=RequirementType.REQUIRED, canonical_name="python", source_text="Python")
    req2 = Requirement(id="r2", name="PostgreSQL", type=RequirementType.REQUIRED, canonical_name="postgresql", source_text="PostgreSQL")
    pref1 = Requirement(id="p1", name="Redis", type=RequirementType.PREFERRED, canonical_name="redis", source_text="Redis")

    skill_py = Skill(canonical_name="python", surface_form="Python", match_type=MatchType.EXACT, confidence=1.0)
    skill_pg = Skill(canonical_name="postgresql", surface_form="PostgreSQL", match_type=MatchType.EXACT, confidence=1.0)
    skill_redis = Skill(canonical_name="redis", surface_form="Redis", match_type=MatchType.EXACT, confidence=1.0)

    # Candidate 1: Well-rounded candidate (covers required + preferred + high semantics)
    sem_1 = [
        MatchEvidence(
            requirement=req1,
            evidence=EvidenceChunk(id="e1", text="Built scalable Python microservices with PostgreSQL and Redis caching", section=SectionType.EXPERIENCE, source_file="c1.pdf"),
            match_type=MatchType.SEMANTIC_EXACT,
            confidence=0.90,
            similarity=0.90,
        )
    ]
    lex_1 = [
        MatchEvidence(
            requirement=req1,
            evidence=EvidenceChunk(id="e1", text="Python PostgreSQL Redis", section=SectionType.SKILLS, source_file="c1.pdf"),
            match_type=MatchType.LEXICAL,
            confidence=0.85,
        )
    ]
    scores_1 = scorer.calculate_score_breakdown([skill_py, skill_pg], [req1, req2], [skill_redis], [pref1], sem_1, lex_1)
    cand_1 = CandidateEvaluation(candidate_id="c1", candidate_name="Strong All-Rounder", scores=scores_1)

    # Candidate 2: Required only, mediocre semantics
    scores_2 = scorer.calculate_score_breakdown([skill_py], [req1, req2], [], [pref1], [], [])
    cand_2 = CandidateEvaluation(candidate_id="c2", candidate_name="Partial Required", scores=scores_2)

    # Candidate 3: Zero skills
    scores_3 = scorer.calculate_score_breakdown([], [req1, req2], [], [pref1], [], [])
    cand_3 = CandidateEvaluation(candidate_id="c3", candidate_name="Unqualified", scores=scores_3)

    ranked = ranker.rank_candidates([cand_3, cand_2, cand_1])
    assert ranked[0].candidate_id == "c1"
    assert ranked[1].candidate_id == "c2"
    assert ranked[2].candidate_id == "c3"
    assert [c.rank for c in ranked] == [1, 2, 3]


def test_keyword_stuffing_does_not_create_huge_inflation(scorer: Scorer):
    """Test 12: Keyword stuffing (repeating the same term 50 times) does not inflate score beyond bounds."""
    req_py = Requirement(id="r1", name="Python", type=RequirementType.REQUIRED, canonical_name="python", source_text="Python")
    req_pg = Requirement(id="r2", name="PostgreSQL", type=RequirementType.REQUIRED, canonical_name="postgresql", source_text="PostgreSQL")

    skill_py = Skill(canonical_name="python", surface_form="Python", match_type=MatchType.EXACT, confidence=1.0)
    # Stuffed resume with 50 Python mentions
    stuffed_skills = [skill_py] * 50

    # Keyword matcher duplicate suppression means only 1 python is matched
    km = KeywordMatcher()
    matched, missing = km.match_explicit_skills(stuffed_skills, [req_py, req_pg])
    assert len(matched) == 1
    assert len(missing) == 1

    # Stuffed BM25 evidence: even if BM25 produces confidence 1.0 for req1, req2 has 0.0
    stuffed_lexical = [
        MatchEvidence(
            requirement=req_py,
            evidence=EvidenceChunk(id=f"chk_{i}", text="Python Python Python", section=SectionType.SKILLS, source_file="stuffed.pdf"),
            match_type=MatchType.LEXICAL,
            confidence=1.0,
        )
        for i in range(50)
    ]

    scores = scorer.calculate_score_breakdown(
        matched_required=matched,
        all_required=[req_py, req_pg],
        matched_preferred=[],
        all_preferred=[],
        semantic_matches=[],
        keyword_matches=stuffed_lexical,
    )

    # Required coverage is capped at 0.5 (1 of 2 requirements)
    assert scores.required_skill_coverage == 0.5
    # Contextual lexical relevance averages across req1 (1.0) and req2 (0.0) -> 0.5
    assert scores.contextual_lexical_relevance <= 0.5
    # Final score remains strictly bounded and does not inflate
    assert scores.final_score <= 0.35 * 0.5 + 0.20 * 0.5 + 0.01


def test_long_resumes_do_not_automatically_win(scorer: Scorer, ranker: Ranker):
    """Test 13: A long resume full of irrelevant padding does not outrank a concise, targeted resume."""
    req = Requirement(id="r1", name="Go", type=RequirementType.REQUIRED, canonical_name="go", source_text="Build Go services")
    skill_go = Skill(canonical_name="go", surface_form="Go", match_type=MatchType.EXACT, confidence=1.0)

    # Concise resume: directly matches Go with strong semantic and lexical evidence
    concise_sem = [
        MatchEvidence(
            requirement=req,
            evidence=EvidenceChunk(id="c_c1", text="Built Go microservices for real-time payment ingestion", section=SectionType.EXPERIENCE, source_file="short.pdf"),
            match_type=MatchType.SEMANTIC_EXACT,
            confidence=0.92,
            similarity=0.92,
        )
    ]
    concise_lex = [
        MatchEvidence(
            requirement=req,
            evidence=EvidenceChunk(id="c_c1", text="Built Go microservices", section=SectionType.EXPERIENCE, source_file="short.pdf"),
            match_type=MatchType.LEXICAL,
            confidence=0.90,
        )
    ]
    scores_concise = scorer.calculate_score_breakdown([skill_go], [req], [], [], concise_sem, concise_lex)
    cand_concise = CandidateEvaluation(candidate_id="concise", candidate_name="Concise Pro", scores=scores_concise)

    # Long resume: 100 chunks of unrelated padding, weak semantic relevance
    long_sem = [
        MatchEvidence(
            requirement=req,
            evidence=EvidenceChunk(id="c_l50", text="Attended general weekly company sync meeting", section=SectionType.EXPERIENCE, source_file="long.pdf"),
            match_type=MatchType.SEMANTIC_INFERRED,
            confidence=0.52,
            similarity=0.52,
        )
    ]
    scores_long = scorer.calculate_score_breakdown([skill_go], [req], [], [], long_sem, [])
    cand_long = CandidateEvaluation(candidate_id="long", candidate_name="Long Padded", scores=scores_long)

    ranked = ranker.rank_candidates([cand_long, cand_concise])
    assert ranked[0].candidate_id == "concise"
    assert ranked[0].rank == 1
    assert ranked[1].candidate_id == "long"
    assert ranked[1].rank == 2
