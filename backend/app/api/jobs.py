"""API routes for Job Description ingestion and retrieval."""

from __future__ import annotations

import time
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.store import get_store
from backend.core.pipeline import get_pipeline
from backend.models.document import JobDescription

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.post("/upload", response_model=JobDescription, status_code=status.HTTP_200_OK)
async def upload_job_description(file: UploadFile = File(...)) -> JobDescription:
    """Upload and parse a Job Description PDF document."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must not be empty.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format: Job Description must have final extension .pdf.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    pipeline = get_pipeline()
    store = get_store()

    doc_id = f"jd_{int(time.time() * 1000)}"
    try:
        jd = pipeline.parse_job_description(source=content, doc_id=doc_id)
        jd.source_file = file.filename
        store.save_job(jd)
        return jd
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse Job Description: {exc}",
        )


@router.get("/{job_id}", response_model=JobDescription, status_code=status.HTTP_200_OK)
async def get_job_description(job_id: str) -> JobDescription:
    """Retrieve structured requirements for an existing Job Description by ID."""
    store = get_store()
    jd = store.get_job(job_id)
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Description with ID '{job_id}' not found.",
        )
    return jd
