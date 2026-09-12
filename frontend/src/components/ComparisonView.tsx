"use client";

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

  const nameA = candidateA.name || candidateA.candidate_name;
  const nameB = candidateB.name || candidateB.candidate_name;

  const scoreA = candidateA.final_score ?? candidateA.scores?.final_score ?? 0;
  const scoreB = candidateB.final_score ?? candidateB.scores?.final_score ?? 0;

  const reqA = candidateA.required_coverage ?? candidateA.scores?.required_skill_coverage ?? 0;
  const reqB = candidateB.required_coverage ?? candidateB.scores?.required_skill_coverage ?? 0;

  const semA = candidateA.semantic_score ?? candidateA.scores?.semantic_requirement_alignment ?? 0;
  const semB = candidateB.semantic_score ?? candidateB.scores?.semantic_requirement_alignment ?? 0;

  const keyA = candidateA.lexical_score ?? candidateA.scores?.contextual_lexical_relevance ?? 0;
  const keyB = candidateB.lexical_score ?? candidateB.scores?.contextual_lexical_relevance ?? 0;

  const prefA = candidateA.preferred_coverage ?? candidateA.scores?.preferred_skill_coverage ?? 0;
  const prefB = candidateB.preferred_coverage ?? candidateB.scores?.preferred_skill_coverage ?? 0;

  return (
    <div className="border border-zinc-800 rounded-lg bg-zinc-900/90 shadow-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800 bg-zinc-900">
        <div>
          <h3 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
            <span>Pairwise Contrastive Comparison</span>
            <span className="text-xs font-normal text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">
              Why did Candidate X outrank Candidate Y?
            </span>
          </h3>
          <p className="text-xs text-zinc-500 mt-0.5">
            Deterministic delta breakdown across required skills, semantic alignment, and lexical signals
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-zinc-500 hover:text-zinc-200 transition-colors p-1.5 rounded-md hover:bg-zinc-800"
          aria-label="Close comparison view"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="p-5 space-y-6 max-h-[calc(100vh-220px)] overflow-y-auto">
        {/* Candidate Selectors */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-zinc-950/60 p-3.5 rounded-lg border border-zinc-800/80">
          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1.5">
              Candidate A:
            </label>
            <select
              value={candidateA.candidate_id}
              onChange={(e) => onSelectCandidateA(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {allCandidates.map((c) => (
                <option key={c.candidate_id} value={c.candidate_id}>
                  #{c.rank} {c.name || c.candidate_name} (Score: {Math.round((c.final_score ?? c.scores?.final_score ?? 0) * 100)}%)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1.5">
              Candidate B:
            </label>
            <select
              value={candidateB.candidate_id}
              onChange={(e) => onSelectCandidateB(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {allCandidates.map((c) => (
                <option key={c.candidate_id} value={c.candidate_id}>
                  #{c.rank} {c.name || c.candidate_name} (Score: {Math.round((c.final_score ?? c.scores?.final_score ?? 0) * 100)}%)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Head-to-Head Cards */}
        <div className="grid grid-cols-1 md:grid-cols-11 gap-4 items-center">
          {/* Candidate A Card */}
          <div
            className={`
              md:col-span-5 rounded-lg border p-4.5 transition-all
              ${winnerIsA && !isTie
                ? "border-emerald-500/40 bg-emerald-500/5 ring-1 ring-emerald-500/30"
                : "border-zinc-800 bg-zinc-950/50"}
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
            <h4 className="text-base font-semibold text-zinc-100 mb-1">
              {nameA}
            </h4>
            <p className="text-xs font-mono text-zinc-500 mb-3">{candidateA.candidate_id}</p>

            <div className="flex items-center justify-between pt-3 border-t border-zinc-800/80">
              <span className="text-xs text-zinc-400">Final Score:</span>
              <ScoreBadge value={scoreA} size="lg" />
            </div>

            <div className="mt-3 space-y-1.5 text-xs text-zinc-400 pt-3 border-t border-zinc-800/50">
              <div className="flex justify-between">
                <span>Req. Skills:</span>
                <span className="font-mono text-zinc-200">{Math.round(reqA * 100)}% ({candidateA.matched_required.length} matched)</span>
              </div>
              <div className="flex justify-between">
                <span>Semantic Score:</span>
                <span className="font-mono text-zinc-200">{Math.round(semA * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Keyword Score:</span>
                <span className="font-mono text-zinc-200">{Math.round(keyA * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Pref. Skills:</span>
                <span className="font-mono text-zinc-200">{Math.round(prefA * 100)}%</span>
              </div>
            </div>
          </div>

          {/* VS Delta Column */}
          <div className="md:col-span-1 flex flex-col items-center justify-center text-center py-2">
            <span className="text-xs font-bold text-zinc-500 bg-zinc-800 px-2 py-1 rounded-full border border-zinc-700">
              VS
            </span>
            <div className="my-2 hidden md:block w-px h-12 bg-zinc-800" />
            <div className="text-[11px] font-mono text-blue-400 mt-1">
              Δ {Math.round(comparison.score_delta * 100)}%
            </div>
          </div>

          {/* Candidate B Card */}
          <div
            className={`
              md:col-span-5 rounded-lg border p-4.5 transition-all
              ${!winnerIsA && !isTie
                ? "border-emerald-500/40 bg-emerald-500/5 ring-1 ring-emerald-500/30"
                : "border-zinc-800 bg-zinc-950/50"}
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
            <h4 className="text-base font-semibold text-zinc-100 mb-1">
              {nameB}
            </h4>
            <p className="text-xs font-mono text-zinc-500 mb-3">{candidateB.candidate_id}</p>

            <div className="flex items-center justify-between pt-3 border-t border-zinc-800/80">
              <span className="text-xs text-zinc-400">Final Score:</span>
              <ScoreBadge value={scoreB} size="lg" />
            </div>

            <div className="mt-3 space-y-1.5 text-xs text-zinc-400 pt-3 border-t border-zinc-800/50">
              <div className="flex justify-between">
                <span>Req. Skills:</span>
                <span className="font-mono text-zinc-200">{Math.round(reqB * 100)}% ({candidateB.matched_required.length} matched)</span>
              </div>
              <div className="flex justify-between">
                <span>Semantic Score:</span>
                <span className="font-mono text-zinc-200">{Math.round(semB * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Keyword Score:</span>
                <span className="font-mono text-zinc-200">{Math.round(keyB * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Pref. Skills:</span>
                <span className="font-mono text-zinc-200">{Math.round(prefB * 100)}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Narrative Comparison Explanation */}
        <section>
          <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
            Deterministic Decision Rationale
          </h4>
          <div className="text-sm text-zinc-200 leading-relaxed bg-zinc-950/80 rounded-lg p-4 border border-zinc-800">
            {comparison.explanation}
          </div>
        </section>

        {/* Advantages Breakdown */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/40 p-4">
            <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <span className="text-emerald-400">✓</span>
              {nameA} Strengths & Key Differentials:
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
              {nameB} Strengths & Key Differentials:
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
