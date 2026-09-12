"""Phase 3 Structured Document Parsing Layer Behavioral Tests.

Covers all 16 required behavioral specifications:
 1. Required JD skill extraction.
 2. Preferred JD skill extraction.
 3. Responsibility extraction.
 4. JD source page preservation.
 5. Resume candidate-name extraction.
 6. Resume section normalization.
 7. Missing section fallback.
 8. Evidence chunk page preservation.
 9. Exact skill alias normalization.
10. PostgreSQL not becoming MongoDB.
11. Express.js remaining distinct from explicit Node.js.
12. Duplicate skill mention suppression.
13. Low-confidence section parsing.
14. Empty/poor resume input.
15. Full synthetic JD -> structured JobDescription.
16. Full synthetic resume -> structured Resume.
"""

import json
from pathlib import Path
from typing import List
import fitz
import pytest

from backend.core.normalization.skill_normalizer import SkillNormalizer
from backend.core.parsing import (
    DocumentParser,
    JobDescriptionParser,
    PDFExtractor,
    ResumeParser,
    SectionClassifier,
    inspect_document,
    inspect_job_description,
    inspect_resume,
)
from backend.core.exceptions import DocumentParsingError
from backend.models.document import JobDescription, Resume
from backend.models.skill import Skill
from backend.models.enums import (
    DocumentType,
    ExtractionQuality,
    ExtractionStatus,
    MatchType,
    RequirementType,
    SectionType,
)
from backend.models.pdf_extraction import PageExtraction, PDFExtractionResult, TextBlock


# ---------------------------------------------------------------------------
# Synthetic PDF Fixture Helpers
# ---------------------------------------------------------------------------

def make_pdf(pages_text: List[str]) -> bytes:
    """Generate in-memory PDF bytes with text on specified pages."""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        if text.strip():
            page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ---------------------------------------------------------------------------
# 1. Required JD skill extraction
# ---------------------------------------------------------------------------

def test_1_required_jd_skill_extraction():
    extractor = PDFExtractor()
    parser = JobDescriptionParser()

    jd_text = (
        "Job Title: Senior Backend Engineer\n\n"
        "Requirements:\n"
        "- Strong proficiency in Python and FastAPI\n"
        "- Hands-on experience with Docker containerization\n"
    )
    pdf_bytes = make_pdf([jd_text])
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.JOB_DESCRIPTION)
    jd = parser.parse(extraction, jd_id="jd_req_01")

    # Canonical source of truth is requirements[]
    assert len(jd.requirements) >= 3
    req_canonicals = [r.canonical_name for r in jd.requirements]
    assert "python" in req_canonicals
    assert "fastapi" in req_canonicals
    assert "docker" in req_canonicals

    for r in jd.requirements:
        assert r.type == RequirementType.REQUIRED
        assert r.critical is True

    # Synchronized required_skills
    assert "python" in jd.required_skills
    assert "fastapi" in jd.required_skills
    assert "docker" in jd.required_skills


# ---------------------------------------------------------------------------
# 2. Preferred JD skill extraction
# ---------------------------------------------------------------------------

def test_2_preferred_jd_skill_extraction():
    extractor = PDFExtractor()
    parser = JobDescriptionParser()

    jd_text = (
        "Position: Cloud Architect\n\n"
        "Preferred Qualifications:\n"
        "- Experience with Kubernetes cluster orchestration\n"
        "- Familiarity with Redis caching\n"
        "- Knowledge of AWS cloud infrastructure\n"
    )
    pdf_bytes = make_pdf([jd_text])
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.JOB_DESCRIPTION)
    jd = parser.parse(extraction, jd_id="jd_pref_01")

    pref_reqs = [r for r in jd.requirements if r.type == RequirementType.PREFERRED]
    assert len(pref_reqs) >= 3

    canonicals = [r.canonical_name for r in pref_reqs]
    assert "kubernetes" in canonicals
    assert "redis" in canonicals
    assert "aws" in canonicals

    for r in pref_reqs:
        assert r.critical is False

    assert "kubernetes" in jd.preferred_skills
    assert "redis" in jd.preferred_skills
    assert "aws" in jd.preferred_skills


# ---------------------------------------------------------------------------
# 3. Responsibility extraction
# ---------------------------------------------------------------------------

def test_3_responsibility_extraction():
    extractor = PDFExtractor()
    parser = JobDescriptionParser()

    jd_text = (
        "Job Title: Lead Systems Developer\n\n"
        "Responsibilities:\n"
        "- Design high-throughput microservices using FastAPI\n"
        "- Mentor junior software engineers on the team\n"
        "- Collaborate with product managers on product roadmap\n"
    )
    pdf_bytes = make_pdf([jd_text])
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.JOB_DESCRIPTION)
    jd = parser.parse(extraction, jd_id="jd_resp_01")

    assert len(jd.responsibilities) >= 3
    assert any("microservices" in resp for resp in jd.responsibilities)
    assert any("Mentor" in resp for resp in jd.responsibilities)

    resp_reqs = [r for r in jd.requirements if r.type == RequirementType.RESPONSIBILITY]
    assert len(resp_reqs) >= 3


# ---------------------------------------------------------------------------
# 4. JD source page preservation
# ---------------------------------------------------------------------------

def test_4_jd_source_page_preservation():
    extractor = PDFExtractor()
    parser = JobDescriptionParser()

    page_1 = (
        "Job Title: Full Stack Lead\n\n"
        "Requirements:\n"
        "- Strong proficiency in Python and PostgreSQL\n"
    )
    page_2 = (
        "Preferred Qualifications:\n"
        "- Experience with Docker and Kubernetes\n"
    )
    pdf_bytes = make_pdf([page_1, page_2])
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.JOB_DESCRIPTION)
    jd = parser.parse(extraction, jd_id="jd_pages_01")

    # Requirements from page 1 must have source_page == 1
    p1_reqs = [r for r in jd.requirements if r.canonical_name in ("python", "postgresql")]
    assert len(p1_reqs) >= 2
    for r in p1_reqs:
        assert r.source_page == 1

    # Requirements from page 2 must have source_page == 2
    p2_reqs = [r for r in jd.requirements if r.canonical_name in ("docker", "kubernetes")]
    assert len(p2_reqs) >= 2
    for r in p2_reqs:
        assert r.source_page == 2, f"Expected page 2, got {r.source_page}"

    # Requirement chunks must also preserve page numbers
    p2_chunks = [c for c in jd.requirement_chunks if c.page == 2]
    assert len(p2_chunks) > 0


# ---------------------------------------------------------------------------
# 5. Resume candidate-name extraction
# ---------------------------------------------------------------------------

def test_5_resume_candidate_name_extraction():
    extractor = PDFExtractor()
    parser = ResumeParser()

    # Normal resume with clear name
    resume_text = (
        "Jane Doe\n"
        "jane.doe@example.com | 555-0199 | San Francisco, CA\n\n"
        "Professional Summary\n"
        "Passionate full-stack developer with 5 years experience.\n"
    )
    pdf_bytes = make_pdf([resume_text])
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.RESUME)
    resume = parser.parse(extraction, candidate_id="cand_001")
    assert resume.name == "Jane Doe"

    # Name with middle initial or hyphen
    resume_text_2 = (
        "John A. Smith\n"
        "john.smith@example.com\n\n"
        "Technical Skills\n"
        "Python, Docker\n"
    )
    pdf_bytes_2 = make_pdf([resume_text_2])
    extraction_2 = extractor.extract(pdf_bytes_2, document_type=DocumentType.RESUME)
    resume_2 = parser.parse(extraction_2, candidate_id="cand_002")
    assert resume_2.name == "John A. Smith"

    # Fallback when no reliable name exists
    anon_text = "555-123-4567 | info@company.com\nhttps://github.com/myprofile\n"
    pdf_bytes_anon = make_pdf([anon_text])
    extraction_anon = extractor.extract(pdf_bytes_anon, document_type=DocumentType.RESUME)
    resume_anon = parser.parse(extraction_anon, candidate_id="cand_anon")
    assert resume_anon.name == "Candidate_cand_anon"


# ---------------------------------------------------------------------------
# 6. Resume section normalization
# ---------------------------------------------------------------------------

def test_6_resume_section_normalization():
    extractor = PDFExtractor()
    parser = ResumeParser()

    resume_text = (
        "Alice Walker\n\n"
        "Professional Summary\n"
        "Senior software engineer focused on resilient backend systems.\n\n"
        "Technical Skills\n"
        "Python, FastAPI, Docker, PostgreSQL\n\n"
        "Work Experience\n"
        "- Built asynchronous data ingestion pipelines with Python\n"
        "- Deployed microservices using Docker\n\n"
        "Academic Projects\n"
        "- Created distributed cache using Redis\n\n"
        "Academic Background\n"
        "- B.S. in Computer Science, University of California\n"
    )
    pdf_bytes = make_pdf([resume_text])
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.RESUME)
    resume = parser.parse(extraction, candidate_id="cand_alice")

    assert SectionType.SUMMARY in resume.sections
    assert SectionType.SKILLS in resume.sections
    assert SectionType.EXPERIENCE in resume.sections
    assert SectionType.PROJECTS in resume.sections
    assert SectionType.EDUCATION in resume.sections

    assert len(resume.experience) >= 2
    assert len(resume.projects) >= 1
    assert len(resume.education) >= 1
    assert resume.summary is not None
    assert "resilient backend" in resume.summary


# ---------------------------------------------------------------------------
# 7. Missing section fallback
# ---------------------------------------------------------------------------

def test_7_missing_section_fallback():
    extractor = PDFExtractor()
    parser = ResumeParser()

    # Resume with no section headers at all
    unstructured_text = (
        "Alex Mercer\n"
        "Self-taught developer skilled in Python and React.\n"
        "Worked on various freelancing contracts building REST APIs.\n"
        "Enjoys open source contribution and continuous learning.\n"
    )
    pdf_bytes = make_pdf([unstructured_text])
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.RESUME)

    # Must not raise an exception
    resume = parser.parse(extraction, candidate_id="cand_unstructured")

    assert resume.candidate_id == "cand_unstructured"
    assert len(resume.evidence_chunks) > 0
    # Raw text preserved
    assert "Alex Mercer" in resume.raw_text
    # Skills still extracted from freeform text
    skill_names = [s.canonical_name for s in resume.skills]
    assert "python" in skill_names
    assert "react" in skill_names


# ---------------------------------------------------------------------------
# 8. Evidence chunk page preservation
# ---------------------------------------------------------------------------

def test_8_evidence_chunk_page_preservation():
    extractor = PDFExtractor()
    parser = ResumeParser()

    p1 = (
        "Bob Builder\n\n"
        "Skills:\n"
        "Python, React, TypeScript\n"
    )
    p2 = (
        "Experience:\n"
        "- Developed web applications using React and TypeScript\n"
        "- Maintained cloud infrastructure using Docker\n"
    )
    p3 = (
        "Education:\n"
        "- Master of Science in Software Engineering, 2022\n"
    )

    pdf_bytes = make_pdf([p1, p2, p3])
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.RESUME)
    resume = parser.parse(extraction, candidate_id="cand_bob")

    # Verify chunks exist on pages 1, 2, and 3
    pages_represented = {chunk.page for chunk in resume.evidence_chunks}
    assert 1 in pages_represented
    assert 2 in pages_represented
    assert 3 in pages_represented

    p2_chunks = [c for c in resume.evidence_chunks if c.page == 2]
    assert len(p2_chunks) >= 2
    assert any("Developed web applications" in c.text for c in p2_chunks)

    p3_chunks = [c for c in resume.evidence_chunks if c.page == 3]
    assert len(p3_chunks) >= 1
    assert any("Master of Science" in c.text for c in p3_chunks)


# ---------------------------------------------------------------------------
# 9. Exact skill alias normalization
# ---------------------------------------------------------------------------

def test_9_exact_skill_alias_normalization():
    normalizer = SkillNormalizer()

    alias_cases = [
        ("js", "javascript"),
        ("ecmascript", "javascript"),
        ("react.js", "react"),
        ("reactjs", "react"),
        ("node", "node.js"),
        ("nodejs", "node.js"),
        ("node js", "node.js"),
        ("express", "express.js"),
        ("expressjs", "express.js"),
        ("postgres", "postgresql"),
        ("psql", "postgresql"),
        ("mongo", "mongodb"),
        ("mongo db", "mongodb"),
        ("rest apis", "rest api"),
        ("restful api", "rest api"),
        ("k8s", "kubernetes"),
        ("ts", "typescript"),
    ]

    for raw_alias, expected_canonical in alias_cases:
        skill = normalizer.normalize_token(raw_alias)
        assert skill is not None, f"Failed to normalize alias: '{raw_alias}'"
        assert skill.canonical_name == expected_canonical, (
            f"Alias '{raw_alias}' resolved to '{skill.canonical_name}', expected '{expected_canonical}'"
        )
        assert skill.match_type in (MatchType.EXACT, MatchType.ALIAS)


# ---------------------------------------------------------------------------
# 10. PostgreSQL not becoming MongoDB
# ---------------------------------------------------------------------------

def test_10_postgresql_not_becoming_mongodb():
    normalizer = SkillNormalizer()

    postgres_skill = normalizer.normalize_token("PostgreSQL")
    assert postgres_skill is not None
    assert postgres_skill.canonical_name == "postgresql"
    assert postgres_skill.canonical_name != "mongodb"

    alias_pg = normalizer.normalize_token("Postgres")
    assert alias_pg is not None
    assert alias_pg.canonical_name == "postgresql"
    assert alias_pg.canonical_name != "mongodb"

    mongo_skill = normalizer.normalize_token("MongoDB")
    assert mongo_skill is not None
    assert mongo_skill.canonical_name == "mongodb"
    assert mongo_skill.canonical_name != "postgresql"

    alias_mongo = normalizer.normalize_token("Mongo")
    assert alias_mongo is not None
    assert alias_mongo.canonical_name == "mongodb"
    assert alias_mongo.canonical_name != "postgresql"

    sql_skill = normalizer.normalize_token("SQL")
    assert sql_skill is not None
    assert sql_skill.canonical_name == "sql"
    assert sql_skill.canonical_name not in ("postgresql", "mongodb")


# ---------------------------------------------------------------------------
# 11. Express.js remaining distinct from explicit Node.js
# ---------------------------------------------------------------------------

def test_11_express_distinct_from_nodejs():
    normalizer = SkillNormalizer()

    text = "Developed REST APIs using Express.js on a Node.js runtime."
    skills = normalizer.extract_skills_from_text(text)
    canonicals = [s.canonical_name for s in skills]

    assert "express.js" in canonicals
    assert "node.js" in canonicals

    express_skill = [s for s in skills if s.canonical_name == "express.js"][0]
    node_skill = [s for s in skills if s.canonical_name == "node.js"][0]

    assert express_skill.canonical_name != node_skill.canonical_name
    assert express_skill.surface_form.lower() in ("express.js", "express")
    assert node_skill.surface_form.lower() in ("node.js", "node")


# ---------------------------------------------------------------------------
# 12. Duplicate skill mention suppression
# ---------------------------------------------------------------------------

def test_12_duplicate_skill_mention_suppression():
    extractor = PDFExtractor()
    parser = ResumeParser()

    resume_text = (
        "Carol Danvers\n\n"
        "Skills:\n"
        "Python, Docker\n\n"
        "Experience:\n"
        "- Built backend service in Python\n"
        "- Optimized Python multiprocessing pipelines\n"
        "- Mentored developers in advanced Python techniques\n"
    )
    pdf_bytes = make_pdf([resume_text])
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.RESUME)
    resume = parser.parse(extraction, candidate_id="cand_carol")

    python_mentions = [s for s in resume.skills if s.canonical_name == "python"]
    assert len(python_mentions) == 1, (
        f"Expected exactly 1 canonical 'python' skill after suppression, found {len(python_mentions)}"
    )

    # However, evidence chunks must preserve all occurrences for ML matching
    python_chunks = [c for c in resume.evidence_chunks if "Python" in c.text]
    assert len(python_chunks) >= 3


# ---------------------------------------------------------------------------
# 13. Low-confidence section parsing
# ---------------------------------------------------------------------------

def test_13_low_confidence_section_parsing():
    raw_block = TextBlock(
        text="Miscellaneous details about personal hobbies and open source adventures.",
        page_number=1,
        bbox=(50.0, 50.0, 300.0, 70.0),
    )
    extraction = PDFExtractionResult(
        source_file="unknown_resume.pdf",
        document_type=DocumentType.RESUME,
        page_count=1,
        pages=[
            PageExtraction(
                page_number=1,
                text="Miscellaneous details about personal hobbies and open source adventures.",
                character_count=73,
                text_blocks=[raw_block],
            )
        ],
        text="Miscellaneous details about personal hobbies and open source adventures.",
        text_blocks=[raw_block],
        character_count=73,
        extraction_status=ExtractionStatus.SUCCESS,
        extraction_quality=ExtractionQuality.HIGH,
    )

    parser = ResumeParser()
    resume = parser.parse(extraction, candidate_id="cand_low_conf")

    assert resume.candidate_id == "cand_low_conf"
    assert len(resume.evidence_chunks) == 1
    # Fallback confidence should be lowered
    assert resume.evidence_chunks[0].confidence <= 0.95


# ---------------------------------------------------------------------------
# 14. Empty/poor resume input
# ---------------------------------------------------------------------------

def test_14_empty_poor_resume_input():
    extraction = PDFExtractionResult(
        source_file="empty_resume.pdf",
        document_type=DocumentType.RESUME,
        page_count=1,
        pages=[
            PageExtraction(
                page_number=1,
                text="",
                character_count=0,
                text_blocks=[],
            )
        ],
        text="",
        text_blocks=[],
        character_count=0,
        extraction_status=ExtractionStatus.LOW_QUALITY,
        extraction_quality=ExtractionQuality.EMPTY,
    )

    parser = ResumeParser()
    resume = parser.parse(extraction, candidate_id="cand_empty")

    assert resume.candidate_id == "cand_empty"
    assert resume.name == "Candidate_cand_empty"
    assert resume.skills == []
    assert resume.experience == []
    assert resume.projects == []
    assert resume.evidence_chunks == []


# ---------------------------------------------------------------------------
# 15. Full synthetic JD -> structured JobDescription
# ---------------------------------------------------------------------------

def test_15_full_synthetic_jd_to_structured_job_description(tmp_path):
    jd_content = (
        "Job Title: Senior Backend AI Engineer\n\n"
        "Responsibilities:\n"
        "- Build scalable Python APIs with FastAPI\n"
        "- Implement continuous delivery pipelines with Docker\n\n"
        "Requirements:\n"
        "- 4+ years software development experience with Python\n"
        "- Experience with PostgreSQL database design\n\n"
        "Preferred Qualifications:\n"
        "- Knowledge of Kubernetes cluster operations\n"
        "- Hands-on experience with Redis\n"
    )
    pdf_bytes = make_pdf([jd_content])
    pdf_path = tmp_path / "synthetic_jd.pdf"
    pdf_path.write_bytes(pdf_bytes)

    doc_parser = DocumentParser()
    jd: JobDescription = doc_parser.parse_job_description(pdf_path, doc_id="jd_synth_01")

    assert jd.id == "jd_synth_01"
    assert "Backend" in jd.role_title
    assert len(jd.requirements) >= 4
    assert len(jd.responsibilities) >= 2
    assert "python" in jd.required_skills
    assert "postgresql" in jd.required_skills
    assert "kubernetes" in jd.preferred_skills
    assert "redis" in jd.preferred_skills
    assert len(jd.requirement_chunks) >= 6

    # Test inspection JSON generation
    json_str = inspect_job_description(pdf_path, jd_id="jd_synth_01")
    parsed_json = json.loads(json_str)
    assert parsed_json["id"] == "jd_synth_01"
    assert "requirements" in parsed_json
    assert len(parsed_json["requirements"]) >= 4


# ---------------------------------------------------------------------------
# 16. Full synthetic resume -> structured Resume
# ---------------------------------------------------------------------------

def test_16_full_synthetic_resume_to_structured_resume(tmp_path):
    p1 = (
        "Diana Prince\n"
        "diana@example.com | 555-0100\n\n"
        "Professional Summary\n"
        "Full-stack engineer with 6 years building cloud-native systems.\n\n"
        "Technical Skills\n"
        "Python, FastAPI, React, Docker, PostgreSQL\n"
    )
    p2 = (
        "Work Experience\n"
        "- Architected high-performance FastAPI backends\n"
        "- Containerized application workflows using Docker\n\n"
        "Education\n"
        "- B.S. Computer Science, Gotham University\n"
    )

    pdf_bytes = make_pdf([p1, p2])
    pdf_path = tmp_path / "synthetic_resume.pdf"
    pdf_path.write_bytes(pdf_bytes)

    doc_parser = DocumentParser()
    resume: Resume = doc_parser.parse_resume(pdf_path, candidate_id="cand_diana")

    assert resume.candidate_id == "cand_diana"
    assert resume.name == "Diana Prince"
    assert SectionType.SKILLS in resume.sections
    assert SectionType.EXPERIENCE in resume.sections
    assert SectionType.EDUCATION in resume.sections

    skill_canonicals = [s.canonical_name for s in resume.skills]
    assert "python" in skill_canonicals
    assert "fastapi" in skill_canonicals
    assert "docker" in skill_canonicals
    assert "postgresql" in skill_canonicals

    assert len(resume.experience) >= 2
    assert len(resume.education) >= 1
    assert len(resume.evidence_chunks) >= 5

    # Test inspection JSON generation
    json_str = inspect_resume(pdf_path, candidate_id="cand_diana")
    parsed_json = json.loads(json_str)
    assert parsed_json["candidate_id"] == "cand_diana"
    assert parsed_json["name"] == "Diana Prince"
    assert len(parsed_json["evidence_chunks"]) >= 5


# ---------------------------------------------------------------------------
# 17. Developer JSON Inspector Utility
# ---------------------------------------------------------------------------

def test_17_inspector_utility(tmp_path):
    # Test inspect_document routing for JD
    jd_bytes = make_pdf(["Job Title: Data Engineer\nRequirements:\n- Python, SQL"])
    jd_path = tmp_path / "test_jd.pdf"
    jd_path.write_bytes(jd_bytes)

    jd_json = inspect_document(jd_path, doc_type="job_description", doc_id="jd_insp")
    data_jd = json.loads(jd_json)
    assert data_jd["id"] == "jd_insp"
    assert "python" in data_jd["required_skills"]

    # Test inspect_document routing for Resume
    res_bytes = make_pdf(["Bruce Wayne\nSkills:\nPython, Linux"])
    res_path = tmp_path / "test_res.pdf"
    res_path.write_bytes(res_bytes)

    res_json = inspect_document(res_path, doc_type=DocumentType.RESUME, doc_id="cand_bruce")
    data_res = json.loads(res_json)
    assert data_res["candidate_id"] == "cand_bruce"
    assert data_res["name"] == "Bruce Wayne"

    # Test invalid doc type error
    with pytest.raises(ValueError, match="Unsupported document type"):
        inspect_document(res_path, doc_type="invalid_type")


# ---------------------------------------------------------------------------
# 18. Critical Fix C1: Failed JD extraction is rejected
# ---------------------------------------------------------------------------

def test_18_failed_jd_extraction_rejected():
    failed_extraction = PDFExtractionResult(
        source_file="corrupt_job.pdf",
        document_type=DocumentType.JOB_DESCRIPTION,
        page_count=0,
        pages=[],
        text="",
        text_blocks=[],
        character_count=0,
        extraction_status=ExtractionStatus.FAILED,
        extraction_quality=ExtractionQuality.CORRUPTED,
        warnings=["Failed to open document: Corrupt PDF header"],
    )

    parser = JobDescriptionParser()
    with pytest.raises(DocumentParsingError) as exc_info:
        parser.parse(failed_extraction)

    assert exc_info.value.source_file == "corrupt_job.pdf"
    assert exc_info.value.extraction_status == ExtractionStatus.FAILED
    assert "Corrupt PDF header" in exc_info.value.reason


# ---------------------------------------------------------------------------
# 19. Critical Fix C1: Failed Resume extraction is rejected
# ---------------------------------------------------------------------------

def test_19_failed_resume_extraction_rejected():
    failed_extraction = PDFExtractionResult(
        source_file="corrupt_candidate.pdf",
        document_type=DocumentType.RESUME,
        page_count=0,
        pages=[],
        text="",
        text_blocks=[],
        character_count=0,
        extraction_status=ExtractionStatus.FAILED,
        extraction_quality=ExtractionQuality.CORRUPTED,
        warnings=["PyMuPDF extraction failed: damaged stream"],
    )

    parser = ResumeParser()
    with pytest.raises(DocumentParsingError) as exc_info:
        parser.parse(failed_extraction)

    assert exc_info.value.source_file == "corrupt_candidate.pdf"
    assert exc_info.value.extraction_status == ExtractionStatus.FAILED
    assert "damaged stream" in exc_info.value.reason


# ---------------------------------------------------------------------------
# 20. Critical Fix C1: No CandidateEvaluation can be created from failed doc
# ---------------------------------------------------------------------------

def test_20_no_candidate_evaluation_from_failed_document():
    failed_extraction = PDFExtractionResult(
        source_file="unreadable.pdf",
        document_type=DocumentType.RESUME,
        page_count=0,
        pages=[],
        text="",
        text_blocks=[],
        character_count=0,
        extraction_status=ExtractionStatus.FAILED,
        extraction_quality=ExtractionQuality.CORRUPTED,
    )

    parser = ResumeParser()
    with pytest.raises(DocumentParsingError):
        # Must fail fast and reject document creation
        parser.parse(failed_extraction, candidate_id="cand_failed")


# ---------------------------------------------------------------------------
# 21. Critical Fix C2: Unknown skill capture
# ---------------------------------------------------------------------------

def test_21_unknown_skill_capture():
    normalizer = SkillNormalizer()
    parser = ResumeParser(skill_normalizer=normalizer)

    resume_text = (
        "Grace Hopper\n\n"
        "Technical Skills:\n"
        "Python, Docker, Terraform, Airflow, Firebase, Rust, Spring Boot, .NET\n"
    )
    pdf_bytes = make_pdf([resume_text])
    extractor = PDFExtractor()
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.RESUME)
    resume = parser.parse(extraction, candidate_id="cand_grace")

    skill_canonicals = {s.canonical_name: s for s in resume.skills}

    # Curated skills must be exact/alias
    assert "python" in skill_canonicals
    assert skill_canonicals["python"].match_type == MatchType.EXACT

    assert "docker" in skill_canonicals
    assert skill_canonicals["docker"].match_type == MatchType.EXACT

    # Unknown technologies must NOT disappear
    unknown_expected = ["terraform", "airflow", "firebase", "rust", "spring_boot", ".net"]
    for tech in unknown_expected:
        assert tech in skill_canonicals, f"Unknown technology '{tech}' was dropped!"
        tech_skill = skill_canonicals[tech]
        # Unknown skills must NOT be labeled exact
        assert tech_skill.match_type != MatchType.EXACT
        assert tech_skill.match_type == MatchType.LOW_CONFIDENCE
        assert tech_skill.confidence <= 0.75

    # Direct normalize_token check for unknown tokens
    token_tf = normalizer.normalize_token("Terraform")
    assert token_tf is not None
    assert token_tf.canonical_name == "terraform"
    assert token_tf.match_type == MatchType.LOW_CONFIDENCE


# ---------------------------------------------------------------------------
# 22. Critical Fix C3: Distinguish skill from contextual requirements
# ---------------------------------------------------------------------------

def test_22_non_skill_jd_requirement_exclusion():
    jd_text = (
        "Job Title: Senior Backend AI Engineer\n\n"
        "Requirements:\n"
        "- 4+ years of software development experience\n"
        "- Bachelor's degree in Computer Science\n"
        "- Strong proficiency in Python and PostgreSQL\n"
        "- Excellent communication and interpersonal skills\n"
    )
    pdf_bytes = make_pdf([jd_text])
    extractor = PDFExtractor()
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.JOB_DESCRIPTION)
    parser = JobDescriptionParser()
    jd = parser.parse(extraction, jd_id="jd_c3_test")

    # All 4 requirements must be preserved in requirements[]
    assert len(jd.requirements) >= 4

    # Technical skill requirements have is_skill_matchable = True
    skill_reqs = [r for r in jd.requirements if r.is_skill_matchable]
    skill_keys = {r.canonical_name for r in skill_reqs}
    assert "python" in skill_keys
    assert "postgresql" in skill_keys

    # Contextual non-skill requirements have is_skill_matchable = False
    context_reqs = [r for r in jd.requirements if not r.is_skill_matchable]
    assert len(context_reqs) >= 2
    for cr in context_reqs:
        assert cr.is_skill_matchable is False

    # required_skills must ONLY contain skill-matchable requirements
    assert "python" in jd.required_skills
    assert "postgresql" in jd.required_skills
    # Non-skill slugs must NOT contaminate required_skills
    for s in jd.required_skills:
        assert "4+" not in s
        assert "years" not in s
        assert "bachelor" not in s
        assert "communication" not in s


# ---------------------------------------------------------------------------
# 23. Medium Fix M2: Wrapped bullet joins into one coherent evidence chunk
# ---------------------------------------------------------------------------

def test_23_wrapped_bullet_joins_into_one_evidence_chunk():
    # Synthetic resume with a bullet wrapped across two lines inside a block
    block_text = (
        "Alan Turing\n\n"
        "Work Experience\n"
        "- Built asynchronous data\n"
        "ingestion pipelines with Python"
    )
    pdf_bytes = make_pdf([block_text])
    extractor = PDFExtractor()
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.RESUME)
    parser = ResumeParser()
    resume = parser.parse(extraction, candidate_id="cand_alan")

    # Find the evidence chunk corresponding to the experience bullet
    exp_chunks = [c for c in resume.evidence_chunks if "Built asynchronous data" in c.text]
    assert len(exp_chunks) == 1, (
        f"Expected exactly 1 coherent chunk for wrapped bullet, found {len(exp_chunks)}"
    )
    chunk = exp_chunks[0]
    assert "Built asynchronous data ingestion pipelines with Python" in chunk.text


# ---------------------------------------------------------------------------
# 24. Medium Fix M3: React Native distinct from React
# ---------------------------------------------------------------------------

def test_24_react_native_distinct_from_react():
    normalizer = SkillNormalizer()

    rn_skill = normalizer.normalize_token("React Native")
    react_skill = normalizer.normalize_token("React")

    assert rn_skill is not None
    assert react_skill is not None
    assert rn_skill.canonical_name == "react native"
    assert react_skill.canonical_name == "react"
    assert rn_skill.canonical_name != react_skill.canonical_name

    # In combined text
    text = "Full-stack developer experienced in React Native for iOS/Android and React for web."
    skills = normalizer.extract_skills_from_text(text)
    canonicals = {s.canonical_name for s in skills}
    assert "react native" in canonicals
    assert "react" in canonicals


# ---------------------------------------------------------------------------
# 25. Medium Fix M4: Deterministic section priority deduplication
# ---------------------------------------------------------------------------

def test_25_section_priority_deduplication():
    normalizer = SkillNormalizer()

    # Skill appearing in both SKILLS section and EXPERIENCE section
    skill_in_skills = Skill(
        canonical_name="python",
        surface_form="Python",
        match_type=MatchType.EXACT,
        confidence=1.0,
        section=SectionType.SKILLS,
        source_page=1,
    )
    skill_in_exp = Skill(
        canonical_name="python",
        surface_form="Python",
        match_type=MatchType.EXACT,
        confidence=0.95,
        section=SectionType.EXPERIENCE,
        source_page=2,
    )

    # Experience (priority 5) must take precedence over Skills (priority 4)
    deduped = normalizer.deduplicate_skills([skill_in_skills, skill_in_exp])
    assert len(deduped) == 1
    assert deduped[0].section == SectionType.EXPERIENCE


# ---------------------------------------------------------------------------
# 26. Medium Fix M5: Missing role title does not fabricate "Software Engineer"
# ---------------------------------------------------------------------------

def test_26_missing_role_title_does_not_fabricate_software_engineer():
    # JD with company background and requirements, but no role title
    jd_text = (
        "About the Company:\n"
        "We are an AI lab building next-generation search systems.\n\n"
        "Requirements:\n"
        "- Strong proficiency in Python and FastAPI\n"
    )
    pdf_bytes = make_pdf([jd_text])
    extractor = PDFExtractor()
    extraction = extractor.extract(pdf_bytes, document_type=DocumentType.JOB_DESCRIPTION)
    parser = JobDescriptionParser()
    jd = parser.parse(extraction, jd_id="jd_no_title")

    # Must NOT fabricate "Software Engineer"
    assert jd.role_title != "Software Engineer"
    assert jd.role_title == ""
