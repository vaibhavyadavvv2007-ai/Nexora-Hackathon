// ============================================================
// Nexora API — Candidate & Evaluation Domain Operations
// Handles resume batch upload, pipeline polling, rankings, and pairwise comparisons
// ============================================================

import {
  CandidateEvaluation,
  EvaluationResult,
  PairwiseComparison,
  ProcessingStatus,
  RequestLifecycleOptions,
  ResumeBatchUploadResponse,
  StartAnalysisResponse,
} from "@/types";
import { apiClient, getDataSourceMode } from "./client";
import { API_ENDPOINTS } from "./config";
import {
  adaptCandidate,
  adaptEvaluationResult,
  adaptPairwiseComparison,
  adaptProcessingStatus,
  adaptResumeUploadBatchResponse,
  adaptStartAnalysisResponse,
} from "./adapters";
import {
  getMockEvaluationResult,
  getMockProcessingStatus,
  getMockCandidateById,
  getMockPairwiseComparison,
} from "../mock/candidateEvaluations";

/**
 * Upload a batch of candidate resumes (PDF, DOCX, TXT).
 */
export async function uploadResumes(
  files: File[],
  jobId?: string,
  options?: RequestLifecycleOptions
): Promise<ResumeBatchUploadResponse> {
  const mode = getDataSourceMode();

  if (mode === "mock") {
    await new Promise((resolve) => setTimeout(resolve, 800));
    // Simulate checking for corrupt files or invalid formats
    const failed: { filename: string; reason: string }[] = [];
    const validFiles = files.filter((f) => {
      if (f.name.endsWith(".exe") || f.name.endsWith(".bin")) {
        failed.push({ filename: f.name, reason: "Unsupported file extension" });
        return false;
      }
      return true;
    });

    return {
      uploaded: validFiles.length,
      failed,
      job_id: jobId,
    };
  }

  // Live FastAPI endpoint
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  if (jobId) {
    formData.append("job_id", jobId);
  }

  const raw = await apiClient<unknown>(
    API_ENDPOINTS.resumes.uploadBatch(),
    {
      method: "POST",
      body: formData,
      signal: options?.signal,
    },
    options?.timeoutMs
  );

  return adaptResumeUploadBatchResponse(raw);
}

/**
 * Trigger batch analysis and scoring across the JD and uploaded resumes.
 */
export async function startAnalysis(
  jobId: string,
  resumeFiles?: File[],
  options?: RequestLifecycleOptions
): Promise<StartAnalysisResponse> {
  const mode = getDataSourceMode();

  if (mode === "mock") {
    await new Promise((resolve) => setTimeout(resolve, 300));
    return { task_id: `mock-task-${Date.now()}` };
  }

  const formData = new FormData();
  formData.append("job_id", jobId);
  if (resumeFiles) {
    resumeFiles.forEach((file) => formData.append("files", file));
  }

  const raw = await apiClient<unknown>(
    API_ENDPOINTS.evaluation.start(),
    {
      method: "POST",
      body: formData,
      signal: options?.signal,
    },
    options?.timeoutMs
  );

  return adaptStartAnalysisResponse(raw);
}

/**
 * Poll pipeline processing status for an active evaluation task.
 */
export async function getAnalysisStatus(
  taskId: string,
  mockStage: ProcessingStatus["stage"] = "complete",
  options?: RequestLifecycleOptions
): Promise<ProcessingStatus> {
  const mode = getDataSourceMode();

  if (mode === "mock") {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return adaptProcessingStatus(getMockProcessingStatus(mockStage));
  }

  const raw = await apiClient<unknown>(
    API_ENDPOINTS.evaluation.status(taskId),
    {
      signal: options?.signal,
    },
    options?.timeoutMs
  );
  return adaptProcessingStatus(raw);
}

/**
 * Retrieve full candidate rankings and evaluation results.
 */
export async function getRankings(
  jobId?: string,
  options?: RequestLifecycleOptions
): Promise<EvaluationResult> {
  const mode = getDataSourceMode();

  if (mode === "mock") {
    await new Promise((resolve) => setTimeout(resolve, 400));
    return adaptEvaluationResult(getMockEvaluationResult());
  }

  const raw = await apiClient<unknown>(
    API_ENDPOINTS.evaluation.rankings(jobId),
    {
      signal: options?.signal,
    },
    options?.timeoutMs
  );
  return adaptEvaluationResult(raw);
}

/**
 * Retrieve individual candidate evaluation dossier with granular evidence.
 */
export async function getCandidate(
  candidateId: string,
  jobId?: string,
  options?: RequestLifecycleOptions
): Promise<CandidateEvaluation | null> {
  const mode = getDataSourceMode();

  if (mode === "mock") {
    await new Promise((resolve) => setTimeout(resolve, 200));
    const mock = getMockCandidateById(candidateId);
    return mock ? adaptCandidate(mock) : null;
  }

  const raw = await apiClient<unknown>(
    API_ENDPOINTS.candidates.get(candidateId, jobId),
    {
      signal: options?.signal,
    },
    options?.timeoutMs
  );
  return raw ? adaptCandidate(raw) : null;
}

/**
 * Request pairwise contrastive comparison between Candidate A and Candidate B.
 */
export async function compareCandidates(
  candidateAId: string,
  candidateBId: string,
  jobId?: string,
  options?: RequestLifecycleOptions
): Promise<PairwiseComparison | null> {
  const mode = getDataSourceMode();

  if (mode === "mock") {
    await new Promise((resolve) => setTimeout(resolve, 300));
    const mock = getMockPairwiseComparison(candidateAId, candidateBId);
    return mock ? adaptPairwiseComparison(mock) : null;
  }

  const raw = await apiClient<unknown>(
    API_ENDPOINTS.evaluation.compare(candidateAId, candidateBId, jobId),
    {
      signal: options?.signal,
    },
    options?.timeoutMs
  );
  return adaptPairwiseComparison(raw);
}
