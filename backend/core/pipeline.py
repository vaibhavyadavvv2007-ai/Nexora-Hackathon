"""Candidate Shortlisting Pipeline Orchestrator.

Orchestrates the complete end-to-end pipeline:
1. Ingestion: PDF Extraction via PyMuPDF with reading order preservation
2. Parsing: Structured Job Description and Resume parsing
3. Skill Normalization: Canonical skill mapping and deduplication
4. Multi-Signal Matching:
   - Explicit keyword matching (coverage)
   - BM25 contextual lexical relevance
   - Sentence-Transformer semantic requirement alignment
5. Score Fusion: Multi-signal weighted scoring bounded to [0, 1]
6. Deterministic Ranking: Strict tie-breaking hierarchy
7. Audit-trail explanation generation: Template-backed, non-hallucinatory

Guarantees fault-isolation: a corrupted resume does not abort the batch.
"""

from __future__ import annotations

from pathlib import Path
import re
import time
from typing import BinaryIO, Dict, List, Optional, Tuple, Union

from backend.config.settings import Settings, get_settings
from backend.core.explanations.explainer import TemplateExplainer
from backend.core.parsing import DocumentParser
from backend.core.ranking import EvaluationMode, RankingEngine
from backend.models.document import JobDescription, Resume
from backend.models.evaluation import CandidateEvaluation
from backend.app.store import EvaluationResultRecord, get_store


class ShortlistingPipeline:
    """End-to-end shortlisting pipeline coordinator."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        document_parser: Optional[DocumentParser] = None,
        ranking_engine: Optional[RankingEngine] = None,
        explainer: Optional[TemplateExplainer] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.parser = document_parser or DocumentParser()
        self.ranking_engine = ranking_engine or RankingEngine(settings=self.settings)
        self.explainer = explainer or TemplateExplainer()

    def parse_job_description(
        self,
        source: Union[str, Path, bytes, BinaryIO],
        doc_id: str = "jd_001",
    ) -> JobDescription:
        """Parse raw PDF or file path into a structured JobDescription.

        Raises DocumentParsingError if parsing fails.
        """
        return self.parser.parse_job_description(source, doc_id=doc_id)

    def parse_resume(
        self,
        source: Union[str, Path, bytes, BinaryIO],
        candidate_id: str,
        candidate_name: Optional[str] = None,
    ) -> Resume:
        """Parse raw resume PDF into a structured Resume.

        Raises DocumentParsingError if parsing fails.
        """
        return self.parser.parse_resume(
            source=source,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
        )

    def parse_resumes_batch(
        self,
        resumes: List[Tuple[str, Union[str, Path, bytes, BinaryIO]]],
        id_prefix: str = "cand",
    ) -> Tuple[List[Resume], List[Dict[str, str]]]:
        """Parse a batch of resumes with fault isolation.

        Only files whose final extension is .pdf are processed.
        Unsupported file extensions are safely rejected without calling PyMuPDF.
        Candidate IDs are uniquely derived preferring parsed name, then filename, then fallback.
        A corrupted or failed resume will be logged in failed_resumes,
        allowing healthy resumes in the batch to proceed.
        """
        parsed_resumes: List[Resume] = []
        failed_resumes: List[Dict[str, str]] = []
        seen_ids: set[str] = set()

        for idx, (filename, source) in enumerate(resumes):
            # Ingestion boundary: only process files with final extension .pdf
            # Handles names like Resume1.pdf vs Resume1.xml vs Resume1.pdf.xml
            lower_name = filename.lower()
            if not lower_name.endswith(".pdf"):
                failed_resumes.append({
                    "filename": filename,
                    "reason": "Unsupported file format: only files with final extension .pdf are supported.",
                })
                continue

            # Safe initial candidate ID based on index and filename
            safe_stem = re.sub(r"[^a-zA-Z0-9_]", "_", Path(filename).stem).lower().strip("_")
            initial_cand_id = f"{id_prefix}_{idx + 1:03d}_{safe_stem}" if safe_stem else f"{id_prefix}_{idx + 1:03d}"

            try:
                resume = self.parse_resume(
                    source=source,
                    candidate_id=initial_cand_id,
                    candidate_name=None,
                )
                resume.source_file = filename

                # Candidate Identification:
                # Prefer: 1. parsed candidate name when available
                #         2. safe filename-derived identifier
                #         3. unique fallback identifier
                # Ensure two files with similar names never collide
                if resume.name and not resume.name.startswith("Candidate_"):
                    clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", resume.name.strip().lower()).strip("_")
                    base_id = f"cand_{clean_name}"
                elif safe_stem:
                    base_id = f"cand_{safe_stem}"
                else:
                    base_id = f"{id_prefix}_{idx + 1:03d}"

                cand_id = base_id
                dup_counter = 1
                while cand_id in seen_ids:
                    cand_id = f"{base_id}_{dup_counter}"
                    dup_counter += 1

                resume.candidate_id = cand_id
                seen_ids.add(cand_id)
                parsed_resumes.append(resume)
            except Exception as exc:
                failed_resumes.append({
                    "filename": filename,
                    "reason": str(exc),
                })

        return parsed_resumes, failed_resumes

    def evaluate_and_rank(
        self,
        job_description: JobDescription,
        resumes: List[Resume],
        mode: EvaluationMode = EvaluationMode.COMBINED,
        failed_resumes: Optional[List[Dict[str, str]]] = None,
    ) -> EvaluationResultRecord:
        """Run matching, score fusion, deterministic ranking, and explanations."""
        start_time = time.perf_counter()

        if not resumes:
            return EvaluationResultRecord(
                job_id=job_description.id,
                job_description=job_description,
                candidates=[],
                processing_time_ms=int((time.perf_counter() - start_time) * 1000),
                model_version="nexora-engine-v1.0",
                failed_candidates=failed_resumes or [],
            )

        # 1. Multi-signal matching, score fusion, and deterministic ranking
        ranked_evaluations = self.ranking_engine.evaluate_and_rank_batch(
            resumes=resumes,
            jd=job_description,
            mode=mode,
        )

        # 2. Attach deterministic explanations to each candidate evaluation
        for evaluation in ranked_evaluations:
            explanation_text = self.explainer.explain_candidate(evaluation)
            evaluation.explanation = explanation_text

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return EvaluationResultRecord(
            job_id=job_description.id,
            job_description=job_description,
            candidates=ranked_evaluations,
            processing_time_ms=elapsed_ms,
            model_version="nexora-engine-v1.0",
            failed_candidates=failed_resumes or [],
        )

    def execute(
        self,
        job_description: JobDescription,
        resume_inputs: List[Tuple[str, Union[str, Path, bytes, BinaryIO]]],
        task_id: Optional[str] = None,
        mode: EvaluationMode = EvaluationMode.COMBINED,
    ) -> EvaluationResultRecord:
        """Execute full batch pipeline with live progress updating in store."""
        store = get_store()
        total_resumes = len(resume_inputs)

        if task_id:
            store.update_task(
                task_id=task_id,
                stage="parsing",
                progress=20,
                message=f"Parsing {total_resumes} resume(s)...",
                jd_processed=True,
                resumes_total=total_resumes,
            )

        # Parse resumes with fault isolation
        parsed_resumes, failed_resumes = self.parse_resumes_batch(resume_inputs)

        # Store parsed resumes
        for r in parsed_resumes:
            store.save_parsed_resume(job_description.id, r)

        if task_id:
            store.update_task(
                task_id=task_id,
                stage="matching",
                progress=50,
                message=f"Executing multi-signal matching on {len(parsed_resumes)} candidate(s)...",
                resumes_processed=len(parsed_resumes),
                failed_resumes=failed_resumes,
                semantic_model_status="ready",
                keyword_engine_status="ready",
            )

        if task_id:
            store.update_task(
                task_id=task_id,
                stage="ranking",
                progress=80,
                message="Calculating score fusion and deterministic ranking...",
                ranking_status="computing",
            )

        # Evaluate and rank
        result_record = self.evaluate_and_rank(
            job_description=job_description,
            resumes=parsed_resumes,
            mode=mode,
            failed_resumes=failed_resumes,
        )

        # Save result in store
        store.save_evaluation_result(result_record)

        if task_id:
            store.update_task(
                task_id=task_id,
                stage="complete",
                progress=100,
                message=f"Evaluation complete. Ranked {len(result_record.candidates)} candidates.",
                ranking_status="complete",
            )

        return result_record


# Global pipeline instance
_PIPELINE_INSTANCE: Optional[ShortlistingPipeline] = None


def get_pipeline() -> ShortlistingPipeline:
    """Accessor for application singleton shortlisting pipeline."""
    global _PIPELINE_INSTANCE
    if _PIPELINE_INSTANCE is None:
        _PIPELINE_INSTANCE = ShortlistingPipeline()
    return _PIPELINE_INSTANCE
