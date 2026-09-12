import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.models.enums import MatchType, RequirementType, SectionType
from backend.models.requirement import Requirement
from backend.models.skill import Skill
from backend.models.evidence import EvidenceChunk, MatchEvidence
from backend.models.document import JobDescription, Resume
from backend.models.evaluation import CandidateEvaluation, ScoreStructure


@pytest.fixture
def test_client() -> TestClient:
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def synthetic_requirement() -> Requirement:
    """Generic synthetic requirement fixture."""
    return Requirement(
        id="req_synthetic_01",
        name="Synthetic Tech",
        type=RequirementType.REQUIRED,
        canonical_name="synthetic_tech",
        weight=1.0,
        critical=True,
        source_text="Must have strong experience in Synthetic Tech."
    )


@pytest.fixture
def synthetic_skill() -> Skill:
    """Generic synthetic skill fixture."""
    return Skill(
        canonical_name="synthetic_tech",
        surface_form="SynthTech",
        match_type=MatchType.EXACT,
        confidence=0.95
    )


@pytest.fixture
def synthetic_evidence_chunk() -> EvidenceChunk:
    """Generic synthetic evidence chunk fixture."""
    return EvidenceChunk(
        id="chunk_syn_01",
        text="Led backend development utilizing Synthetic Tech for scalable pipelines.",
        section=SectionType.EXPERIENCE,
        page=1,
        confidence=0.98,
        source_file="synthetic_doc_01.pdf"
    )


@pytest.fixture
def synthetic_resume(synthetic_skill: Skill, synthetic_evidence_chunk: EvidenceChunk) -> Resume:
    """Generic synthetic resume fixture without real candidate identity."""
    return Resume(
        candidate_id="cand_test_001",
        name="Candidate Alpha",
        source_file="resume_test_001.pdf",
        raw_text="Candidate Alpha\nExperience: Led backend development utilizing Synthetic Tech.",
        sections={
            SectionType.EXPERIENCE: "Led backend development utilizing Synthetic Tech.",
            SectionType.SKILLS: "Synthetic Tech, Python"
        },
        skills=[synthetic_skill],
        evidence_chunks=[synthetic_evidence_chunk]
    )


@pytest.fixture
def synthetic_jd(synthetic_requirement: Requirement) -> JobDescription:
    """Generic synthetic JD fixture."""
    return JobDescription(
        id="jd_test_001",
        title="Software Engineer - Synthetic Test",
        source_file="job_description_test.pdf",
        raw_text="Role: Software Engineer. Must have strong experience in Synthetic Tech.",
        requirements=[synthetic_requirement],
        required_skills=["synthetic_tech"],
        preferred_skills=[],
        responsibilities=["Develop backend services"],
        requirement_chunks=[]
    )


@pytest.fixture
def synthetic_evaluation(
    synthetic_skill: Skill,
    synthetic_requirement: Requirement,
    synthetic_evidence_chunk: EvidenceChunk
) -> CandidateEvaluation:
    """Generic synthetic evaluation dossier."""
    match = MatchEvidence(
        requirement=synthetic_requirement,
        evidence=synthetic_evidence_chunk,
        match_type=MatchType.EXACT,
        confidence=0.95,
        similarity=0.92
    )
    return CandidateEvaluation(
        candidate_id="cand_test_001",
        candidate_name="Candidate Alpha",
        scores=ScoreStructure(
            required_skill_coverage=1.0,
            semantic_requirement_alignment=0.88,
            contextual_lexical_relevance=0.80,
            preferred_skill_coverage=0.0,
            final_score=0.818
        ),
        matched_required=[synthetic_skill],
        matched_preferred=[],
        missing_required=[],
        semantic_matches=[match],
        keyword_matches=[match],
        evidence=[synthetic_evidence_chunk],
        rank=1
    )
