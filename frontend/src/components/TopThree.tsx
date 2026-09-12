"use client";

import { CandidateEvaluation } from "@/types";
import { ScoreBadge } from "./ScoreBar";

interface TopThreeProps {
  candidates: CandidateEvaluation[];
  onSelectCandidate: (id: string) => void;
  onCompareTopTwo?: () => void;
}

export default function TopThree({
  candidates,
  onSelectCandidate,
  onCompareTopTwo,
}: TopThreeProps) {
  const top3 = candidates
    .filter((c) => c.rank <= 3)
    .sort((a, b) => a.rank - b.rank);

  if (top3.length === 0) return null;

  const rankThemes = [
    {
      ring: "border-amber-500/40 bg-amber-500/5 hover:border-amber-500/70",
      rankBadge: "bg-amber-500/20 text-amber-300 border-amber-500/30",
      label: "Gold Match",
      icon: "🥇",
    },
    {
      ring: "border-zinc-400/30 bg-zinc-400/5 hover:border-zinc-400/60",
      rankBadge: "bg-zinc-400/20 text-zinc-200 border-zinc-400/30",
      label: "Silver Match",
      icon: "🥈",
    },
    {
      ring: "border-orange-500/30 bg-orange-500/5 hover:border-orange-500/60",
      rankBadge: "bg-orange-500/20 text-orange-300 border-orange-500/30",
      label: "Bronze Match",
      icon: "🥉",
    },
  ];

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            Top-3 Candidates Executive Summary
          </h3>
          <p className="text-xs text-zinc-500">
            Algorithmic shortlisting based on dual-signal keyword & semantic evidence fusion
          </p>
        </div>
        {top3.length >= 2 && onCompareTopTwo && (
          <button
            onClick={onCompareTopTwo}
            className="text-xs px-3 py-1.5 rounded-md border border-blue-500/40 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 transition-colors flex items-center gap-1.5"
          >
            <span>Compare #1 vs #2</span>
            <span>→</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        {top3.map((c, i) => {
          const theme = rankThemes[i];
          const displayName = c.name || c.candidate_name;
          const finalScore = c.final_score ?? c.scores?.final_score ?? 0;
          const reqScore = c.required_coverage ?? c.scores?.required_skill_coverage ?? 0;
          const semScore = c.semantic_score ?? c.scores?.semantic_requirement_alignment ?? 0;
          const keyScore = c.lexical_score ?? c.scores?.contextual_lexical_relevance ?? 0;

          return (
            <button
              key={c.candidate_id}
              onClick={() => onSelectCandidate(c.candidate_id)}
              className={`
                text-left rounded-lg border ${theme.ring} p-4.5
                transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/40
                flex flex-col justify-between
              `}
            >
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{theme.icon}</span>
                    <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded border ${theme.rankBadge}`}>
                      Rank #{c.rank}
                    </span>
                  </div>
                  <ScoreBadge value={finalScore} size="md" />
                </div>

                <h4 className="text-sm font-semibold text-zinc-100 mb-1.5 line-clamp-1">
                  {displayName}
                </h4>

                <p className="text-xs text-zinc-400 leading-relaxed line-clamp-3 mb-3">
                  {c.explanation}
                </p>
              </div>

              <div className="pt-3 border-t border-zinc-800/80 grid grid-cols-3 gap-2 text-center text-zinc-400">
                <div className="bg-zinc-900/60 rounded p-1.5 border border-zinc-800/50">
                  <span className="text-[10px] text-zinc-500 uppercase block">Required</span>
                  <span className="text-xs font-mono font-medium text-zinc-200">
                    {Math.round(reqScore * 100)}%
                  </span>
                </div>
                <div className="bg-zinc-900/60 rounded p-1.5 border border-zinc-800/50">
                  <span className="text-[10px] text-zinc-500 uppercase block">Semantic</span>
                  <span className="text-xs font-mono font-medium text-zinc-200">
                    {Math.round(semScore * 100)}%
                  </span>
                </div>
                <div className="bg-zinc-900/60 rounded p-1.5 border border-zinc-800/50">
                  <span className="text-[10px] text-zinc-500 uppercase block">Keyword</span>
                  <span className="text-xs font-mono font-medium text-zinc-200">
                    {Math.round(keyScore * 100)}%
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
