// ============================================================
// Service Layer — Abstracts data source for future backend swap
// Replace mock implementations with fetch() calls when FastAPI is ready
// ============================================================

import {
  CandidateEvaluation,
  EvaluationResult,
  PairwiseComparison,
  ProcessingStatus,
} from "@/types";
import {
  getMockEvaluationResult,
  getMockProcessingStatus,
  getMockPairwiseComparison,
  getMockCandidateById,
} from "@/data/mock-data";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Simulates network latency for realistic UI testing
function simulateDelay(ms: number = 400): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Submit a job description and batch of resumes for evaluation.
 * Currently returns mock data; replace with POST to /api/evaluate
 */
export async function submitEvaluation(
  _jobDescriptionFile: File | null,
  _resumeFiles: File[]
): Promise<EvaluationResult> {
  // Future: POST to `${API_BASE_URL}/api/evaluate` with FormData
  await simulateDelay(1200);
  return getMockEvaluationResult();
}

/**
 * Poll processing status.
 * Currently returns mock status; replace with GET /api/status/:id
 */
export async function getProcessingStatus(
  _jobId: string,
  stage: ProcessingStatus["stage"] = "complete"
): Promise<ProcessingStatus> {
  // Future: GET `${API_BASE_URL}/api/status/${jobId}`
  await simulateDelay(200);
  return getMockProcessingStatus(stage);
}

/**
 * Fetch a single candidate's evaluation details.
 * Currently returns mock data; replace with GET /api/candidates/:id
 */
export async function getCandidateDetail(
  candidateId: string
): Promise<CandidateEvaluation | null> {
  // Future: GET `${API_BASE_URL}/api/candidates/${candidateId}`
  await simulateDelay(300);
  return getMockCandidateById(candidateId);
}

/**
 * Fetch pairwise comparison between two candidates.
 * Currently returns mock data; replace with GET /api/compare?a=X&b=Y
 */
export async function getPairwiseComparison(
  candidateAId: string,
  candidateBId: string
): Promise<PairwiseComparison | null> {
  // Future: GET `${API_BASE_URL}/api/compare?a=${candidateAId}&b=${candidateBId}`
  await simulateDelay(400);
  return getMockPairwiseComparison(candidateAId, candidateBId);
}

/**
 * Fetch the full evaluation result set.
 * Currently returns mock data; replace with GET /api/results/:jobId
 */
export async function getEvaluationResults(
  _jobId: string
): Promise<EvaluationResult> {
  // Future: GET `${API_BASE_URL}/api/results/${jobId}`
  await simulateDelay(300);
  return getMockEvaluationResult();
}

// Export the base URL for health checks
export { API_BASE_URL };
