"use client";

import { useState, useEffect, useCallback } from "react";
import {
  CandidateEvaluation,
  EvaluationResult,
  PairwiseComparison,
  ProcessingStatus,
} from "@/types";
import {
  submitEvaluation,
  getCandidateDetail,
  getPairwiseComparison,
} from "@/services/api";
import {
  getMockEvaluationResult,
  getMockProcessingStatus,
} from "@/data/mock-data";
import UploadPanel from "@/components/UploadPanel";
import ProcessingBar from "@/components/ProcessingBar";
import TopThree from "@/components/TopThree";
import RankingTable from "@/components/RankingTable";
import CandidateDetail from "@/components/CandidateDetail";
import ComparisonView from "@/components/ComparisonView";

export default function RecruiterDashboard() {
  // Evaluation Result State (initialized with mock evaluation for immediate evaluation)
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null);
  const [status, setStatus] = useState<ProcessingStatus>(getMockProcessingStatus("idle"));
  const [isProcessing, setIsProcessing] = useState(false);

  // Active views / selections
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateEvaluation | null>(null);
  
  // Pairwise comparison state
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonCandidateAId, setComparisonCandidateAId] = useState<string>("MOCK-CAND-001");
  const [comparisonCandidateBId, setComparisonCandidateBId] = useState<string>("MOCK-CAND-002");
  const [currentComparison, setCurrentComparison] = useState<PairwiseComparison | null>(null);

  // Upload panel visibility
  const [showUploadPanel, setShowUploadPanel] = useState(false);

  // Initial load: populate with default mock dataset
  useEffect(() => {
    const defaultData = getMockEvaluationResult();
    setEvaluationResult(defaultData);
    if (defaultData.candidates.length > 0) {
      setSelectedCandidateId(defaultData.candidates[0].candidate_id);
      setSelectedCandidate(defaultData.candidates[0]);
    }
  }, []);

  // Update selected candidate details when selectedCandidateId changes
  useEffect(() => {
    if (!selectedCandidateId) {
      setSelectedCandidate(null);
      return;
    }
    getCandidateDetail(selectedCandidateId).then((candidate) => {
      setSelectedCandidate(candidate);
    });
  }, [selectedCandidateId]);

  // Update comparison when candidate IDs change
  useEffect(() => {
    if (isComparing && comparisonCandidateAId && comparisonCandidateBId) {
      getPairwiseComparison(comparisonCandidateAId, comparisonCandidateBId).then(
        (comp) => {
          setCurrentComparison(comp);
        }
      );
    }
  }, [isComparing, comparisonCandidateAId, comparisonCandidateBId]);

  // Run evaluation flow (simulates pipeline execution)
  const handleRunEvaluation = useCallback(
    async (jdFile: File | null, resumeFiles: File[]) => {
      setIsProcessing(true);
      setShowUploadPanel(false);

      const stages: ProcessingStatus["stage"][] = [
        "uploading",
        "parsing",
        "matching",
        "ranking",
        "complete",
      ];

      for (const stage of stages) {
        setStatus(getMockProcessingStatus(stage));
        await new Promise((resolve) => setTimeout(resolve, 500));
      }

      const res = await submitEvaluation(jdFile, resumeFiles);
      setEvaluationResult(res);
      if (res.candidates.length > 0) {
        setSelectedCandidateId(res.candidates[0].candidate_id);
      }
      setIsProcessing(false);
    },
    []
  );

  // Handle direct compare click from ranking table or detail view
  const handleLaunchCompare = (candidateAId: string, candidateBId?: string) => {
    setComparisonCandidateAId(candidateAId);
    if (candidateBId) {
      setComparisonCandidateBId(candidateBId);
    } else if (evaluationResult && evaluationResult.candidates.length > 1) {
      const other = evaluationResult.candidates.find(
        (c) => c.candidate_id !== candidateAId
      );
      if (other) setComparisonCandidateBId(other.candidate_id);
    }
    setIsComparing(true);
  };

  const candidates = evaluationResult?.candidates || [];
  const candidateA = candidates.find((c) => c.candidate_id === comparisonCandidateAId);
  const candidateB = candidates.find((c) => c.candidate_id === comparisonCandidateBId);

  return (
    <div className="min-h-screen flex flex-col bg-zinc-950 text-zinc-100">
      {/* Top Navigation Bar */}
      <header className="border-b border-zinc-800 bg-zinc-900/90 sticky top-0 z-30 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-sm">
              N
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-zinc-100 text-base tracking-tight">
                  Nexora
                </span>
                <span className="text-zinc-600">/</span>
                <span className="text-xs text-zinc-400 font-medium">
                  Smart Shortlisting Engine
                </span>
              </div>
              <p className="text-[11px] text-zinc-500 font-mono">
                Recruiter Intelligence Dashboard
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Mock Data Banner Badge */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded border border-amber-500/30 bg-amber-500/10 text-amber-300 text-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              <span>Synthetic Mock Data</span>
            </div>

            {/* Upload toggle */}
            <button
              onClick={() => setShowUploadPanel(!showUploadPanel)}
              className="text-xs font-medium px-3 py-1.5 rounded-md border border-zinc-700 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors flex items-center gap-1.5"
            >
              <svg className="w-4 h-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              <span>{showUploadPanel ? "Hide Ingestion" : "Upload Documents"}</span>
            </button>

            {/* Compare Tool */}
            <button
              onClick={() => setIsComparing(true)}
              className="text-xs font-medium px-3 py-1.5 rounded-md border border-blue-500/40 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 transition-colors flex items-center gap-1.5"
            >
              <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
              </svg>
              <span>Compare Candidates</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Upload Drawer (Collapsible) */}
        {showUploadPanel && (
          <section className="rounded-xl border border-zinc-800 bg-zinc-900/90 p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div>
                <h2 className="text-sm font-semibold text-zinc-200">
                  Document Ingestion & Batch Evaluation
                </h2>
                <p className="text-xs text-zinc-500">
                  Upload 1 Job Description PDF/text and batch candidate resumes to trigger ranking
                </p>
              </div>
              <button
                onClick={() => setShowUploadPanel(false)}
                className="text-zinc-500 hover:text-zinc-300 p-1 text-xs"
              >
                ✕ Close
              </button>
            </div>
            <UploadPanel onSubmit={handleRunEvaluation} isProcessing={isProcessing} />
          </section>
        )}

        {/* Processing Progress Status */}
        {isProcessing && <ProcessingBar status={status} />}

        {/* Job Description Summary Banner */}
        {evaluationResult && (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs uppercase tracking-wider font-semibold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                  Target Role
                </span>
                <h1 className="text-base font-semibold text-zinc-100">
                  {evaluationResult.job_description.title}
                </h1>
              </div>
              <p className="text-xs text-zinc-400 mt-1 max-w-3xl line-clamp-1">
                {evaluationResult.job_description.raw_text}
              </p>
            </div>

            <div className="flex items-center gap-4 shrink-0 text-xs border-t md:border-t-0 pt-2 md:pt-0 border-zinc-800">
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Pool Size</span>
                <span className="font-mono font-semibold text-zinc-200">
                  {candidates.length} Candidates
                </span>
              </div>
              <div className="w-px h-7 bg-zinc-800" />
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Required</span>
                <span className="font-mono font-semibold text-blue-400">
                  {evaluationResult.job_description.required_skills.length} Skills
                </span>
              </div>
              <div className="w-px h-7 bg-zinc-800" />
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Preferred</span>
                <span className="font-mono font-semibold text-teal-400">
                  {evaluationResult.job_description.preferred_skills.length} Skills
                </span>
              </div>
              <div className="w-px h-7 bg-zinc-800" />
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Engine Latency</span>
                <span className="font-mono text-zinc-400">
                  {evaluationResult.processing_time_ms}ms
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Top 3 Candidates Section */}
        {candidates.length > 0 && (
          <TopThree
            candidates={candidates}
            onSelectCandidate={(id) => {
              setSelectedCandidateId(id);
              setIsComparing(false);
            }}
            onCompareTopTwo={() => handleLaunchCompare("MOCK-CAND-001", "MOCK-CAND-002")}
          />
        )}

        {/* Primary View: Side-by-side or Main table + Detail Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Ranking Table */}
          <div className={`${selectedCandidate || isComparing ? "lg:col-span-7" : "lg:col-span-12"} space-y-4`}>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-zinc-200">
                  Candidate Leaderboard
                </h2>
                <p className="text-xs text-zinc-500">
                  Select candidate row to view detailed evidence dossier or contrastive comparison
                </p>
              </div>
              <span className="text-xs text-zinc-500 font-mono">
                {candidates.length} total applicants
              </span>
            </div>

            <RankingTable
              candidates={candidates}
              selectedId={selectedCandidateId}
              onSelectCandidate={(id) => {
                setSelectedCandidateId(id);
                setIsComparing(false);
              }}
              onCompareWithAnother={(id) => handleLaunchCompare(id)}
            />
          </div>

          {/* Right Column: Candidate Detail or Pairwise Comparison */}
          {(selectedCandidate || isComparing) && (
            <div className="lg:col-span-5 lg:sticky lg:top-24 space-y-4">
              {isComparing && candidateA && candidateB && currentComparison ? (
                <ComparisonView
                  comparison={currentComparison}
                  candidateA={candidateA}
                  candidateB={candidateB}
                  allCandidates={candidates}
                  onSelectCandidateA={(id) => setComparisonCandidateAId(id)}
                  onSelectCandidateB={(id) => setComparisonCandidateBId(id)}
                  onClose={() => setIsComparing(false)}
                />
              ) : selectedCandidate ? (
                <CandidateDetail
                  candidate={selectedCandidate}
                  allCandidates={candidates}
                  onClose={() => setSelectedCandidateId(null)}
                  onCompare={(otherId) =>
                    handleLaunchCompare(selectedCandidate.candidate_id, otherId)
                  }
                />
              ) : null}
            </div>
          )}
        </div>
      </main>

      {/* Professional Recruiter Footer */}
      <footer className="border-t border-zinc-800/80 bg-zinc-950 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-zinc-500">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-zinc-400">Nexora</span>
            <span>•</span>
            <span>Deterministic Scoring Formula: 0.35 × S_req + 0.30 × S_sem + 0.25 × S_lex + 0.10 × S_pref</span>
          </div>
          <div className="font-mono text-[11px] text-zinc-600">
            Contract: CandidateEvaluation JSON · Mock Service Layer Active
          </div>
        </div>
      </footer>
    </div>
  );
}
