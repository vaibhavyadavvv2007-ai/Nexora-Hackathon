"use client";

import { ProcessingStatus } from "@/types";

interface ProcessingBarProps {
  status: ProcessingStatus;
}

const STAGE_LABELS: Record<ProcessingStatus["stage"], string> = {
  idle: "Ready",
  uploading: "Uploading",
  parsing: "Parsing PDFs",
  matching: "Matching",
  ranking: "Ranking",
  complete: "Complete",
  error: "Error",
};

export default function ProcessingBar({ status }: ProcessingBarProps) {
  if (status.stage === "idle") return null;

  const isError = status.stage === "error";
  const isComplete = status.stage === "complete";

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isComplete ? (
            <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : isError ? (
            <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-blue-400 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          <span className={`text-sm font-medium ${isError ? "text-red-400" : isComplete ? "text-emerald-400" : "text-zinc-300"}`}>
            {STAGE_LABELS[status.stage]}
          </span>
        </div>
        <span className="text-xs text-zinc-500">
          {status.candidates_processed}/{status.candidates_total} candidates
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${
            isError ? "bg-red-500" : isComplete ? "bg-emerald-500" : "bg-blue-500"
          }`}
          style={{ width: `${status.progress}%` }}
        />
      </div>

      <p className="text-xs text-zinc-500 mt-2">{status.message}</p>
    </div>
  );
}
