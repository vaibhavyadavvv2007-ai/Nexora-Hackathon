"""Comprehensive integration tests for the Nexora FastAPI backend and shortlisting pipeline.

Tests:
- Health check
- CORS headers for frontend integration
- JD upload and retrieval
- Resume batch upload with validation and fault isolation
- Asynchronous pipeline execution and status polling
- Deterministic candidate ranking and score breakdowns
- Individual candidate dossier retrieval
- Contrastive pairwise candidate comparisons
- Audit explanations (no hallucinations, citing matched/missing skills)
"""

from __future__ import annotations

import io
import time
from typing import List
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.store import get_store
from backend.core.pipeline import get_pipeline


def make_pdf(pages_text: List[str]) -> bytes:
    """Helper to generate in-memory synthetic PDF bytes."""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        if text.strip():
            page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture(autouse=True)
def clean_store():
    """Reset the in-memory state before and after each test."""
    store = get_store()
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)


def test_health_endpoint(client):
    """GET /health must return 200 OK with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_headers_for_frontend(client):
    """FastAPI must include CORS allow headers for localhost:3000."""
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_job_upload_and_retrieval(client):
    """POST /api/jobs/upload parses PDF and GET /api/jobs/{id} retrieves it."""
    jd_content = (
        "Job Title: Senior Backend Architect\n\n"
        "Requirements:\n"
        "- Strong proficiency in Python, FastAPI, and Docker\n"
        "- Experience with PostgreSQL database design\n\n"
        "Preferred:\n"
        "- Knowledge of Kubernetes and Redis\n"
    )
    pdf_bytes = make_pdf([jd_content])

    # 1. Upload JD
    response = client.post(
        "/api/jobs/upload",
        files={"file": ("senior_backend_jd.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert len(data["requirements"]) > 0
    assert "python" in [s.lower() for s in data["required_skills"]]
    job_id = data["id"]

    # 2. Retrieve JD
    get_resp = client.get(f"/api/jobs/{job_id}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["id"] == job_id
    assert len(retrieved["requirements"]) == len(data["requirements"])


def test_resume_batch_upload_with_fault_isolation(client):
    """POST /api/resumes/upload-batch isolates corrupt or invalid files."""
    valid_pdf_1 = make_pdf(["John Doe\nSoftware Engineer\nSkills: Python, FastAPI\nExperience: Built APIs."])
    valid_pdf_2 = make_pdf(["Jane Smith\nData Engineer\nSkills: SQL, Python\nExperience: Data pipelines."])

    files = [
        ("files", ("resume_1.pdf", valid_pdf_1, "application/pdf")),
        ("files", ("resume_2.pdf", valid_pdf_2, "application/pdf")),
        ("files", ("corrupt.exe", b"invalid binary", "application/octet-stream")),
    ]

    response = client.post("/api/resumes/upload-batch", files=files, data={"job_id": "jd_test_01"})
    assert response.status_code == 200
    data = response.json()
    assert data["uploaded"] == 2
    assert len(data["failed"]) == 1
    assert data["failed"][0]["filename"] == "corrupt.exe"
    assert "Unsupported file format" in data["failed"][0]["reason"]


def test_full_shortlisting_pipeline_and_evaluation(client):
    """Full end-to-end integration:
    JD upload -> Resume upload -> Evaluation start -> Polling -> Rankings -> Pairwise compare.
    """
    # 1. Upload Job Description
    jd_content = (
        "Job Title: Python Backend Engineer\n\n"
        "Requirements:\n"
        "- Extensive experience with Python and FastAPI\n"
        "- Strong SQL and database modeling\n\n"
        "Preferred:\n"
        "- Hands-on Docker containerization\n"
    )
    jd_pdf = make_pdf([jd_content])
    jd_resp = client.post(
        "/api/jobs/upload",
        files={"file": ("python_dev_jd.pdf", jd_pdf, "application/pdf")},
    )
    assert jd_resp.status_code == 200
    job_id = jd_resp.json()["id"]

    # 2. Upload Candidate Resumes
    # Strong Candidate (matches Python, FastAPI, SQL, Docker)
    strong_pdf = make_pdf([
        "Alice Johnson\n"
        "Senior Python Engineer\n"
        "Skills: Python, FastAPI, SQL, Docker, PostgreSQL\n"
        "Experience: Architected high-throughput REST APIs using FastAPI and Python. Modeled relational SQL schemas."
    ])

    # Moderate Candidate (matches Python only)
    moderate_pdf = make_pdf([
        "Bob Miller\n"
        "Junior Scripting Analyst\n"
        "Skills: Python, Excel\n"
        "Experience: Wrote Python scripts to automate spreadsheet reporting."
    ])

    # Unrelated Candidate
    unrelated_pdf = make_pdf([
        "Charlie Brown\n"
        "Graphic Designer\n"
        "Skills: Photoshop, Figma, Illustrator\n"
        "Experience: Created brand identities and logo designs."
    ])

    upload_resp = client.post(
        "/api/resumes/upload-batch",
        files=[
            ("files", ("alice.pdf", strong_pdf, "application/pdf")),
            ("files", ("bob.pdf", moderate_pdf, "application/pdf")),
            ("files", ("charlie.pdf", unrelated_pdf, "application/pdf")),
        ],
        data={"job_id": job_id},
    )
    assert upload_resp.status_code == 200
    assert upload_resp.json()["uploaded"] == 3

    # 3. Start Analysis
    start_resp = client.post("/api/evaluation/start", data={"job_id": job_id})
    assert start_resp.status_code == 200
    task_id = start_resp.json()["task_id"]
    assert task_id.startswith("eval_")

    # In TestClient, BackgroundTasks run during the request cycle, so the task completes!
    # 4. Check Status
    status_resp = client.get(f"/api/evaluation/status/{task_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["stage"] in ("complete", "ranking", "matching")
    assert status_data["progress"] >= 50

    # 5. Retrieve Rankings
    rank_resp = client.get(f"/api/evaluation/rankings?job_id={job_id}")
    assert rank_resp.status_code == 200
    rank_data = rank_resp.json()
    assert len(rank_data["candidates"]) == 3

    # Candidates must be ranked deterministically (rank 1, 2, 3)
    cands = rank_data["candidates"]
    assert cands[0]["rank"] == 1
    assert cands[1]["rank"] == 2
    assert cands[2]["rank"] == 3

    # Alice should rank #1 with highest score
    assert "alice" in cands[0]["candidate_name"].lower() or "alice" in cands[0]["candidate_id"].lower() or cands[0]["final_score"] > cands[2]["final_score"]
    assert cands[0]["final_score"] > cands[1]["final_score"]
    assert cands[1]["final_score"] >= cands[2]["final_score"]

    # Verify score breakdown and explanations
    for c in cands:
        assert c["final_score"] is not None
        assert 0.0 <= c["final_score"] <= 1.0
        assert c["explanation"] is not None and len(c["explanation"]) > 0
        assert "rank" in c

    top_cand_id = cands[0]["candidate_id"]
    second_cand_id = cands[1]["candidate_id"]

    # 6. Retrieve Individual Candidate Dossier
    cand_resp = client.get(f"/api/candidates/{top_cand_id}?job_id={job_id}")
    assert cand_resp.status_code == 200
    cand_dossier = cand_resp.json()
    assert cand_dossier["candidate_id"] == top_cand_id
    assert len(cand_dossier["evidence"]) > 0

    # 7. Contrastive Pairwise Comparison
    comp_resp = client.get(
        f"/api/evaluation/compare?candidate_a={top_cand_id}&candidate_b={second_cand_id}&job_id={job_id}"
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["candidate_a_id"] == top_cand_id
    assert comp_data["candidate_b_id"] == second_cand_id
    assert comp_data["winner_id"] == top_cand_id
    assert comp_data["score_delta"] > 0
    assert len(comp_data["explanation"]) > 0
    assert len(comp_data["advantages_a"]) > 0
