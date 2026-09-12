"use client";

import { useCallback, useState } from "react";

interface UploadPanelProps {
  onSubmit: (jdFile: File | null, resumeFiles: File[]) => void;
  onLoadSample: () => void;
  isProcessing: boolean;
}

const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt"];
const MAX_RECOMMENDED_RESUMES = 25;

export default function UploadPanel({
  onSubmit,
  onLoadSample,
  isProcessing,
}: UploadPanelProps) {
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const [jdDragOver, setJdDragOver] = useState(false);
  const [resumeDragOver, setResumeDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const isValidFile = (file: File) => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    return ACCEPTED_EXTENSIONS.includes(ext);
  };

  const handleJdChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!isValidFile(file)) {
        setValidationError(`Invalid JD file "${file.name}". Accepted formats: .pdf, .docx, .txt`);
        return;
      }
      setValidationError(null);
      setJdFile(file);
    }
  }, []);

  const handleResumesChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        const files = Array.from(e.target.files);
        const invalid = files.filter((f) => !isValidFile(f));
        if (invalid.length > 0) {
          setValidationError(
            `Skipped ${invalid.length} unsupported file(s). Accepted formats: .pdf, .docx, .txt`
          );
        } else {
          setValidationError(null);
        }
        const valid = files.filter(isValidFile);
        setResumeFiles((prev) => [...prev, ...valid]);
      }
    },
    []
  );

  const handleJdDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setJdDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      if (!isValidFile(file)) {
        setValidationError(`Invalid JD file "${file.name}". Accepted formats: .pdf, .docx, .txt`);
        return;
      }
      setValidationError(null);
      setJdFile(file);
    }
  }, []);

  const handleResumeDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setResumeDragOver(false);
    if (e.dataTransfer.files) {
      const files = Array.from(e.dataTransfer.files);
      const invalid = files.filter((f) => !isValidFile(f));
      if (invalid.length > 0) {
        setValidationError(
          `Skipped ${invalid.length} unsupported file(s). Accepted formats: .pdf, .docx, .txt`
        );
      } else {
        setValidationError(null);
      }
      const valid = files.filter(isValidFile);
      setResumeFiles((prev) => [...prev, ...valid]);
    }
  }, []);

  const handleRemoveResume = (index: number) => {
    setResumeFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = useCallback(() => {
    onSubmit(jdFile, resumeFiles);
  }, [jdFile, resumeFiles, onSubmit]);

  const canSubmit = (jdFile !== null || resumeFiles.length > 0) && !isProcessing;

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      {validationError && (
        <div
          role="alert"
          className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-300 flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span>{validationError}</span>
          </div>
          <button
            onClick={() => setValidationError(null)}
            className="text-red-400 hover:text-red-200 ml-2"
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* JD Upload Section */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="jd-upload" className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider">
              1. Job Description Document
            </label>
            <span className="text-[11px] text-zinc-500 font-mono">PDF, DOCX, TXT</span>
          </div>
          <div
            onDragOver={(e) => { e.preventDefault(); setJdDragOver(true); }}
            onDragLeave={() => setJdDragOver(false)}
            onDrop={handleJdDrop}
            className={`
              relative border-2 border-dashed rounded-lg p-5 text-center transition-all duration-150 cursor-pointer
              ${jdDragOver
                ? "border-blue-500 bg-blue-500/10"
                : jdFile
                  ? "border-emerald-500/50 bg-emerald-950/20"
                  : "border-zinc-700 bg-zinc-900/50 hover:border-zinc-500"
              }
            `}
          >
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleJdChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              id="jd-upload"
              aria-label="Upload Job Description document"
            />
            {jdFile ? (
              <div className="flex items-center justify-between text-left p-1">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-8 h-8 rounded bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center shrink-0">
                    <svg className="w-4 h-4 text-emerald-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-zinc-100 truncate">{jdFile.name}</p>
                    <p className="text-[10px] text-zinc-500 font-mono">{formatFileSize(jdFile.size)} · Ready</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setJdFile(null); }}
                  className="p-1 text-zinc-500 hover:text-red-400 transition-colors"
                  aria-label="Remove JD file"
                >
                  ✕
                </button>
              </div>
            ) : (
              <div>
                <svg className="w-7 h-7 text-zinc-500 mx-auto mb-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <p className="text-xs text-zinc-300 font-medium">Select or drop Job Description PDF</p>
                <p className="text-[11px] text-zinc-500 mt-0.5">Supports PDF text layer, DOCX, or plain text</p>
              </div>
            )}
          </div>
        </div>

        {/* Resumes Upload Section */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="resume-upload" className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider">
              2. Batch Resumes
            </label>
            <span className="text-[11px] text-zinc-500 font-mono">
              {resumeFiles.length} file{resumeFiles.length !== 1 ? "s" : ""} selected
            </span>
          </div>
          <div
            onDragOver={(e) => { e.preventDefault(); setResumeDragOver(true); }}
            onDragLeave={() => setResumeDragOver(false)}
            onDrop={handleResumeDrop}
            className={`
              relative border-2 border-dashed rounded-lg p-5 text-center transition-all duration-150 cursor-pointer
              ${resumeDragOver
                ? "border-blue-500 bg-blue-500/10"
                : resumeFiles.length > 0
                  ? "border-blue-500/50 bg-blue-950/20"
                  : "border-zinc-700 bg-zinc-900/50 hover:border-zinc-500"
              }
            `}
          >
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              multiple
              onChange={handleResumesChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              id="resume-upload"
              aria-label="Upload candidate resume files"
            />
            <div>
              <svg className="w-7 h-7 text-zinc-500 mx-auto mb-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75" />
              </svg>
              <p className="text-xs text-zinc-300 font-medium">Select or drop multiple applicant PDFs</p>
              <p className="text-[11px] text-zinc-500 mt-0.5">Recommended 10–25 candidate resumes per cohort</p>
            </div>
          </div>
        </div>
      </div>

      {/* Selected Resumes File List */}
      {resumeFiles.length > 0 && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-zinc-400">
              Queued Applicant Resumes ({resumeFiles.length})
            </span>
            <button
              onClick={() => setResumeFiles([])}
              className="text-[11px] text-zinc-500 hover:text-red-400"
            >
              Clear all
            </button>
          </div>
          <div className="max-h-32 overflow-y-auto space-y-1.5 pr-1">
            {resumeFiles.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-xs py-1 px-2.5 rounded bg-zinc-900 border border-zinc-800"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-zinc-500 font-mono text-[10px]">#{idx + 1}</span>
                  <span className="text-zinc-200 truncate max-w-[280px]">{file.name}</span>
                  <span className="text-[10px] text-zinc-500 font-mono">{formatFileSize(file.size)}</span>
                </div>
                <button
                  onClick={() => handleRemoveResume(idx)}
                  className="text-zinc-500 hover:text-red-400 transition-colors ml-2"
                  aria-label={`Remove ${file.name}`}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          {resumeFiles.length > MAX_RECOMMENDED_RESUMES && (
            <p className="text-[11px] text-amber-400/90 mt-2 flex items-center gap-1">
              <span>⚠</span> Cohorts over {MAX_RECOMMENDED_RESUMES} resumes may require additional parsing time.
            </p>
          )}
        </div>
      )}

      {/* Action Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-zinc-800">
        <div className="flex items-center gap-3">
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className={`
              px-5 py-2 rounded-lg text-xs font-semibold transition-all duration-150 flex items-center gap-2
              ${canSubmit
                ? "bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-950/50 cursor-pointer"
                : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
              }
            `}
          >
            {isProcessing ? (
              <>
                <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span>Evaluating Cohort…</span>
              </>
            ) : (
              <>
                <span>Start Shortlisting Analysis</span>
                <span>→</span>
              </>
            )}
          </button>

          <span className="text-xs text-zinc-500 font-mono">
            {jdFile ? "1 JD staged" : "Default JD active"} · {resumeFiles.length} uploaded files
          </span>
        </div>

        {/* 1-Click Demo Button */}
        <button
          onClick={onLoadSample}
          disabled={isProcessing}
          type="button"
          className="text-xs px-3 py-1.5 rounded-md border border-zinc-700 bg-zinc-800/80 text-zinc-300 hover:text-white hover:bg-zinc-700 transition-colors flex items-center gap-1.5"
        >
          <span>⚡</span>
          <span>Load Synthetic Hackathon Sample (5 Candidates)</span>
        </button>
      </div>
    </div>
  );
}
