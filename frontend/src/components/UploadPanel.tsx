"use client";

import { useCallback, useState } from "react";

interface UploadPanelProps {
  onSubmit: (jdFile: File | null, resumeFiles: File[]) => void;
  isProcessing: boolean;
}

export default function UploadPanel({ onSubmit, isProcessing }: UploadPanelProps) {
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const [jdDragOver, setJdDragOver] = useState(false);
  const [resumeDragOver, setResumeDragOver] = useState(false);

  const handleJdChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setJdFile(e.target.files[0]);
  }, []);

  const handleResumesChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setResumeFiles(Array.from(e.target.files));
  }, []);

  const handleJdDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setJdDragOver(false);
    if (e.dataTransfer.files?.[0]) setJdFile(e.dataTransfer.files[0]);
  }, []);

  const handleResumeDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setResumeDragOver(false);
    if (e.dataTransfer.files) setResumeFiles(Array.from(e.dataTransfer.files));
  }, []);

  const handleSubmit = useCallback(() => {
    onSubmit(jdFile, resumeFiles);
  }, [jdFile, resumeFiles, onSubmit]);

  const canSubmit = (jdFile || resumeFiles.length > 0) && !isProcessing;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {/* JD Upload */}
      <div>
        <label className="block text-sm font-medium text-zinc-400 mb-2">
          Job Description
        </label>
        <div
          onDragOver={(e) => { e.preventDefault(); setJdDragOver(true); }}
          onDragLeave={() => setJdDragOver(false)}
          onDrop={handleJdDrop}
          className={`
            relative border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 cursor-pointer
            ${jdDragOver
              ? "border-blue-500 bg-blue-500/5"
              : jdFile
                ? "border-emerald-600/40 bg-emerald-900/10"
                : "border-zinc-700 bg-zinc-900/50 hover:border-zinc-500"
            }
          `}
        >
          <input
            type="file"
            accept=".pdf,.txt,.docx"
            onChange={handleJdChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            id="jd-upload"
          />
          {jdFile ? (
            <div className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-zinc-300 truncate max-w-[200px]">{jdFile.name}</span>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setJdFile(null); }}
                className="ml-2 text-zinc-500 hover:text-red-400 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ) : (
            <div>
              <svg className="w-8 h-8 text-zinc-600 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              <p className="text-sm text-zinc-500">Drop JD file here or click to browse</p>
              <p className="text-xs text-zinc-600 mt-1">PDF, TXT, or DOCX</p>
            </div>
          )}
        </div>
      </div>

      {/* Resume Upload */}
      <div>
        <label className="block text-sm font-medium text-zinc-400 mb-2">
          Candidate Resumes
        </label>
        <div
          onDragOver={(e) => { e.preventDefault(); setResumeDragOver(true); }}
          onDragLeave={() => setResumeDragOver(false)}
          onDrop={handleResumeDrop}
          className={`
            relative border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 cursor-pointer
            ${resumeDragOver
              ? "border-blue-500 bg-blue-500/5"
              : resumeFiles.length > 0
                ? "border-emerald-600/40 bg-emerald-900/10"
                : "border-zinc-700 bg-zinc-900/50 hover:border-zinc-500"
            }
          `}
        >
          <input
            type="file"
            accept=".pdf,.txt,.docx"
            multiple
            onChange={handleResumesChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            id="resume-upload"
          />
          {resumeFiles.length > 0 ? (
            <div className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-zinc-300">{resumeFiles.length} file{resumeFiles.length > 1 ? "s" : ""} selected</span>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setResumeFiles([]); }}
                className="ml-2 text-zinc-500 hover:text-red-400 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ) : (
            <div>
              <svg className="w-8 h-8 text-zinc-600 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75" />
              </svg>
              <p className="text-sm text-zinc-500">Drop resume files or click to browse</p>
              <p className="text-xs text-zinc-600 mt-1">Multiple PDFs supported</p>
            </div>
          )}
        </div>
      </div>

      {/* Submit */}
      <div className="lg:col-span-2 flex items-center gap-4">
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className={`
            px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
            ${canSubmit
              ? "bg-blue-600 hover:bg-blue-500 text-white shadow-sm shadow-blue-900/30"
              : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
            }
          `}
        >
          {isProcessing ? (
            <span className="flex items-center gap-2">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Processing…
            </span>
          ) : (
            "Run Evaluation"
          )}
        </button>
        <span className="text-xs text-zinc-600">
          {jdFile ? "1 JD" : "No JD"} · {resumeFiles.length} resume{resumeFiles.length !== 1 ? "s" : ""}
        </span>
      </div>
    </div>
  );
}
