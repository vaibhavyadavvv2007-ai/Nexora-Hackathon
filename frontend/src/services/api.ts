// ============================================================
// Nexora Service Layer
// Canonical facade exposing typed domain operations to UI components
// ============================================================

import {
  uploadJobDescription,
  uploadResumes,
  startAnalysis,
  getAnalysisStatus,
  getRankings,
  getCandidate,
  compareCandidates,
  getJobDescription,
  apiClient,
  ApiError,
  getDataSourceMode,
  setDataSourceMode,
  API_BASE_URL,
  API_ENDPOINTS,
} from "@/lib/api";

import type {
  CandidateEvaluation,
  EvaluationResult,
  PairwiseComparison,
  ProcessingStatus,
  StartAnalysisResponse,
} from "@/types";

export type {
  CandidateEvaluation,
  EvaluationResult,
  PairwiseComparison,
  ProcessingStatus,
  ResumeBatchUploadResponse,
  StartAnalysisResponse,
  RequestLifecycleOptions,
  FastApiErrorResponse,
} from "@/types";

// Authoritative 7 Operations explicitly available through the service layer
export {
  uploadJobDescription,
  uploadResumes,
  startAnalysis,
  getAnalysisStatus,
  getRankings,
  getCandidate,
  compareCandidates,
};

// Transport & Configuration exports
export {
  getJobDescription,
  apiClient,
  ApiError,
  getDataSourceMode,
  setDataSourceMode,
  API_BASE_URL,
  API_ENDPOINTS,
};

// Re-export adapters for testability and custom normalization
export * from "@/lib/api/adapters";

// ============================================================
// High-Level Workflow Helpers (Backward Compatibility)
// ============================================================

/**
 * End-to-end evaluation pipeline coordinator.
 */
export async function submitEvaluation(
  jobDescriptionFile: File | null,
  resumeFiles: File[]
): Promise<EvaluationResult> {
  let jobId = "job-current";
  if (jobDescriptionFile) {
    const jd = await uploadJobDescription(jobDescriptionFile);
    jobId = jd.id;
  }
  if (resumeFiles.length > 0) {
    await uploadResumes(resumeFiles, jobId);
  }
  const task: StartAnalysisResponse = await startAnalysis(jobId, resumeFiles);
  await getAnalysisStatus(task.task_id);
  return getRankings(jobId);
}

/**
 * Status retrieval helper with optional mock stage override.
 */
export async function getProcessingStatus(
  jobId: string,
  stage: ProcessingStatus["stage"] = "complete"
): Promise<ProcessingStatus> {
  return getAnalysisStatus(jobId, stage);
}

/**
 * Candidate detail dossier lookup.
 */
export async function getCandidateDetail(
  candidateId: string
): Promise<CandidateEvaluation | null> {
  return getCandidate(candidateId);
}

/**
 * Pairwise contrastive comparison lookup.
 */
export async function getPairwiseComparison(
  candidateAId: string,
  candidateBId: string
): Promise<PairwiseComparison | null> {
  return compareCandidates(candidateAId, candidateBId);
}

/**
 * Full ranking results lookup.
 */
export async function getEvaluationResults(
  jobId?: string
): Promise<EvaluationResult> {
  return getRankings(jobId);
}
