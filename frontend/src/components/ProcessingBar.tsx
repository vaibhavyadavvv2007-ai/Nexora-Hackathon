"use client";

import { ProcessingStatus } from "@/types";

interface ProcessingBarProps {
  status: ProcessingStatus;
  onRetry?: () => void;
}

export default function ProcessingBar({ status, onRetry }: ProcessingBarProps) {
  if (status.stage === "idle") return null;

  const isError = status.stage === "error";
  const isComplete = status.stage === "complete";

  const getSubStatusPill = (
    label: string,
    state: "idle" | "loading" | "encoding" | "indexing" | "matching" | "computing" | "ready" | "complete" | "error" | boolean
  ) => {
    let color = "bg-zinc-800 text-zinc-500 border-zinc-700/50";
    let icon = "○";

    if (state === true || state === "ready" || state === "complete") {
      color = "bg-emerald-950/40 text-emerald-300 border-emerald-500/30";
      icon = "✓";
    } else if (state === "error") {
      color = "bg-red-950/40 text-red-300 border-red-500/30";
      icon = "✕";
    } else if (state !== "idle" && state !== false) {
      color = "bg-blue-950/40 text-blue-300 border-blue-500/30";
      icon = "●";
    }

    return (
      <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-mono border ${color}`}>
        <span className="text-[10px]">{icon}</span>
        <span>{label}</span>
      </div>
    );
  };

  return (
    <div
      role="status"
      aria-live="polite"
      className={`
        rounded-lg border p-4.5 transition-all
        ${isError
          ? "border-red-500/40 bg-red-950/20"
          : isComplete
            ? "border-emerald-500/30 bg-emerald-950/10"
            : "border-blue-500/30 bg-blue-950/10"
        }
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          {isComplete ? (
            <div className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs">
              ✓
            </div>
          ) : isError ? (
            <div className="w-6 h-6 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center font-bold text-xs">
              ✕
            </div>
          ) : (
            <div className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          )}

          <div>
            <h3 className="text-xs font-semibold text-zinc-100 uppercase tracking-wider">
              {status.stage.toUpperCase()} — {status.message}
            </h3>
            <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
              Processed {status.resumes_processed} of {status.resumes_total} candidate resumes
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono font-semibold text-zinc-300">
            {status.progress}%
          </span>
          {isError && onRetry && (
            <button
              onClick={onRetry}
              className="text-xs px-2.5 py-1 rounded bg-red-500/20 border border-red-500/40 text-red-200 hover:bg-red-500/30"
            >
              Retry Evaluation
            </button>
          )}
        </div>
      </div>

      {/* Progress Track */}
      <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-3">
        <div
          className={`h-full transition-all duration-300 ease-out ${
            isError ? "bg-red-500" : isComplete ? "bg-emerald-500" : "bg-blue-500"
          }`}
          style={{ width: `${status.progress}%` }}
        />
      </div>

      {/* Granular Pipeline Stage Monitors */}
      <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-zinc-800/80">
        {getSubStatusPill("JD Parsed", status.jd_processed)}
        {getSubStatusPill(
          `Resumes: ${status.resumes_processed}/${status.resumes_total}`,
          status.resumes_processed > 0 && status.resumes_processed === status.resumes_total
        )}
        {getSubStatusPill(
          `Semantic: ${status.semantic_model_status}`,
          status.semantic_model_status
        )}
        {getSubStatusPill(
          `Keyword BM25: ${status.keyword_engine_status}`,
          status.keyword_engine_status
        )}
        {getSubStatusPill(
          `Ranking Fusion: ${status.ranking_status}`,
          status.ranking_status
        )}
      </div>

      {/* Failed Resumes notice if any */}
      {status.failed_resumes.length > 0 && (
        <div className="mt-3 p-2.5 rounded bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300">
          <p className="font-semibold mb-1">Partial Processing Notice:</p>
          <ul className="list-disc list-inside text-[11px] text-amber-300/90 space-y-0.5">
            {status.failed_resumes.map((fr, i) => (
              <li key={i}>
                <span className="font-mono">{fr.filename}</span>: {fr.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
