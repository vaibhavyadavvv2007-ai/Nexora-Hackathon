"""API routes for individual candidate evaluation dossiers."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.store import get_store
from backend.models.evaluation import CandidateEvaluation

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])


@router.get(
    "/{candidate_id}",
    response_model=CandidateEvaluation,
    status_code=status.HTTP_200_OK,
)
async def get_candidate(
    candidate_id: str,
    job_id: Optional[str] = Query(None),
) -> CandidateEvaluation:
    """Retrieve full evaluation dossier, component scores, and evidence for an individual candidate."""
    store = get_store()
    evaluation = store.get_candidate_evaluation(candidate_id=candidate_id, job_id=job_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate evaluation '{candidate_id}' not found.",
        )
    return evaluation
