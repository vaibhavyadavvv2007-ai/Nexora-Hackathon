"use client";

import { useEffect } from "react";
import { PairwiseComparison, CandidateEvaluation } from "@/types";
import { ScoreBadge } from "./ScoreBar";

interface ComparisonViewProps {
  comparison: PairwiseComparison;
  candidateA: CandidateEvaluation;
  candidateB: CandidateEvaluation;
  allCandidates: CandidateEvaluation[];
  onSelectCandidateA: (id: string) => void;
  onSelectCandidateB: (id: string) => void;
  onClose: () => void;
}

export default function ComparisonView({
  comparison,
  candidateA,
  candidateB,
  allCandidates,
  onSelectCandidateA,
  onSelectCandidateB,
  onClose,
}: ComparisonViewProps) {
  const winnerIsA = comparison.winner_id === candidateA.candidate_id;
  const isTie = comparison.score_delta === 0;

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Pairwise Comparison between ${candidateA.name} and ${candidateB.name}`}
      className="border border-zinc-800 rounded-lg bg-zinc-900/95 shadow-2xl overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800 bg-zinc-900">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-zinc-100">
              Pairwise Contrastive Comparison
            </h3>
            <span className="text-[11px] font-mono uppercase bg-blue-500/10 text-blue-300 border border-blue-500/20 px-2 py-0.5 rounded">
              Why did Candidate A outrank Candidate B?
            </span>
          </div>
          <p className="text-xs text-zinc-500 mt-0.5">
            Objective evidence delta derived from stored evaluation records
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-zinc-500 hover:text-zinc-200 transition-colors p-1.5 rounded-md hover:bg-zinc-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
          aria-label="Close pairwise comparison"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="p-5 space-y-6 max-h-[calc(100vh-220px)] overflow-y-auto">
        {/* Candidate Pickers */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-zinc-950/60 p-3.5 rounded-lg border border-zinc-800/80">
          <div>
            <label htmlFor="select-candidate-a" className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
              Candidate A:
            </label>
            <select
              id="select-candidate-a"
              value={candidateA.candidate_id}
              onChange={(e) => onSelectCandidateA(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            >
              {allCandidates.map((c) => (
                <option key={c.candidate_id} value={c.candidate_id}>
                  Rank #{c.rank} — {c.name} ({Math.round(c.final_score * 100)}%)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="select-candidate-b" className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
              Candidate B:
            </label>
            <select
              id="select-candidate-b"
              value={candidateB.candidate_id}
              onChange={(e) => onSelectCandidateB(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            >
              {allCandidates.map((c) => (
                <option key={c.candidate_id} value={c.candidate_id}>
                  Rank #{c.rank} — {c.name} ({Math.round(c.final_score * 100)}%)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Head-to-Head Visual Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-11 gap-4 items-center">
          {/* Candidate A Column */}
          <div
            className={`
              md:col-span-5 rounded-lg border p-4.5 transition-all
              ${winnerIsA && !isTie
                ? "border-emerald-500/40 bg-emerald-500/5 ring-1 ring-emerald-500/30"
                : "border-zinc-800 bg-zinc-950/50"
              }
            `}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-bold text-zinc-400">
                Rank #{candidateA.rank}
              </span>
              {winnerIsA && !isTie && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Higher Ranked
                </span>
              )}
            </div>
            <h4 className="text-base font-semibold text-zinc-100 mb-1 truncate">
              {candidateA.name}
            </h4>
            <p className="text-xs font-mono text-zinc-500 mb-3">{candidateA.candidate_id}</p>

            <div className="flex items-center justify-between pt-3 border-t border-zinc-800/80">
              <span className="text-xs text-zinc-400">Final Score:</span>
              <ScoreBadge value={candidateA.final_score} size="lg" />
            </div>

            <div className="mt-3 space-y-1.5 text-xs text-zinc-400 pt-3 border-t border-zinc-800/50">
              <div className="flex justify-between">
                <span>Req. Skills:</span>
                <span className="font-mono text-zinc-200">
                  {Math.round(candidateA.required_coverage * 100)}% ({candidateA.matched_required.length} matched)
                </span>
              </div>
              <div className="flex justify-between">
                <span>Semantic Score:</span>
                <span className="font-mono text-zinc-200">{Math.round(candidateA.semantic_score * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Keyword Score:</span>
                <span className="font-mono text-zinc-200">{Math.round(candidateA.lexical_score * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Pref. Skills:</span>
                <span className="font-mono text-zinc-200">{Math.round(candidateA.preferred_coverage * 100)}%</span>
              </div>
            </div>
          </div>

          {/* VS & Deltas Column */}
          <div className="md:col-span-1 flex flex-col items-center justify-center text-center py-2">
            <span className="text-xs font-bold text-zinc-400 bg-zinc-800 px-2 py-1 rounded-full border border-zinc-700">
              VS
            </span>
            <div className="my-2 hidden md:block w-px h-12 bg-zinc-800" />
            <div className="text-[11px] font-mono text-blue-400 font-bold mt-1">
              Δ {Math.round(comparison.score_delta * 100)}%
            </div>
          </div>

          {/* Candidate B Column */}
          <div
            className={`
              md:col-span-5 rounded-lg border p-4.5 transition-all
              ${!winnerIsA && !isTie
                ? "border-emerald-500/40 bg-emerald-500/5 ring-1 ring-emerald-500/30"
                : "border-zinc-800 bg-zinc-950/50"
              }
            `}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-bold text-zinc-400">
                Rank #{candidateB.rank}
              </span>
              {!winnerIsA && !isTie && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Higher Ranked
                </span>
              )}
            </div>
            <h4 className="text-base font-semibold text-zinc-100 mb-1 truncate">
              {candidateB.name}
            </h4>
            <p className="text-xs font-mono text-zinc-500 mb-3">{candidateB.candidate_id}</p>

            <div className="flex items-center justify-between pt-3 border-t border-zinc-800/80">
              <span className="text-xs text-zinc-400">Final Score:</span>
              <ScoreBadge value={candidateB.final_score} size="lg" />
            </div>

            <div className="mt-3 space-y-1.5 text-xs text-zinc-400 pt-3 border-t border-zinc-800/50">
              <div className="flex justify-between">
                <span>Req. Skills:</span>
                <span className="font-mono text-zinc-200">
                  {Math.round(candidateB.required_coverage * 100)}% ({candidateB.matched_required.length} matched)
                </span>
              </div>
              <div className="flex justify-between">
                <span>Semantic Score:</span>
                <span className="font-mono text-zinc-200">{Math.round(candidateB.semantic_score * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Keyword Score:</span>
                <span className="font-mono text-zinc-200">{Math.round(candidateB.lexical_score * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Pref. Skills:</span>
                <span className="font-mono text-zinc-200">{Math.round(candidateB.preferred_coverage * 100)}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Delta Metrics Strip */}
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded border border-zinc-800 bg-zinc-950/40 p-3 text-center">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider block mb-1">
              Required Coverage Δ
            </span>
            <span className="text-sm font-mono font-bold text-zinc-200">
              {comparison.required_skill_delta >= 0 ? "+" : ""}
              {Math.round(comparison.required_skill_delta * 100)}%
            </span>
          </div>
          <div className="rounded border border-zinc-800 bg-zinc-950/40 p-3 text-center">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider block mb-1">
              Semantic Alignment Δ
            </span>
            <span className="text-sm font-mono font-bold text-zinc-200">
              {comparison.semantic_delta >= 0 ? "+" : ""}
              {Math.round(comparison.semantic_delta * 100)}%
            </span>
          </div>
          <div className="rounded border border-zinc-800 bg-zinc-950/40 p-3 text-center">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider block mb-1">
              Overall Score Δ
            </span>
            <span className="text-sm font-mono font-bold text-blue-400">
              {comparison.score_delta >= 0 ? "+" : ""}
              {Math.round(comparison.score_delta * 100)} pts
            </span>
          </div>
        </div>

        {/* Missing Skills Differential */}
        {comparison.missing_skills_diff && (
          <section className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-4 space-y-3">
            <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
              <span>Missing Required Skills Differential</span>
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3 rounded bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-400 block mb-1.5 font-medium">
                  Skills Missing only in {candidateA.name}:
                </span>
                {comparison.missing_skills_diff.only_a_missing.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {comparison.missing_skills_diff.only_a_missing.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-red-950/40 text-red-300 border border-red-500/30 text-[11px]">
                        ✕ {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-zinc-500 italic text-[11px]">None (No unique gaps)</span>
                )}
              </div>

              <div className="p-3 rounded bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-400 block mb-1.5 font-medium">
                  Skills Missing only in {candidateB.name}:
                </span>
                {comparison.missing_skills_diff.only_b_missing.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {comparison.missing_skills_diff.only_b_missing.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-red-950/40 text-red-300 border border-red-500/30 text-[11px]">
                        ✕ {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-zinc-500 italic text-[11px]">None (No unique gaps)</span>
                )}
              </div>
            </div>
          </section>
        )}

        {/* Narrative Decision Rationale (From Backend Contract) */}
        <section>
          <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
            Why {candidateA.name} {winnerIsA ? "outranked" : "ranked below"} {candidateB.name}?
          </h4>
          <div className="text-sm text-zinc-200 leading-relaxed bg-zinc-950/90 rounded-lg p-4 border border-zinc-800">
            {comparison.explanation}
          </div>
        </section>

        {/* Key Advantages Breakdown */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-4">
            <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <span className="text-emerald-400">✓</span>
              <span>{candidateA.name} Key Differentials:</span>
            </h4>
            <ul className="space-y-1.5 text-xs text-zinc-400">
              {comparison.advantages_a.map((adv, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">•</span>
                  <span>{adv}</span>
                </li>
              ))}
              {comparison.advantages_a.length === 0 && (
                <li className="italic text-zinc-500">No distinct advantages identified.</li>
              )}
            </ul>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-4">
            <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <span className="text-emerald-400">✓</span>
              <span>{candidateB.name} Key Differentials:</span>
            </h4>
            <ul className="space-y-1.5 text-xs text-zinc-400">
              {comparison.advantages_b.map((adv, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">•</span>
                  <span>{adv}</span>
                </li>
              ))}
              {comparison.advantages_b.length === 0 && (
                <li className="italic text-zinc-500">No distinct advantages identified.</li>
              )}
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
