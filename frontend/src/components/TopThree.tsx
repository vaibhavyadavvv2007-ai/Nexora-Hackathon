"use client";

import { CandidateEvaluation } from "@/types";
import { ScoreBadge } from "./ScoreBar";

interface TopThreeProps {
  candidates: CandidateEvaluation[];
  onSelectCandidate: (id: string) => void;
  onComparePair?: (idA: string, idB: string) => void;
}

export default function TopThree({
  candidates,
  onSelectCandidate,
  onComparePair,
}: TopThreeProps) {
  const top3 = candidates
    .filter((c) => c.rank <= 3)
    .sort((a, b) => a.rank - b.rank);

  if (top3.length === 0) return null;

  const rankThemes = [
    {
      ring: "border-amber-500/40 bg-amber-500/5 hover:border-amber-500/70",
      rankBadge: "bg-amber-500/20 text-amber-300 border-amber-500/30",
      icon: "🥇",
    },
    {
      ring: "border-zinc-400/30 bg-zinc-400/5 hover:border-zinc-400/60",
      rankBadge: "bg-zinc-400/20 text-zinc-200 border-zinc-400/30",
      icon: "🥈",
    },
    {
      ring: "border-orange-500/30 bg-orange-500/5 hover:border-orange-500/60",
      rankBadge: "bg-orange-500/20 text-orange-300 border-orange-500/30",
      icon: "🥉",
    },
  ];

  return (
    <section aria-label="Top 3 Shortlisted Candidates">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div>
          <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
            <span>Top-3 Executive Shortlist</span>
            <span className="text-[10px] bg-blue-500/10 text-blue-300 px-1.5 py-0.2 rounded border border-blue-500/20 font-mono">
              Deterministic Fusion
            </span>
          </h3>
          <p className="text-xs text-zinc-500">
            Highest ranking profiles based on verified evidence and requirement coverage
          </p>
        </div>
        {top3.length >= 2 && onComparePair && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => onComparePair(top3[0].candidate_id, top3[1].candidate_id)}
              className="text-xs px-2.5 py-1 rounded border border-blue-500/40 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 transition-colors font-mono"
            >
              Compare #1 vs #2 →
            </button>
            {top3.length >= 3 && (
              <button
                onClick={() => onComparePair(top3[1].candidate_id, top3[2].candidate_id)}
                className="text-xs px-2.5 py-1 rounded border border-zinc-700 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-colors font-mono hidden md:inline"
              >
                #2 vs #3
              </button>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        {top3.map((c, i) => {
          const theme = rankThemes[i];

          return (
            <div
              key={c.candidate_id}
              onClick={() => onSelectCandidate(c.candidate_id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectCandidate(c.candidate_id);
                }
              }}
              className={`
                text-left rounded-lg border ${theme.ring} p-4
                transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/40 cursor-pointer
                flex flex-col justify-between focus:outline-none focus:ring-1 focus:ring-blue-500
              `}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{theme.icon}</span>
                    <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded border ${theme.rankBadge}`}>
                      Rank #{c.rank}
                    </span>
                  </div>
                  <ScoreBadge value={c.final_score} size="md" />
                </div>

                <h4 className="text-sm font-semibold text-zinc-100 mb-1 line-clamp-1">
                  {c.name}
                </h4>

                <p className="text-xs text-zinc-400 leading-relaxed line-clamp-3 mb-3">
                  {c.explanation}
                </p>
              </div>

              <div className="pt-2.5 border-t border-zinc-800/80 grid grid-cols-3 gap-2 text-center text-zinc-400">
                <div className="bg-zinc-900/60 rounded p-1.5 border border-zinc-800/50">
                  <span className="text-[10px] text-zinc-500 uppercase block">Required</span>
                  <span className="text-xs font-mono font-medium text-zinc-200">
                    {Math.round(c.required_coverage * 100)}%
                  </span>
                </div>
                <div className="bg-zinc-900/60 rounded p-1.5 border border-zinc-800/50">
                  <span className="text-[10px] text-zinc-500 uppercase block">Semantic</span>
                  <span className="text-xs font-mono font-medium text-zinc-200">
                    {Math.round(c.semantic_score * 100)}%
                  </span>
                </div>
                <div className="bg-zinc-900/60 rounded p-1.5 border border-zinc-800/50">
                  <span className="text-[10px] text-zinc-500 uppercase block">Keyword</span>
                  <span className="text-xs font-mono font-medium text-zinc-200">
                    {Math.round(c.lexical_score * 100)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
