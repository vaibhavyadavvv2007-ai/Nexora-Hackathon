"""Phase 4 Validation Test Suite: Matching, Score Fusion, and Ranking Engine.

Covers all Phase 4 specifications:
1. Increasing semantic score can change rank
2. Increasing explicit skill coverage can change rank
3. Missing critical skill lowers ranking
4. Keyword stuffing does not dominate
5. Semantic-only relevance cannot falsely create exact skill matches
6. Combined ranking differs meaningfully from single-signal modes
7. Identical inputs produce identical rankings (determinism & tie-breaking)
8. Candidate evaluation schema completeness & evidence preservation
9. Full ablation study generation (rankings, top 3, score distribution, position changes)
10. Uncalibrated normalized score distribution (no artificial min-max scaling)
"""

import random
import pytest

from backend.config.settings import Settings
from backend.core.matching.keyword_matcher import KeywordMatcher
from backend.core.matching.semantic_matcher import SemanticMatcher
from backend.core.ranking.engine import (
    AblationReport,
    EvaluationMode,
    RankingEngine,
    compute_distribution_stats,
)
from backend.core.ranking.ranker import Ranker
from backend.core.ranking.scorer import Scorer
from backend.models.document import JobDescription, Resume
from backend.models.enums import MatchType, RequirementType, SectionType
from backend.models.evaluation import CandidateEvaluation
from backend.models.evidence import EvidenceChunk, MatchEvidence
from backend.models.requirement import Requirement
from backend.models.skill import Skill


# ============================================================================
# Test Fixtures & Helpers
# ============================================================================

def _req(
    req_id: str,
    name: str,
    canonical: str,
    req_type: RequirementType = RequirementType.REQUIRED,
    text: str = "",
) -> Requirement:
    return Requirement(
        id=req_id,
        name=name,
        type=req_type,
        canonical_name=canonical,
        source_text=text or f"Must have experience with {name}",
    )


def _skill(
    canonical: str,
    surface: str,
    match_type: MatchType = MatchType.EXACT,
    confidence: float = 1.0,
) -> Skill:
    return Skill(
        canonical_name=canonical,
        surface_form=surface,
        match_type=match_type,
        confidence=confidence,
    )


def _chunk(
    chunk_id: str,
    text: str,
    section: SectionType = SectionType.EXPERIENCE,
    page: int = 1,
    source_file: str = "resume.pdf",
) -> EvidenceChunk:
    return EvidenceChunk(
        id=chunk_id,
        text=text,
        section=section,
        page=page,
        source_file=source_file,
    )


def _resume(
    candidate_id: str,
    name: str,
    skills: list[Skill] | None = None,
    chunks: list[EvidenceChunk] | None = None,
    source_file: str = "resume.pdf",
) -> Resume:
    return Resume(
        candidate_id=candidate_id,
        name=name,
        source_file=source_file,
        raw_text=" ".join(c.text for c in (chunks or [])),
        skills=skills or [],
        evidence_chunks=chunks or [],
    )


def _jd(
    requirements: list[Requirement],
    title: str = "Senior Backend Engineer",
    jd_id: str = "jd_phase4_001",
) -> JobDescription:
    return JobDescription(
        id=jd_id,
        title=title,
        source_file="jd.pdf",
        raw_text=" ".join(r.source_text for r in requirements),
        requirements=requirements,
    )


@pytest.fixture
def engine() -> RankingEngine:
    return RankingEngine()


# ============================================================================
# 1. Increasing semantic score can change rank
# ============================================================================

def test_increasing_semantic_score_can_change_rank(engine: RankingEngine):
    """Test 1: Two candidates with identical skill coverage; candidate with higher

    semantic alignment ranks higher. Increasing a candidate's semantic score flips rank.
    """
    r1 = _req("r1", "Python", "python", text="Develop core backend services using Python.")
    r2 = _req("r2", "Distributed Systems", "distributed systems",
              text="Architect resilient distributed consensus and event streaming systems.")
    jd = _jd([r1, r2])

    sk_py = _skill("python", "Python")

    # Cand A: has Python, but weak/generic text for distributed systems
    chunk_a = _chunk("ca1", "Assisted with office software and managed internal spreadsheets.")
    cand_a = _resume("cand_a", "Alice Admin", skills=[sk_py], chunks=[chunk_a])

    # Cand B: has Python, and strong distributed systems experience
    chunk_b = _chunk("cb1", "Architected high-throughput distributed microservices with Kafka streaming and consensus protocols.")
    cand_b = _resume("cand_b", "Bob Architect", skills=[sk_py], chunks=[chunk_b])

    initial_ranking = engine.evaluate_and_rank_batch([cand_a, cand_b], jd)
    assert initial_ranking[0].candidate_id == "cand_b"
    assert initial_ranking[0].rank == 1
    assert initial_ranking[1].candidate_id == "cand_a"
    assert initial_ranking[1].rank == 2

    # Now upgrade Alice with world-class distributed systems experience
    chunk_a_upgraded = _chunk(
        "ca2",
        "Architect resilient distributed consensus and event streaming systems with Python and Kafka.",
    )
    cand_a_upgraded = _resume("cand_a", "Alice Admin", skills=[sk_py], chunks=[chunk_a_upgraded])

    updated_ranking = engine.evaluate_and_rank_batch([cand_a_upgraded, cand_b], jd)
    assert updated_ranking[0].candidate_id == "cand_a"
    assert updated_ranking[0].rank == 1
    assert updated_ranking[0].semantic_score > initial_ranking[1].semantic_score
    assert updated_ranking[1].candidate_id == "cand_b"
    assert updated_ranking[1].rank == 2


# ============================================================================
# 2. Increasing explicit skill coverage can change rank
# ============================================================================

def test_increasing_explicit_skill_coverage_can_change_rank(engine: RankingEngine):
    """Test 2: Candidate with 1/2 skills ranks below candidate with 2/2 skills.

    When the candidate adds the missing explicit skill, their rank increases.
    """
    r1 = _req("r1", "Python", "python", text="Write idiomatic Python services.")
    r2 = _req("r2", "Kubernetes", "kubernetes", text="Deploy and manage containers on Kubernetes clusters.")
    jd = _jd([r1, r2])

    sk_py = _skill("python", "Python")
    sk_k8s = _skill("kubernetes", "Kubernetes")

    # Cand A: only Python (coverage = 0.5)
    chunk_a = _chunk("ca", "Python developer building REST APIs and microservices.")
    cand_a_partial = _resume("cand_a", "Candidate A", skills=[sk_py], chunks=[chunk_a])

    # Cand B: Python + Kubernetes (coverage = 1.0)
    chunk_b = _chunk("cb", "Deployed Python applications onto production Kubernetes clusters.")
    cand_b_full = _resume("cand_b", "Candidate B", skills=[sk_py, sk_k8s], chunks=[chunk_b])

    initial_ranking = engine.evaluate_and_rank_batch([cand_a_partial, cand_b_full], jd)
    assert initial_ranking[0].candidate_id == "cand_b"
    assert initial_ranking[0].required_coverage == 1.0
    assert initial_ranking[1].candidate_id == "cand_a"
    assert initial_ranking[1].required_coverage == 0.5

    # Now Cand A gains Kubernetes certification & skill
    cand_a_complete = _resume("cand_a", "Candidate A", skills=[sk_py, sk_k8s], chunks=[chunk_a])
    updated_ranking = engine.evaluate_and_rank_batch([cand_a_complete, cand_b_full], jd)

    # Coverage increased from 0.5 to 1.0
    eval_a = next(e for e in updated_ranking if e.candidate_id == "cand_a")
    assert eval_a.required_coverage == 1.0
    assert eval_a.final_score > initial_ranking[1].final_score


# ============================================================================
# 3. Missing critical skill lowers ranking
# ============================================================================

def test_missing_critical_skill_lowers_ranking(engine: RankingEngine):
    """Test 3: Missing a required critical skill lowers candidate score and ranking."""
    r1 = _req("r1", "Go", "go", text="Develop high-performance networking daemons in Go.")
    r2 = _req("r2", "Docker", "docker", text="Containerize services using Docker.")
    r3 = _req("r3", "PostgreSQL", "postgresql", text="Optimize PostgreSQL database queries.")
    jd = _jd([r1, r2, r3])

    sk_go = _skill("go", "Go")
    sk_docker = _skill("docker", "Docker")
    sk_pg = _skill("postgresql", "PostgreSQL")

    chunk_full = _chunk("c1", "Built Go microservices in Docker with PostgreSQL.")
    cand_full = _resume("c_full", "Full Stack", skills=[sk_go, sk_docker, sk_pg], chunks=[chunk_full])

    chunk_missing = _chunk("c2", "Containerized web applications in Docker using PostgreSQL.")
    cand_missing = _resume("c_missing", "Missing Go", skills=[sk_docker, sk_pg], chunks=[chunk_missing])

    ranked = engine.evaluate_and_rank_batch([cand_missing, cand_full], jd)

    assert ranked[0].candidate_id == "c_full"
    assert ranked[0].rank == 1
    assert ranked[1].candidate_id == "c_missing"
    assert ranked[1].rank == 2

    # Check missing required is tracked
    assert len(ranked[1].missing_required) == 1
    assert ranked[1].missing_required[0].canonical_name == "go"
    assert ranked[0].required_coverage > ranked[1].required_coverage


# ============================================================================
# 4. Keyword stuffing does not dominate
# ============================================================================

def test_keyword_stuffing_does_not_dominate(engine: RankingEngine):
    """Test 4: Candidate repeating Python 100 times does not defeat a candidate

    with balanced coverage of all required skills.
    """
    r1 = _req("r1", "Python", "python", text="Write Python backend code.")
    r2 = _req("r2", "Docker", "docker", text="Build Docker containers.")
    r3 = _req("r3", "AWS", "aws", text="Deploy infrastructure on AWS.")
    jd = _jd([r1, r2, r3])

    # Spammer repeats Python 100 times in skills, mentions it repeatedly in text
    sk_py = _skill("python", "Python")
    stuffed_skills = [sk_py] * 100
    stuffed_text = " ".join(["Python python python programming code developer."] * 20)
    chunk_stuffed = _chunk("c_stuff", stuffed_text)
    cand_stuffer = _resume("stuffer", "Keyword Spammer", skills=stuffed_skills, chunks=[chunk_stuffed])

    # Balanced candidate has 1 of each skill
    sk_docker = _skill("docker", "Docker")
    sk_aws = _skill("aws", "AWS")
    chunk_balanced = _chunk("c_bal", "Built Python microservices packaged in Docker and deployed to AWS.")
    cand_balanced = _resume("balanced", "Balanced Pro", skills=[sk_py, sk_docker, sk_aws], chunks=[chunk_balanced])

    ranked = engine.evaluate_and_rank_batch([cand_stuffer, cand_balanced], jd)

    assert ranked[0].candidate_id == "balanced"
    assert ranked[0].rank == 1
    assert ranked[1].candidate_id == "stuffer"
    assert ranked[1].rank == 2

    # Required coverage is strictly capped at 1/3 (0.3333) for stuffer despite 100 repeats
    eval_stuffer = ranked[1]
    assert eval_stuffer.required_coverage == pytest.approx(1.0 / 3.0, abs=1e-3)
    assert len(eval_stuffer.matched_required) == 1
    assert len(eval_stuffer.missing_required) == 2


# ============================================================================
# 5. Semantic-only relevance cannot falsely create exact skill matches
# ============================================================================

def test_semantic_only_relevance_cannot_falsely_create_exact_skill_matches(engine: RankingEngine):
    """Test 5: MongoDB requirement + PostgreSQL resume:

    Semantic evidence captures related database experience, but MongoDB is strictly
    retained in missing_required and required_skill_coverage is 0.0.
    """
    req_mongo = _req("r_mongo", "MongoDB", "mongodb", text="Design MongoDB document schemas and replica sets.")
    jd = _jd([req_mongo])

    sk_postgres = _skill("postgresql", "PostgreSQL")
    chunk = _chunk("c_pg", "Database engineer with PostgreSQL expertise designing document schemas, JSON collections, and NoSQL storage pipelines.")
    resume = _resume("cand_pg", "Postgres Dev", skills=[sk_postgres], chunks=[chunk])

    evaluation = engine.evaluate_candidate(resume, jd, mode=EvaluationMode.COMBINED)

    # Invariants
    assert len(evaluation.matched_required) == 0
    assert len(evaluation.missing_required) == 1
    assert evaluation.missing_required[0].canonical_name == "mongodb"
    assert evaluation.required_coverage == 0.0

    # Semantic evidence exists and reflects related database concept
    assert len(evaluation.semantic_matches) > 0
    sem_ev = evaluation.semantic_matches[0]
    assert sem_ev.similarity is not None
    assert sem_ev.similarity >= 0.45  # Related database semantic overlap above inferred threshold
    # Crucially, semantic match did NOT convert missing MongoDB into an explicit match
    assert all(s.canonical_name != "mongodb" for s in evaluation.matched_required)


# ============================================================================
# 6. Combined ranking differs meaningfully from single-signal modes
# ============================================================================

def test_combined_ranking_differs_meaningfully_from_single_signal_mode(engine: RankingEngine):
    """Test 6: Demonstrates that combined mode produces a different ranking

    than keyword-only and semantic-only single-signal modes.
    """
    r1 = _req("r1", "Python", "python", text="Build scalable Python backend systems.")
    r2 = _req("r2", "Kafka", "kafka", text="Stream events with Apache Kafka messaging queues.")
    r3 = _req("r3", "Cassandra", "cassandra", text="Store distributed time-series in Apache Cassandra.")
    jd = _jd([r1, r2, r3])

    sk_py = _skill("python", "Python")
    sk_kafka = _skill("kafka", "Kafka")
    sk_cass = _skill("cassandra", "Cassandra")

    # Cand 1: "KeywordKing" - Has all 3 skills listed, but very weak/vague evidence text
    chunk_1 = _chunk("c1", "General tasks and miscellaneous tech maintenance.")
    c1 = _resume("c1", "Keyword King", skills=[sk_py, sk_kafka, sk_cass], chunks=[chunk_1])

    # Cand 2: "SemanticHero" - Has 0 skills in resume.skills list, but rich deep experience in evidence chunks
    chunk_2 = _chunk(
        "c2",
        "Engineered scalable Python microservices publishing streaming events to Apache Kafka with Apache Cassandra persistence.",
    )
    c2 = _resume("c2", "Semantic Hero", skills=[], chunks=[chunk_2])

    # Cand 3: "BalancedPerformer" - Has 2/3 skills (Python, Kafka) and strong evidence text
    chunk_3 = _chunk("c3", "Developed high-throughput Python pipelines integrating Kafka message queues.")
    c3 = _resume("c3", "Balanced Performer", skills=[sk_py, sk_kafka], chunks=[chunk_3])

    resumes = [c1, c2, c3]

    ablation = engine.run_ablation_study(resumes, jd)

    rank_kw = [e.candidate_id for e in ablation.modes["keyword-only"].full_ranking]
    rank_sem = [e.candidate_id for e in ablation.modes["semantic-only"].full_ranking]
    rank_comb = [e.candidate_id for e in ablation.modes["combined"].full_ranking]

    # Keyword-only: c1 must be rank 1 (has 3/3 keywords)
    assert rank_kw[0] == "c1"

    # Semantic-only: c2 or c3 must be ahead of c1 (c1 has near zero semantic text)
    assert rank_sem[0] != "c1"

    # Combined ranking is balanced: either different from keyword-only or different from semantic-only
    assert rank_comb != rank_kw or rank_comb != rank_sem

    # Position changes recorded
    assert len(ablation.position_changes) == 3


# ============================================================================
# 7. Identical inputs produce identical rankings (Determinism & Tie-Breaking)
# ============================================================================

def test_identical_inputs_produce_identical_rankings(engine: RankingEngine):
    """Test 7: Shuffling input resume order produces 100% identical rankings and scores."""
    r1 = _req("r1", "React", "react", text="Frontend React SPA development.")
    r2 = _req("r2", "TypeScript", "typescript", text="Strong TypeScript type safety.")
    jd = _jd([r1, r2])

    sk_react = _skill("react", "React")
    sk_ts = _skill("typescript", "TypeScript")

    c1 = _resume("cand_01", "Adam", skills=[sk_react, sk_ts], chunks=[_chunk("c1", "React with TypeScript")])
    c2 = _resume("cand_02", "Bella", skills=[sk_react], chunks=[_chunk("c2", "React components")])
    c3 = _resume("cand_03", "Charlie", skills=[sk_ts], chunks=[_chunk("c3", "TypeScript utilities")])
    c4 = _resume("cand_04", "Daisy", skills=[], chunks=[_chunk("c4", "UI designer with HTML")])
    # Tie candidate with identical scores to Bella, testing candidate_id tie-breaker
    c5 = _resume("cand_05", "Evan", skills=[sk_react], chunks=[_chunk("c5", "React components")])

    base_list = [c1, c2, c3, c4, c5]
    reference_ranking = engine.evaluate_and_rank_batch(base_list, jd)
    ref_order = [(e.candidate_id, e.rank, e.final_score) for e in reference_ranking]

    # Run 10 trials with randomized order
    rng = random.Random(42)
    for trial in range(10):
        shuffled = list(base_list)
        rng.shuffle(shuffled)
        trial_ranking = engine.evaluate_and_rank_batch(shuffled, jd)
        trial_order = [(e.candidate_id, e.rank, e.final_score) for e in trial_ranking]
        assert trial_order == ref_order, f"Determinism violation on trial {trial}"


# ============================================================================
# 8. Candidate Evaluation Schema Completeness
# ============================================================================

def test_candidate_evaluation_schema_completeness(engine: RankingEngine):
    """Test 8: Evaluates a candidate and verifies all fields and convenience

    accessors required by Phase 4 are present and correctly populated.
    """
    req1 = _req("r1", "Python", "python", text="Built Python microservices")
    pref1 = _req("p1", "Docker", "docker", req_type=RequirementType.PREFERRED, text="Docker containers")
    jd = _jd([req1, pref1])

    sk_py = _skill("python", "Python")
    chunk = _chunk("e1", "Built Python microservices and deployed Docker containers", page=2, source_file="resume_john.pdf")
    resume = _resume("cand_john", "John Doe", skills=[sk_py], chunks=[chunk], source_file="resume_john.pdf")

    eval_result = engine.evaluate_candidate(resume, jd, mode=EvaluationMode.COMBINED)

    # Required Phase 4 schema fields
    assert eval_result.candidate_id == "cand_john"
    assert eval_result.candidate_name == "John Doe"
    assert eval_result.required_coverage == 1.0
    assert eval_result.preferred_coverage == 0.0
    assert eval_result.lexical_score is not None and eval_result.lexical_score >= 0.0
    assert eval_result.semantic_score is not None and eval_result.semantic_score >= 0.0
    assert eval_result.final_score is not None and 0.0 <= eval_result.final_score <= 1.0

    # Lists
    assert len(eval_result.matched_required) == 1
    assert eval_result.matched_required[0].canonical_name == "python"
    assert len(eval_result.matched_preferred) == 0
    assert len(eval_result.missing_required) == 0
    assert len(eval_result.keyword_evidence) > 0
    assert len(eval_result.semantic_evidence) > 0

    # Evidence preservation for explanation
    assert len(eval_result.evidence) == 1
    assert eval_result.evidence[0].page == 2
    assert eval_result.evidence[0].source_file == "resume_john.pdf"


# ============================================================================
# 9. Ablation Study Report Structure
# ============================================================================

def test_ablation_study_report_structure(engine: RankingEngine):
    """Test 9: Verifies full ranking, top 3, score distribution, and position changes."""
    r1 = _req("r1", "Java", "java")
    jd = _jd([r1])

    c1 = _resume("c1", "Cand 1", skills=[_skill("java", "Java")], chunks=[_chunk("e1", "Java spring")])
    c2 = _resume("c2", "Cand 2", skills=[], chunks=[_chunk("e2", "Java backend")])
    c3 = _resume("c3", "Cand 3", skills=[], chunks=[_chunk("e3", "frontend developer")])
    c4 = _resume("c4", "Cand 4", skills=[_skill("java", "Java")], chunks=[_chunk("e4", "Java enterprise")])

    report = engine.run_ablation_study([c1, c2, c3, c4], jd)

    assert report.total_candidates == 4
    assert set(report.modes.keys()) == {"combined", "keyword-only", "semantic-only"}

    for mode_name in ["combined", "keyword-only", "semantic-only"]:
        mode_sum = report.modes[mode_name]
        assert len(mode_sum.full_ranking) == 4
        assert len(mode_sum.top_3) == 3
        dist = mode_sum.score_distribution
        assert "mean" in dist
        assert "std" in dist
        assert "min" in dist
        assert "max" in dist
        assert "median" in dist
        assert 0.0 <= dist["min"] <= dist["max"] <= 1.0

    # Position changes structure
    assert len(report.position_changes) == 4
    for pc in report.position_changes:
        assert pc.candidate_id in {"c1", "c2", "c3", "c4"}
        assert 1 <= pc.rank_combined <= 4


# ============================================================================
# 10. Score distribution preserves component values (no artificial min-max)
# ============================================================================

def test_score_distribution_no_min_max_distortion(engine: RankingEngine):
    """Test 10: Scores are NOT artificially stretched to [0, 1] across candidates.

    True metric normalization is preserved.
    """
    r1 = _req("r1", "C++", "c++", text="Write low-latency C++ game engines.")
    r2 = _req("r2", "Rust", "rust", text="Write memory-safe Rust systems.")
    jd = _jd([r1, r2])

    # All candidates have only 1/2 skills and moderate semantic evidence
    sk_cpp = _skill("c++", "C++")
    c1 = _resume("c1", "Dev 1", skills=[sk_cpp], chunks=[_chunk("e1", "C++ developer")])
    c2 = _resume("c2", "Dev 2", skills=[sk_cpp], chunks=[_chunk("e2", "C++ systems engineer")])

    ranked = engine.evaluate_and_rank_batch([c1, c2], jd)

    # If min-max scaling were applied across candidates, one would be 1.0 and one would be 0.0
    # True scores must reflect realistic values (~0.35 to 0.60)
    for item in ranked:
        assert item.final_score is not None
        assert 0.20 <= item.final_score <= 0.85
        # Neither candidate is artificially 0.0 or 1.0
        assert item.final_score != 0.0
        assert item.final_score != 1.0


# ============================================================================
# 11. Phase 3 Input Contract Direct Consumption
# ============================================================================

def test_phase3_input_contract_direct_consumption(engine: RankingEngine):
    """Test 11: Directly consumes Phase 3 models using only Phase 3 fields:
    JobDescription: requirements, responsibilities
    Requirement: id, canonical_name, source_text, type, weight, critical, source_page, confidence, is_skill_matchable
    Resume: candidate_id, name, skills, evidence_chunks
    EvidenceChunk: text, section, page, source_file, confidence
    """
    req_py = Requirement(
        id="req_01",
        canonical_name="python",
        source_text="Must develop backend APIs in Python",
        type=RequirementType.REQUIRED,
        weight=1.0,
        critical=True,
        source_page=1,
        confidence=0.98,
        is_skill_matchable=True,
    )
    req_lead = Requirement(
        id="req_02",
        canonical_name="technical leadership",
        source_text="Lead technical architecture and mentor engineering team",
        type=RequirementType.PREFERRED,
        weight=1.0,
        critical=False,
        source_page=1,
        confidence=0.95,
        is_skill_matchable=False,  # non-skill requirement, evaluated semantically
    )

    jd = JobDescription(
        id="jd_real_001",
        title="Staff Backend Engineer",
        source_file="job_description.pdf",
        raw_text="Staff Backend Engineer Job Description",
        requirements=[req_py, req_lead],
        responsibilities=["Design distributed backend services", "Mentor junior engineers"],
    )

    sk_python = Skill(
        canonical_name="python",
        surface_form="Python",
        match_type=MatchType.EXACT,
        confidence=1.0,
    )
    chunk1 = EvidenceChunk(
        text="Architected and built scalable Python REST and gRPC microservices.",
        section=SectionType.EXPERIENCE,
        page=1,
        source_file="resume_real_01.pdf",
        confidence=0.99,
    )
    chunk2 = EvidenceChunk(
        text="Spearheaded system architecture and mentored team of 8 backend developers.",
        section=SectionType.EXPERIENCE,
        page=2,
        source_file="resume_real_01.pdf",
        confidence=0.97,
    )

    resume = Resume(
        candidate_id="cand_real_001",
        name="Elena Rostova",
        source_file="resume_real_01.pdf",
        raw_text="Elena Rostova Senior Staff Engineer",
        skills=[sk_python],
        evidence_chunks=[chunk1, chunk2],
    )

    evaluation = engine.evaluate_candidate(resume, jd, mode=EvaluationMode.COMBINED)

    assert evaluation.candidate_id == "cand_real_001"
    assert evaluation.candidate_name == "Elena Rostova"
    assert evaluation.required_coverage == 1.0  # Python matched
    assert evaluation.semantic_score > 0.50    # Both technical leadership and Python matched semantically
    assert evaluation.final_score is not None and evaluation.final_score > 0.50
    assert len(evaluation.matched_required) == 1
    assert evaluation.matched_required[0].canonical_name == "python"
    assert len(evaluation.missing_required) == 0
    assert len(evaluation.evidence) == 2

