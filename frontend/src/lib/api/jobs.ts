// ============================================================
// Nexora API — Job Description Domain Operations
// Handles JD upload, parsing, and structured requirement retrieval
// ============================================================

import { JobDescription, RequestLifecycleOptions } from "@/types";
import { apiClient, getDataSourceMode } from "./client";
import { API_ENDPOINTS } from "./config";
import { adaptJobDescription } from "./adapters";
import { MOCK_JOB_DESCRIPTION } from "../mock/candidateEvaluations";

/**
 * Upload and parse a single Job Description document (PDF, DOCX, or TXT).
 */
export async function uploadJobDescription(
  file: File,
  options?: RequestLifecycleOptions
): Promise<JobDescription> {
  const mode = getDataSourceMode();

  if (mode === "mock") {
    // Simulate brief upload and parsing latency
    await new Promise((resolve) => setTimeout(resolve, 600));
    return adaptJobDescription({
      ...MOCK_JOB_DESCRIPTION,
      source_file: file.name,
      title:
        file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ") || MOCK_JOB_DESCRIPTION.title,
    });
  }

  // Live FastAPI endpoint
  const formData = new FormData();
  formData.append("file", file);

  const raw = await apiClient<unknown>(
    API_ENDPOINTS.jobs.upload(),
    {
      method: "POST",
      body: formData,
      signal: options?.signal,
    },
    options?.timeoutMs
  );

  return adaptJobDescription(raw);
}

/**
 * Retrieve an existing parsed Job Description by identifier.
 */
export async function getJobDescription(
  jobId: string,
  options?: RequestLifecycleOptions
): Promise<JobDescription> {
  const mode = getDataSourceMode();

  if (mode === "mock") {
    await new Promise((resolve) => setTimeout(resolve, 200));
    return adaptJobDescription(MOCK_JOB_DESCRIPTION);
  }

  const raw = await apiClient<unknown>(
    API_ENDPOINTS.jobs.get(jobId),
    {
      signal: options?.signal,
    },
    options?.timeoutMs
  );
  return adaptJobDescription(raw);
}
