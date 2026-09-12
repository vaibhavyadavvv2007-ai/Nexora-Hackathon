// ============================================================
// Nexora API — Central Endpoint & Transport Configuration
// Single source of truth for backend URLs, paths, and timeouts.
// Update this file when backend route signatures or base URLs change.
// ============================================================

export const API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export const DEFAULT_TIMEOUT_MS = 15000;

export const DATA_SOURCE_STORAGE_KEY = "nexora_data_source_mode";

/**
 * Authoritative registry of all backend API endpoint paths.
 * No UI component or domain function should hardcode URL strings.
 */
export const API_ENDPOINTS = {
  // Job Description operations
  jobs: {
    upload: () => "api/jobs/upload",
    get: (jobId: string) => `api/jobs/${encodeURIComponent(jobId)}`,
  },

  // Resume batch upload operations
  resumes: {
    uploadBatch: () => "api/resumes/upload-batch",
  },

  // Pipeline evaluation & ranking operations
  evaluation: {
    start: () => "api/evaluation/start",
    status: (taskId: string) => `api/evaluation/status/${encodeURIComponent(taskId)}`,
    rankings: (jobId?: string) => {
      const query = jobId ? `?job_id=${encodeURIComponent(jobId)}` : "";
      return `api/evaluation/rankings${query}`;
    },
    compare: (candidateAId: string, candidateBId: string, jobId?: string) => {
      const base = `api/evaluation/compare?candidate_a=${encodeURIComponent(
        candidateAId
      )}&candidate_b=${encodeURIComponent(candidateBId)}`;
      return jobId ? `${base}&job_id=${encodeURIComponent(jobId)}` : base;
    },
  },

  // Individual candidate dossier operations
  candidates: {
    get: (candidateId: string, jobId?: string) => {
      const base = `api/candidates/${encodeURIComponent(candidateId)}`;
      return jobId ? `${base}?job_id=${encodeURIComponent(jobId)}` : base;
    },
  },

  // System health verification
  health: () => "health",
} as const;
