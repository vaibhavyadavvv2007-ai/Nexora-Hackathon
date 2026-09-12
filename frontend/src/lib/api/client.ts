// ============================================================
// Nexora API Client — Core HTTP Transport & Mode Configuration
// Manages backend base URL, timeouts, and Mock/Live API switching
// ============================================================

import { DataSourceMode } from "@/types";
import { API_BASE_URL, DEFAULT_TIMEOUT_MS, DATA_SOURCE_STORAGE_KEY } from "./config";

export { API_BASE_URL };

/**
 * Returns the currently active data source mode ('mock' or 'api').
 * Defaults to 'mock' if backend is not yet deployed or in offline dev.
 */
export function getDataSourceMode(): DataSourceMode {
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem(DATA_SOURCE_STORAGE_KEY);
    if (saved === "api" || saved === "mock") {
      return saved;
    }
  }
  const envMode = process.env.NEXT_PUBLIC_DATA_SOURCE;
  return envMode === "api" ? "api" : "mock";
}

/**
 * Set runtime data source mode ('mock' or 'api').
 */
export function setDataSourceMode(mode: DataSourceMode): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(DATA_SOURCE_STORAGE_KEY, mode);
  }
}

/**
 * Structured API Error class for frontend error handling.
 */
export class ApiError extends Error {
  public status: number;
  public details?: unknown;

  constructor(message: string, status: number = 500, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

/**
 * Generic typed HTTP request executor with timeout and error mapping.
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<T> {
  const url = `${API_BASE_URL.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const onExternalAbort = () => {
    clearTimeout(timeoutId);
    controller.abort();
  };

  if (options.signal) {
    if (options.signal.aborted) {
      clearTimeout(timeoutId);
      controller.abort();
    } else {
      options.signal.addEventListener("abort", onExternalAbort, { once: true });
    }
  }

  try {
    const headers = new Headers(options.headers || {});
    if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    if (options.signal) {
      options.signal.removeEventListener("abort", onExternalAbort);
    }

    if (!response.ok) {
      let errorDetail: unknown = null;
      try {
        errorDetail = await response.json();
      } catch {
        errorDetail = await response.text();
      }
      throw new ApiError(
        `Backend request failed (${response.status}): ${response.statusText}`,
        response.status,
        errorDetail
      );
    }

    return (await response.json()) as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) {
      throw err;
    }
    if (err instanceof Error && err.name === "AbortError") {
      throw new ApiError(`Request timeout after ${timeoutMs}ms`, 408);
    }
    throw new ApiError(
      err instanceof Error ? err.message : "Network error connecting to Nexora backend",
      0
    );
  }
}
