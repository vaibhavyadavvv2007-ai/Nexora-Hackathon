"""API routes for candidate evaluation pipeline, status polling, rankings, and pairwise comparisons."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from typing import List, Optional
import uuid
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile, status

from backend.app.schemas.evaluation import (
    EvaluationResultResponse,
    FailedUploadItem,
    PairwiseComparisonResponse,
    ProcessingStatusResponse,
    StartAnalysisResponse,
)
from backend.app.store import get_store
from backend.core.explanations.explainer import TemplateExplainer
from backend.core.pipeline import get_pipeline
from backend.core.ranking import EvaluationMode

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])
_EXECUTOR = ThreadPoolExecutor(max_workers=4)


def _run_pipeline_worker(job_id: str, task_id: str) -> None:
    """Worker function executed in background to run shortlisting pipeline."""
    store = get_store()
    pipeline = get_pipeline()

    jd = store.get_job(job_id)
    if not jd:
        store.update_task(
            task_id=task_id,
            stage="error",
            progress=0,
            message=f"Job Description '{job_id}' not found.",
            error=f"Job Description '{job_id}' not found.",
        )
        return

    # Retrieve all raw resume files stored for this job
    file_records = store.get_resume_files(job_id)
    if not file_records:
        # Check if we already have parsed resumes
        parsed_resumes = store.get_parsed_resumes(job_id)
        if parsed_resumes:
            # Directly evaluate and rank already parsed resumes
            store.update_task(
                task_id=task_id,
                stage="ranking",
                progress=70,
                message="Evaluating parsed candidates...",
                ranking_status="computing",
            )
            result = pipeline.evaluate_and_rank(jd, parsed_resumes)
            store.save_evaluation_result(result)
            store.update_task(
                task_id=task_id,
                stage="complete",
                progress=100,
                message=f"Evaluation complete. Ranked {len(result.candidates)} candidates.",
                ranking_status="complete",
            )
            return
        else:
            store.update_task(
                task_id=task_id,
                stage="complete",
                progress=100,
                message="No resumes to process.",
                resumes_total=0,
                resumes_processed=0,
            )
            return

    # Prepare inputs: list of (filename, bytes)
    inputs = [(rec.filename, rec.content) for rec in file_records]

    try:
        pipeline.execute(
            job_description=jd,
            resume_inputs=inputs,
            task_id=task_id,
            mode=EvaluationMode.COMBINED,
        )
    except Exception as exc:
        store.update_task(
            task_id=task_id,
            stage="error",
            progress=0,
            message=f"Pipeline failure: {exc}",
            error=str(exc),
        )


@router.post(
    "/start",
    response_model=StartAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def start_evaluation(
    background_tasks: BackgroundTasks,
    job_id: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
) -> StartAnalysisResponse:
    """Trigger shortlisting pipeline across job description and candidate resumes."""
    store = get_store()
    jd = store.get_job(job_id)
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Description with ID '{job_id}' not found.",
        )

    # If new resume files were submitted alongside start_analysis
    if files:
        for file in files:
            filename = file.filename or "uploaded_resume.pdf"
            content = await file.read()
            if content:
                store.save_resume_file(
                    job_id=job_id,
                    filename=filename,
                    content=content,
                    content_type=file.content_type or "application/pdf",
                )

    total_files = len(store.get_resume_files(job_id))
    task_id = f"eval_{uuid.uuid4().hex[:10]}"
    store.create_task(task_id=task_id, job_id=job_id, resumes_total=total_files)

    # Submit background execution
    background_tasks.add_task(_run_pipeline_worker, job_id, task_id)

    return StartAnalysisResponse(task_id=task_id, status="processing")


@router.get(
    "/status/{task_id}",
    response_model=ProcessingStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_evaluation_status(task_id: str) -> ProcessingStatusResponse:
    """Poll pipeline progress and telemetry for an active evaluation task."""
    store = get_store()
    task = store.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation task '{task_id}' not found.",
        )

    return ProcessingStatusResponse(
        stage=task.stage,
        progress=task.progress,
        message=task.message,
        jd_processed=task.jd_processed,
        resumes_processed=task.resumes_processed,
        resumes_total=task.resumes_total,
        semantic_model_status=task.semantic_model_status,
        keyword_engine_status=task.keyword_engine_status,
        ranking_status=task.ranking_status,
        failed_resumes=[
            FailedUploadItem(filename=f["filename"], reason=f["reason"])
            for f in task.failed_resumes
        ],
    )


@router.get(
    "/rankings",
    response_model=EvaluationResultResponse,
    status_code=status.HTTP_200_OK,
)
async def get_rankings(
    job_id: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
) -> EvaluationResultResponse:
    """Retrieve full candidate evaluation dossiers and deterministic rankings."""
    store = get_store()
    record = store.get_evaluation_result(job_id)
    if not record:
        # Fallback: check if we have an active JD, return empty results
        active_jd = store.get_job(job_id)
        if not active_jd:
            all_jobs = list(store._jobs.values())
            if all_jobs:
                active_jd = all_jobs[0]
            else:
                from backend.models.document import JobDescription
                active_jd = JobDescription(
                    id="pending",
                    role_title="No Job Description Uploaded",
                    source_file="",
                    raw_text="No job description uploaded yet. Please upload a JD and candidate resumes to run the evaluation.",
                )
        return EvaluationResultResponse(
            job_description=active_jd,
            candidates=[],
            processing_time_ms=0,
            model_version="nexora-engine-v1.0",
        )

    candidates = list(record.candidates)

    # Optional min_score filter
    if min_score is not None:
        candidates = [c for c in candidates if (c.final_score or 0.0) >= min_score]

    # Optional sort_by
    if sort_by:
        if sort_by == "final_score":
            candidates.sort(key=lambda c: (c.final_score or 0.0), reverse=True)
        elif sort_by == "required_coverage":
            candidates.sort(key=lambda c: (c.required_coverage or 0.0), reverse=True)
        elif sort_by == "semantic_score":
            candidates.sort(key=lambda c: (c.semantic_score or 0.0), reverse=True)
        elif sort_by == "lexical_score":
            candidates.sort(key=lambda c: (c.lexical_score or 0.0), reverse=True)
        elif sort_by == "rank":
            candidates.sort(key=lambda c: (c.rank or 999999))

    return EvaluationResultResponse(
        job_description=record.job_description,
        candidates=candidates,
        processing_time_ms=record.processing_time_ms,
        model_version=record.model_version,
        failed_candidates=[
            FailedUploadItem(filename=f["filename"], reason=f["reason"])
            for f in record.failed_candidates
        ],
    )


@router.get(
    "/compare",
    response_model=PairwiseComparisonResponse,
    status_code=status.HTTP_200_OK,
)
async def compare_candidates(
    candidate_a: str = Query(..., alias="candidate_a"),
    candidate_b: str = Query(..., alias="candidate_b"),
    job_id: Optional[str] = Query(None),
) -> PairwiseComparisonResponse:
    """Produce deterministic contrastive comparison between Candidate A and Candidate B."""
    store = get_store()
    cand_a = store.get_candidate_evaluation(candidate_a, job_id)
    if not cand_a:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_a}' not found in evaluation records.",
        )

    cand_b = store.get_candidate_evaluation(candidate_b, job_id)
    if not cand_b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_b}' not found in evaluation records.",
        )

    explainer = TemplateExplainer()
    return explainer.compare_pairwise_detailed(cand_a, cand_b)
