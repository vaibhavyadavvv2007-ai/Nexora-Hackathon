import pytest
from pydantic import ValidationError
from backend.models.enums import MatchType, RequirementType, SectionType
from backend.models.requirement import Requirement
from backend.models.skill import Skill
from backend.models.evidence import EvidenceChunk, MatchEvidence
from backend.models.document import JobDescription, Resume
from backend.models.evaluation import CandidateEvaluation, ScoreStructure


def test_requirement_valid(synthetic_requirement: Requirement):
    """Test Requirement model creates and holds fields correctly."""
    assert synthetic_requirement.id == "req_synthetic_01"
    assert synthetic_requirement.type == RequirementType.REQUIRED
    assert synthetic_requirement.critical is True
    assert synthetic_requirement.weight == 1.0


def test_requirement_invalid_type():
    """Test Requirement rejects invalid requirement type enum."""
    with pytest.raises(ValidationError):
        Requirement(
            id="req_inv",
            name="Invalid",
            type="invalid_type",  # type: ignore
            canonical_name="invalid",
            source_text="Invalid source text"
        )


def test_skill_confidence_valid(synthetic_skill: Skill):
    """Test Skill confidence within [0, 1]."""
    assert 0.0 <= synthetic_skill.confidence <= 1.0


@pytest.mark.parametrize("invalid_confidence", [-0.1, 1.01, 2.5, -10.0])
def test_skill_confidence_out_of_range(invalid_confidence: float):
    """Test Skill confidence validation fails when outside [0, 1]."""
    with pytest.raises(ValidationError) as exc_info:
        Skill(
            canonical_name="python",
            surface_form="Python",
            match_type=MatchType.EXACT,
            confidence=invalid_confidence
        )
    assert "confidence" in str(exc_info.value)


def test_evidence_chunk_valid(synthetic_evidence_chunk: EvidenceChunk):
    """Test EvidenceChunk fields and bounds."""
    assert synthetic_evidence_chunk.page >= 1
    assert 0.0 <= synthetic_evidence_chunk.confidence <= 1.0
    assert synthetic_evidence_chunk.section == SectionType.EXPERIENCE


@pytest.mark.parametrize("invalid_confidence", [-0.05, 1.2])
def test_evidence_chunk_confidence_bounds(invalid_confidence: float):
    """Test EvidenceChunk rejects out of bounds confidence."""
    with pytest.raises(ValidationError):
        EvidenceChunk(
            id="chunk_err",
            text="Testing out of bounds confidence.",
            section=SectionType.PROJECTS,
            page=1,
            confidence=invalid_confidence,
            source_file="test.pdf"
        )


def test_evidence_chunk_invalid_page():
    """Test EvidenceChunk rejects page numbers < 1."""
    with pytest.raises(ValidationError):
        EvidenceChunk(
            id="chunk_err",
            text="Invalid page.",
            page=0,
            source_file="test.pdf"
        )


def test_match_evidence_similarity_bounds(
    synthetic_requirement: Requirement,
    synthetic_evidence_chunk: EvidenceChunk
):
    """Test MatchEvidence rejects similarity outside [0, 1]."""
    # Valid
    match = MatchEvidence(
        requirement=synthetic_requirement,
        evidence=synthetic_evidence_chunk,
        match_type=MatchType.SEMANTIC_EXACT,
        confidence=0.9,
        similarity=0.85
    )
    assert match.similarity == 0.85

    # Out of bounds
    with pytest.raises(ValidationError):
        MatchEvidence(
            requirement=synthetic_requirement,
            evidence=synthetic_evidence_chunk,
            match_type=MatchType.SEMANTIC_EXACT,
            confidence=0.9,
            similarity=1.1
        )


def test_resume_model_composition(synthetic_resume: Resume):
    """Test Resume model includes expected sections, skills, and evidence chunks."""
    assert synthetic_resume.candidate_id == "cand_test_001"
    assert SectionType.EXPERIENCE in synthetic_resume.sections
    assert len(synthetic_resume.skills) == 1
    assert len(synthetic_resume.evidence_chunks) == 1


def test_job_description_model(synthetic_jd: JobDescription):
    """Test JobDescription model composition and defaults."""
    assert synthetic_jd.id == "jd_test_001"
    assert len(synthetic_jd.requirements) == 1
    assert "synthetic_tech" in synthetic_jd.required_skills


def test_score_structure_bounds():
    """Test ScoreStructure validates all metrics into [0, 1]."""
    valid = ScoreStructure(
        required_skill_coverage=0.8,
        semantic_requirement_alignment=0.75,
        contextual_lexical_relevance=0.6,
        preferred_skill_coverage=0.5,
        final_score=0.71
    )
    assert valid.final_score == 0.71

    with pytest.raises(ValidationError):
        ScoreStructure(required_skill_coverage=1.5)


def test_candidate_evaluation_model(synthetic_evaluation: CandidateEvaluation):
    """Test CandidateEvaluation schema completeness and round-trip serialization."""
    assert synthetic_evaluation.candidate_id == "cand_test_001"
    assert synthetic_evaluation.scores.final_score == 0.818
    assert synthetic_evaluation.rank == 1
    assert len(synthetic_evaluation.matched_required) == 1

    # Round-trip JSON serialization test
    json_data = synthetic_evaluation.model_dump_json()
    reloaded = CandidateEvaluation.model_validate_json(json_data)
    assert reloaded.candidate_id == synthetic_evaluation.candidate_id
    assert reloaded.scores.final_score == synthetic_evaluation.scores.final_score
