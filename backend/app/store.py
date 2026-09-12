"""In-memory state store for Nexora backend.

Stores active job descriptions, uploaded resume documents, pipeline processing statuses,
and computed evaluation results across request lifecycles. Thread-safe with threading.Lock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import threading
from typing import Any, Dict, List, Optional

from backend.models.document import JobDescription, Resume
from backend.models.evaluation import CandidateEvaluation


@dataclass
class UploadedFileRecord:
    """Raw uploaded file metadata and binary content."""
    filename: str
    content: bytes
    content_type: str = "application/pdf"
    size_bytes: int = 0

    def __post_init__(self) -> None:
        if not self.size_bytes and self.content:
            self.size_bytes = len(self.content)


@dataclass
class EvaluationTaskRecord:
    """Telemetry and progress tracking for an asynchronous/background evaluation pipeline run."""
    task_id: str
    job_id: str
    stage: str = "idle"  # idle | uploading | parsing | matching | ranking | complete | error
    progress: int = 0    # 0 - 100
    message: str = "Initialized"
    jd_processed: bool = False
    resumes_processed: int = 0
    resumes_total: int = 0
    semantic_model_status: str = "idle"  # idle | loading | encoding | ready | error
    keyword_engine_status: str = "idle"  # idle | indexing | matching | ready | error
    ranking_status: str = "idle"         # idle | computing | complete | error
    failed_resumes: List[Dict[str, str]] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class EvaluationResultRecord:
    """Completed evaluation output containing ranked candidates and job description."""
    job_id: str
    job_description: JobDescription
    candidates: List[CandidateEvaluation]
    processing_time_ms: int = 0
    model_version: str = "nexora-engine-v1.0"
    failed_candidates: List[Dict[str, str]] = field(default_factory=list)


class InMemoryStore:
    """Thread-safe singleton-style in-memory repository for application state."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # job_id -> JobDescription
        self._jobs: Dict[str, JobDescription] = {}
        # job_id -> { filename -> UploadedFileRecord }
        self._resume_files: Dict[str, Dict[str, UploadedFileRecord]] = {}
        # job_id -> { candidate_id -> Resume }
        self._parsed_resumes: Dict[str, Dict[str, Resume]] = {}
        # task_id -> EvaluationTaskRecord
        self._tasks: Dict[str, EvaluationTaskRecord] = {}
        # job_id -> EvaluationResultRecord
        self._evaluation_results: Dict[str, EvaluationResultRecord] = {}
        # latest job_id tracker
        self._latest_job_id: Optional[str] = None

    # ---------------- Job Descriptions ----------------

    def save_job(self, jd: JobDescription) -> None:
        with self._lock:
            self._jobs[jd.id] = jd
            self._latest_job_id = jd.id
            if jd.id not in self._resume_files:
                self._resume_files[jd.id] = {}
            if jd.id not in self._parsed_resumes:
                self._parsed_resumes[jd.id] = {}

    def get_job(self, job_id: Optional[str] = None) -> Optional[JobDescription]:
        with self._lock:
            if job_id:
                return self._jobs.get(job_id)
            if self._latest_job_id:
                return self._jobs.get(self._latest_job_id)
            return next(iter(self._jobs.values()), None)

    def list_jobs(self) -> List[JobDescription]:
        with self._lock:
            return list(self._jobs.values())

    # ---------------- Uploaded Resumes ----------------

    def save_resume_file(self, job_id: str, filename: str, content: bytes, content_type: str = "application/pdf") -> None:
        with self._lock:
            if job_id not in self._resume_files:
                self._resume_files[job_id] = {}
            self._resume_files[job_id][filename] = UploadedFileRecord(
                filename=filename,
                content=content,
                content_type=content_type,
                size_bytes=len(content)
            )

    def get_resume_files(self, job_id: Optional[str] = None) -> List[UploadedFileRecord]:
        with self._lock:
            target_id = job_id or self._latest_job_id
            if not target_id or target_id not in self._resume_files:
                return []
            return list(self._resume_files[target_id].values())

    # ---------------- Parsed Resumes ----------------

    def save_parsed_resume(self, job_id: str, resume: Resume) -> None:
        with self._lock:
            if job_id not in self._parsed_resumes:
                self._parsed_resumes[job_id] = {}
            self._parsed_resumes[job_id][resume.candidate_id] = resume

    def get_parsed_resumes(self, job_id: Optional[str] = None) -> List[Resume]:
        with self._lock:
            target_id = job_id or self._latest_job_id
            if not target_id or target_id not in self._parsed_resumes:
                return []
            return list(self._parsed_resumes[target_id].values())

    # ---------------- Evaluation Tasks ----------------

    def create_task(self, task_id: str, job_id: str, resumes_total: int = 0) -> EvaluationTaskRecord:
        with self._lock:
            task = EvaluationTaskRecord(
                task_id=task_id,
                job_id=job_id,
                stage="uploading",
                progress=5,
                message="Starting pipeline processing...",
                jd_processed=job_id in self._jobs,
                resumes_total=resumes_total,
            )
            self._tasks[task_id] = task
            return task

    def get_task(self, task_id: str) -> Optional[EvaluationTaskRecord]:
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(
        self,
        task_id: str,
        stage: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        jd_processed: Optional[bool] = None,
        resumes_processed: Optional[int] = None,
        resumes_total: Optional[int] = None,
        semantic_model_status: Optional[str] = None,
        keyword_engine_status: Optional[str] = None,
        ranking_status: Optional[str] = None,
        failed_resumes: Optional[List[Dict[str, str]]] = None,
        error: Optional[str] = None,
    ) -> Optional[EvaluationTaskRecord]:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            if stage is not None:
                task.stage = stage
            if progress is not None:
                task.progress = progress
            if message is not None:
                task.message = message
            if jd_processed is not None:
                task.jd_processed = jd_processed
            if resumes_processed is not None:
                task.resumes_processed = resumes_processed
            if resumes_total is not None:
                task.resumes_total = resumes_total
            if semantic_model_status is not None:
                task.semantic_model_status = semantic_model_status
            if keyword_engine_status is not None:
                task.keyword_engine_status = keyword_engine_status
            if ranking_status is not None:
                task.ranking_status = ranking_status
            if failed_resumes is not None:
                task.failed_resumes.extend(failed_resumes)
            if error is not None:
                task.error = error
            return task

    # ---------------- Evaluation Results ----------------

    def save_evaluation_result(self, result: EvaluationResultRecord) -> None:
        with self._lock:
            self._evaluation_results[result.job_id] = result

    def get_evaluation_result(self, job_id: Optional[str] = None) -> Optional[EvaluationResultRecord]:
        with self._lock:
            target_id = job_id or self._latest_job_id
            if not target_id:
                return next(iter(self._evaluation_results.values()), None)
            return self._evaluation_results.get(target_id)

    def get_candidate_evaluation(
        self, candidate_id: str, job_id: Optional[str] = None
    ) -> Optional[CandidateEvaluation]:
        with self._lock:
            result = self.get_evaluation_result(job_id)
            if not result:
                return None
            for cand in result.candidates:
                if cand.candidate_id == candidate_id:
                    return cand
            return None

    def clear(self) -> None:
        """Reset all in-memory state (useful for tests)."""
        with self._lock:
            self._jobs.clear()
            self._resume_files.clear()
            self._parsed_resumes.clear()
            self._tasks.clear()
            self._evaluation_results.clear()
            self._latest_job_id = None


# Global store instance
_STORE_INSTANCE: Optional[InMemoryStore] = None


def get_store() -> InMemoryStore:
    """Accessor for application singleton in-memory store."""
    global _STORE_INSTANCE
    if _STORE_INSTANCE is None:
        _STORE_INSTANCE = InMemoryStore()
    return _STORE_INSTANCE
