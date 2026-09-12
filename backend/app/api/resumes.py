"""API routes for batch resume document upload and validation."""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, File, Form, UploadFile, status

from backend.app.schemas.evaluation import FailedUploadItem, ResumeBatchUploadResponse
from backend.app.store import get_store

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


@router.post(
    "/upload-batch",
    response_model=ResumeBatchUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_resumes_batch(
    files: List[UploadFile] = File(...),
    job_id: Optional[str] = Form(None),
) -> ResumeBatchUploadResponse:
    """Upload and store a batch of candidate resume documents."""
    store = get_store()

    # If job_id not provided in form, resolve against active stored JD
    target_job_id = job_id
    if not target_job_id:
        active_jd = store.get_job()
        target_job_id = active_jd.id if active_jd else "default_job"

    uploaded_names: List[str] = []
    failed_items: List[FailedUploadItem] = []

    for file in files:
        filename = file.filename or "unknown.pdf"

        # Check format
        lower_name = filename.lower()
        if not (lower_name.endswith(".pdf") or lower_name.endswith(".docx") or lower_name.endswith(".txt")):
            failed_items.append(
                FailedUploadItem(
                    filename=filename,
                    reason="Unsupported file format. Accepted: .pdf, .docx, .txt",
                )
            )
            continue

        try:
            content = await file.read()
            if not content:
                failed_items.append(
                    FailedUploadItem(filename=filename, reason="File is empty (0 bytes).")
                )
                continue

            store.save_resume_file(
                job_id=target_job_id,
                filename=filename,
                content=content,
                content_type=file.content_type or "application/pdf",
            )
            uploaded_names.append(filename)
        except Exception as exc:
            failed_items.append(
                FailedUploadItem(filename=filename, reason=f"Failed to read file: {exc}")
            )

    return ResumeBatchUploadResponse(
        uploaded=len(uploaded_names),
        failed=failed_items,
        job_id=target_job_id,
        files=uploaded_names,
    )
