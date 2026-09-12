"use client";

import { useState, useEffect, useCallback } from "react";
import {
  CandidateEvaluation,
  DataSourceMode,
  EvaluationResult,
  PairwiseComparison,
  ProcessingStatus,
} from "@/types";
import {
  uploadJobDescription,
  uploadResumes,
  startAnalysis,
  getAnalysisStatus,
  getRankings,
  getCandidate,
  compareCandidates,
  getDataSourceMode,
  setDataSourceMode,
  API_BASE_URL,
} from "@/services/api";
import {
  getMockEvaluationResult,
  getMockProcessingStatus,
} from "@/lib/mock/candidateEvaluations";
import UploadPanel from "@/components/UploadPanel";
import ProcessingBar from "@/components/ProcessingBar";
import TopThree from "@/components/TopThree";
import RankingTable from "@/components/RankingTable";
import CandidateDetail from "@/components/CandidateDetail";
import ComparisonView from "@/components/ComparisonView";

export default function RecruiterDashboard() {
  // Runtime Data Source Mode (Mock vs Live API)
  const [dataMode, setDataMode] = useState<DataSourceMode>(() => getDataSourceMode());

  // Evaluation Result State
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null);
  const [status, setStatus] = useState<ProcessingStatus>(getMockProcessingStatus("idle"));
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Selected candidate for deep-dive detail dossier
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateEvaluation | null>(null);

  // Pairwise comparison state
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonCandidateAId, setComparisonCandidateAId] = useState<string>("MOCK-CAND-001");
  const [comparisonCandidateBId, setComparisonCandidateBId] = useState<string>("MOCK-CAND-002");
  const [currentComparison, setCurrentComparison] = useState<PairwiseComparison | null>(null);

  // Ingestion Drawer visibility
  const [showUploadPanel, setShowUploadPanel] = useState(false);

  // Synchronize data source mode on mount
  useEffect(() => {
    // Initial load: populate with initial evaluation dataset
    getRankings()
      .then((res) => {
        if (res && res.candidates && res.candidates.length > 0) {
          setEvaluationResult(res);
          setSelectedCandidateId(res.candidates[0].candidate_id);
          setSelectedCandidate(res.candidates[0]);
          if (res.candidates.length >= 2) {
            setComparisonCandidateAId(res.candidates[0].candidate_id);
            setComparisonCandidateBId(res.candidates[1].candidate_id);
          }
        } else {
          // No backend evaluations yet, load rich demo fixture
          const fallback = getMockEvaluationResult();
          setEvaluationResult(fallback);
          if (fallback.candidates.length > 0) {
            setSelectedCandidateId(fallback.candidates[0].candidate_id);
            setSelectedCandidate(fallback.candidates[0]);
            if (fallback.candidates.length >= 2) {
              setComparisonCandidateAId(fallback.candidates[0].candidate_id);
              setComparisonCandidateBId(fallback.candidates[1].candidate_id);
            }
          }
        }
      })
      .catch((err) => {
        // Fallback to local mock if backend is not running
        console.warn("Backend unavailable, loading local mock fixture:", err);
        const fallback = getMockEvaluationResult();
        setEvaluationResult(fallback);
        if (fallback.candidates.length > 0) {
          setSelectedCandidateId(fallback.candidates[0].candidate_id);
          setSelectedCandidate(fallback.candidates[0]);
          if (fallback.candidates.length >= 2) {
            setComparisonCandidateAId(fallback.candidates[0].candidate_id);
            setComparisonCandidateBId(fallback.candidates[1].candidate_id);
          }
        }
      });
  }, []);

  // Mode switcher handler
  const handleToggleDataMode = (newMode: DataSourceMode) => {
    setDataSourceMode(newMode);
    setDataMode(newMode);
    setErrorMessage(null);

    getRankings()
      .then((res) => {
        if (res && res.candidates && res.candidates.length > 0) {
          setEvaluationResult(res);
          setSelectedCandidateId(res.candidates[0].candidate_id);
          setSelectedCandidate(res.candidates[0]);
        } else {
          const fallback = getMockEvaluationResult();
          setEvaluationResult(fallback);
          if (fallback.candidates.length > 0) {
            setSelectedCandidateId(fallback.candidates[0].candidate_id);
            setSelectedCandidate(fallback.candidates[0]);
          }
        }
      })
      .catch((err) => {
        setErrorMessage(
          newMode === "api"
            ? `Cannot connect to FastAPI backend at ${API_BASE_URL}. Ensure server is running on port 8000 or switch back to Mock Mode.`
            : `Failed to load mock data: ${err.message}`
        );
      });
  };

  // Fetch candidate details when selectedCandidateId changes
  useEffect(() => {
    let isCancelled = false;
    if (selectedCandidateId) {
      const existing = evaluationResult?.candidates.find(
        (c) => c.candidate_id === selectedCandidateId
      );
      if (existing) {
        setSelectedCandidate(existing);
      }

      getCandidate(selectedCandidateId)
        .then((candidate) => {
          if (!isCancelled && candidate) {
            setSelectedCandidate(candidate);
          }
        })
        .catch((err) => {
          console.warn(`Could not load candidate '${selectedCandidateId}':`, err);
        });
    }
    return () => {
      isCancelled = true;
    };
  }, [selectedCandidateId, evaluationResult]);

  // Fetch comparison when comparison candidate IDs change
  useEffect(() => {
    if (isComparing && comparisonCandidateAId && comparisonCandidateBId) {
      compareCandidates(comparisonCandidateAId, comparisonCandidateBId)
        .then((comp) => {
          if (comp) {
            setCurrentComparison(comp);
          }
        })
        .catch((err) => {
          console.warn("Could not compare candidates:", err);
        });
    }
  }, [isComparing, comparisonCandidateAId, comparisonCandidateBId]);

  // Run full evaluation pipeline
  const handleRunEvaluation = useCallback(
    async (jdFile: File | null, resumeFiles: File[]) => {
      setIsProcessing(true);
      setErrorMessage(null);
      setShowUploadPanel(false);

      try {
        if (dataMode === "mock") {
          // Simulate the 5 deterministic pipeline stages with telemetry
          const stages: ProcessingStatus["stage"][] = [
            "uploading",
            "parsing",
            "matching",
            "ranking",
            "complete",
          ];

          for (const stage of stages) {
            setStatus(getMockProcessingStatus(stage));
            await new Promise((resolve) => setTimeout(resolve, 550));
          }

          const res = await getRankings();
          setEvaluationResult(res);
          if (res.candidates.length > 0) {
            setSelectedCandidateId(res.candidates[0].candidate_id);
          }
        } else {
          // Real backend flow
          if (jdFile) {
            await uploadJobDescription(jdFile);
          }
          if (resumeFiles.length > 0) {
            await uploadResumes(resumeFiles);
          }
          const task = await startAnalysis("active-job", resumeFiles);

          // Poll status
          let isDone = false;
          while (!isDone) {
            const currentStatus = await getAnalysisStatus(task.task_id);
            setStatus(currentStatus);
            if (currentStatus.stage === "complete" || currentStatus.stage === "error") {
              isDone = true;
            } else {
              await new Promise((r) => setTimeout(r, 1000));
            }
          }

          const res = await getRankings();
          setEvaluationResult(res);
          if (res.candidates.length > 0) {
            setSelectedCandidateId(res.candidates[0].candidate_id);
          }
        }
      } catch (err: unknown) {
        setErrorMessage(
          err instanceof Error
            ? err.message
            : "Pipeline execution failed. Please verify files and service status."
        );
        setStatus(getMockProcessingStatus("error"));
      } finally {
        setIsProcessing(false);
      }
    },
    [dataMode]
  );

  // Load sample evaluation dataset
  const handleLoadSample = () => {
    const sample = getMockEvaluationResult();
    setEvaluationResult(sample);
    if (sample.candidates.length > 0) {
      setSelectedCandidateId(sample.candidates[0].candidate_id);
      setSelectedCandidate(sample.candidates[0]);
      if (sample.candidates.length >= 2) {
        setComparisonCandidateAId(sample.candidates[0].candidate_id);
        setComparisonCandidateBId(sample.candidates[1].candidate_id);
      }
    }
    setStatus(getMockProcessingStatus("complete"));
    setShowUploadPanel(false);
  };

  // Launch comparison tool
  const handleLaunchCompare = (candidateAId: string, candidateBId?: string) => {
    setComparisonCandidateAId(candidateAId);
    if (candidateBId) {
      setComparisonCandidateBId(candidateBId);
    } else if (evaluationResult && evaluationResult.candidates.length > 1) {
      const other = evaluationResult.candidates.find((c) => c.candidate_id !== candidateAId);
      if (other) setComparisonCandidateBId(other.candidate_id);
    }
    setIsComparing(true);
  };

  const candidates = evaluationResult?.candidates || [];
  const candidateA = candidates.find((c) => c.candidate_id === comparisonCandidateAId);
  const candidateB = candidates.find((c) => c.candidate_id === comparisonCandidateBId);

  return (
    <div className="min-h-screen flex flex-col bg-zinc-950 text-zinc-100 antialiased selection:bg-blue-600/30">
      {/* Top Application Header */}
      <header className="border-b border-zinc-800 bg-zinc-900/90 sticky top-0 z-30 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-blue-600 flex items-center justify-center font-bold text-white shadow-sm tracking-tight text-sm">
              NX
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-zinc-100 text-sm tracking-tight">
                  Nexora
                </span>
                <span className="text-zinc-600">/</span>
                <span className="text-xs text-zinc-400 font-medium">
                  Smart Shortlisting Engine
                </span>
              </div>
              <p className="text-[10px] text-zinc-500 font-mono">
                Technical Candidate Evaluation & Evidence Audit
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 sm:gap-3">
            {/* Mode Switcher: Mock vs Live API */}
            <div className="flex items-center bg-zinc-950 border border-zinc-800 rounded-md p-0.5 text-xs">
              <button
                onClick={() => handleToggleDataMode("mock")}
                className={`px-2.5 py-1 rounded transition-colors font-medium flex items-center gap-1.5 ${
                  dataMode === "mock"
                    ? "bg-zinc-800 text-amber-300 font-semibold shadow-xs"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
                title="Use programmatic mock fixtures for offline testing"
              >
                <span className={`w-1.5 h-1.5 rounded-full ${dataMode === "mock" ? "bg-amber-400" : "bg-zinc-600"}`} />
                <span>Mock Mode</span>
              </button>
              <button
                onClick={() => handleToggleDataMode("api")}
                className={`px-2.5 py-1 rounded transition-colors font-medium flex items-center gap-1.5 ${
                  dataMode === "api"
                    ? "bg-zinc-800 text-emerald-300 font-semibold shadow-xs"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
                title={`Connect to FastAPI backend at ${API_BASE_URL}`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${dataMode === "api" ? "bg-emerald-400 animate-pulse" : "bg-zinc-600"}`} />
                <span>Live API Mode</span>
              </button>
            </div>

            {/* Upload Drawer Toggle */}
            <button
              onClick={() => setShowUploadPanel(!showUploadPanel)}
              className="text-xs font-medium px-3 py-1.5 rounded-md border border-zinc-700 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors flex items-center gap-1.5"
              aria-expanded={showUploadPanel}
            >
              <svg className="w-3.5 h-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              <span>{showUploadPanel ? "Close Panel" : "Ingest Documents"}</span>
            </button>

            {/* Pairwise Comparison Tool Trigger */}
            <button
              onClick={() => setIsComparing(true)}
              className="text-xs font-semibold px-3 py-1.5 rounded-md border border-blue-500/40 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <svg className="w-3.5 h-3.5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
              </svg>
              <span>Compare Pair</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Error / Offline Alert Banner */}
        {errorMessage && (
          <div
            role="alert"
            className="rounded-lg border border-red-500/40 bg-red-950/30 p-4 text-xs text-red-200 flex items-start justify-between gap-3 shadow-md"
          >
            <div className="flex items-start gap-2.5">
              <svg className="w-5 h-5 text-red-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <div>
                <span className="font-semibold text-red-100 block">Service Notice:</span>
                <span className="leading-relaxed">{errorMessage}</span>
              </div>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-red-400 hover:text-red-200 p-1 text-xs"
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        {/* Collapsible Document Ingestion Drawer */}
        {showUploadPanel && (
          <section
            aria-label="Document Ingestion Area"
            className="rounded-xl border border-zinc-800 bg-zinc-900/90 p-5 shadow-lg space-y-4"
          >
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div>
                <h2 className="text-sm font-semibold text-zinc-200">
                  Document Ingestion & Pipeline Configuration
                </h2>
                <p className="text-xs text-zinc-500">
                  Upload 1 Job Description and 10–25 Candidate Resumes for dual-signal evaluation
                </p>
              </div>
              <button
                onClick={() => setShowUploadPanel(false)}
                className="text-zinc-500 hover:text-zinc-300 p-1 text-xs font-mono"
              >
                ✕ Close
              </button>
            </div>
            <UploadPanel
              onSubmit={handleRunEvaluation}
              onLoadSample={handleLoadSample}
              isProcessing={isProcessing}
            />
          </section>
        )}

        {/* Pipeline Processing State Indicator */}
        {isProcessing && (
          <ProcessingBar
            status={status}
            onRetry={() => handleRunEvaluation(null, [])}
          />
        )}

        {/* Active Job Description Summary Banner */}
        {evaluationResult ? (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] uppercase tracking-wider font-semibold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
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
                  {candidates.length} Applicants
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
                <span className="text-zinc-500 block text-[10px] uppercase">Latency</span>
                <span className="font-mono text-zinc-400">
                  {evaluationResult.processing_time_ms}ms
                </span>
              </div>
            </div>
          </div>
        ) : (
          /* Empty State when no evaluation is active */
          <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-900/30 p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center mx-auto text-zinc-400 text-xl font-bold">
              📄
            </div>
            <h2 className="text-base font-semibold text-zinc-200">
              No Evaluation Results Loaded
            </h2>
            <p className="text-xs text-zinc-500 max-w-md mx-auto leading-relaxed">
              Upload a Job Description and candidate resumes to run the dual-signal shortlisting pipeline, or load the pre-computed hackathon dataset.
            </p>
            <div className="pt-2 flex items-center justify-center gap-3">
              <button
                onClick={() => setShowUploadPanel(true)}
                className="text-xs font-semibold px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-500 text-white"
              >
                Upload Documents
              </button>
              <button
                onClick={handleLoadSample}
                className="text-xs font-semibold px-4 py-2 rounded-md border border-zinc-700 bg-zinc-800 hover:bg-zinc-700 text-zinc-200"
              >
                Load Hackathon Sample
              </button>
            </div>
          </div>
        )}

        {/* Top 3 Executive Shortlist */}
        {candidates.length > 0 && (
          <TopThree
            candidates={candidates}
            onSelectCandidate={(id) => {
              setSelectedCandidateId(id);
              setIsComparing(false);
            }}
            onComparePair={(idA, idB) => {
              setComparisonCandidateAId(idA);
              setComparisonCandidateBId(idB);
              setIsComparing(true);
            }}
          />
        )}

        {/* Candidate Leaderboard + Detail Dossier Layout */}
        {candidates.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Candidate Ranking Table (Leaderboard) */}
            <div className={`${selectedCandidate || isComparing ? "lg:col-span-7" : "lg:col-span-12"} space-y-3`}>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold text-zinc-200">
                    Candidate Shortlisting Leaderboard
                  </h2>
                  <p className="text-xs text-zinc-500">
                    Deterministic ranking derived from: 0.35·Req + 0.30·Sem + 0.25·Lex + 0.10·Pref
                  </p>
                </div>
                <span className="text-xs text-zinc-500 font-mono">
                  {candidates.length} profiles evaluated
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

            {/* Right Pane: Candidate Detail Dossier or Pairwise Comparison */}
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
                    onClose={() => {
                      setSelectedCandidateId(null);
                      setSelectedCandidate(null);
                    }}
                    onCompare={(otherId) =>
                      handleLaunchCompare(selectedCandidate.candidate_id, otherId)
                    }
                  />
                ) : null}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Recruiter System Status Footer */}
      <footer className="border-t border-zinc-800/80 bg-zinc-950 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-zinc-500">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-zinc-300">Nexora Engine</span>
            <span>•</span>
            <span>Formula: 0.35·S_req + 0.30·S_sem + 0.25·S_lex + 0.10·S_pref</span>
            <span>•</span>
            <span className="font-mono text-[11px] text-zinc-400">
              Active Mode: {dataMode.toUpperCase()}
            </span>
          </div>
          <div className="font-mono text-[11px] text-zinc-600">
            No LLM hallucination · Stored evidence verification
          </div>
        </div>
      </footer>
    </div>
  );
}
