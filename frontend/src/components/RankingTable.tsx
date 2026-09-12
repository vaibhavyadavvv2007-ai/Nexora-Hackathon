"use client";

import { useState, useMemo } from "react";
import { CandidateEvaluation } from "@/types";
import { ScoreBadge } from "./ScoreBar";

interface RankingTableProps {
  candidates: CandidateEvaluation[];
  onSelectCandidate: (id: string) => void;
  selectedId: string | null;
  onCompareWithAnother?: (candidateId: string) => void;
}

type SortField =
  | "rank"
  | "name"
  | "final_score"
  | "required_coverage"
  | "lexical_score"
  | "semantic_score"
  | "preferred_coverage";

export default function RankingTable({
  candidates,
  onSelectCandidate,
  selectedId,
  onCompareWithAnother,
}: RankingTableProps) {
  const [sortField, setSortField] = useState<SortField>("rank");
  const [sortAsc, setSortAsc] = useState(true);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      // For score columns, default descending, for rank/name default ascending
      setSortAsc(field === "rank" || field === "name");
    }
  };

  const sortedCandidates = useMemo(() => {
    const list = [...candidates];
    return list.sort((a, b) => {
      let valA: number | string = 0;
      let valB: number | string = 0;

      switch (sortField) {
        case "rank":
          valA = a.rank;
          valB = b.rank;
          break;
        case "name":
          valA = a.name || a.candidate_name || "";
          valB = b.name || b.candidate_name || "";
          break;
        case "final_score":
          valA = a.final_score ?? a.scores?.final_score ?? 0;
          valB = b.final_score ?? b.scores?.final_score ?? 0;
          break;
        case "required_coverage":
          valA = a.required_coverage ?? a.scores?.required_skill_coverage ?? 0;
          valB = b.required_coverage ?? b.scores?.required_skill_coverage ?? 0;
          break;
        case "lexical_score":
          valA = a.lexical_score ?? a.scores?.contextual_lexical_relevance ?? 0;
          valB = b.lexical_score ?? b.scores?.contextual_lexical_relevance ?? 0;
          break;
        case "semantic_score":
          valA = a.semantic_score ?? a.scores?.semantic_requirement_alignment ?? 0;
          valB = b.semantic_score ?? b.scores?.semantic_requirement_alignment ?? 0;
          break;
        case "preferred_coverage":
          valA = a.preferred_coverage ?? a.scores?.preferred_skill_coverage ?? 0;
          valB = b.preferred_coverage ?? b.scores?.preferred_skill_coverage ?? 0;
          break;
      }

      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [candidates, sortField, sortAsc]);

  const renderSortIndicator = (field: SortField) => {
    if (sortField !== field) {
      return <span className="opacity-20 ml-1">↕</span>;
    }
    return <span className="text-blue-400 ml-1">{sortAsc ? "▲" : "▼"}</span>;
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-900/40">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-800 bg-zinc-900/80 text-zinc-400 text-xs">
            <th
              onClick={() => handleSort("rank")}
              className="py-3 px-3 cursor-pointer select-none hover:text-zinc-200 font-medium w-16"
            >
              Rank {renderSortIndicator("rank")}
            </th>
            <th
              onClick={() => handleSort("name")}
              className="py-3 px-4 cursor-pointer select-none hover:text-zinc-200 font-medium"
            >
              Candidate {renderSortIndicator("name")}
            </th>
            <th
              onClick={() => handleSort("final_score")}
              className="py-3 px-3 text-center cursor-pointer select-none hover:text-zinc-200 font-medium"
            >
              Final Score {renderSortIndicator("final_score")}
            </th>
            <th
              onClick={() => handleSort("required_coverage")}
              className="py-3 px-3 text-center cursor-pointer select-none hover:text-zinc-200 font-medium hidden sm:table-cell"
            >
              Req. Skills {renderSortIndicator("required_coverage")}
            </th>
            <th
              onClick={() => handleSort("lexical_score")}
              className="py-3 px-3 text-center cursor-pointer select-none hover:text-zinc-200 font-medium hidden md:table-cell"
            >
              Keyword {renderSortIndicator("lexical_score")}
            </th>
            <th
              onClick={() => handleSort("semantic_score")}
              className="py-3 px-3 text-center cursor-pointer select-none hover:text-zinc-200 font-medium hidden md:table-cell"
            >
              Semantic {renderSortIndicator("semantic_score")}
            </th>
            <th
              onClick={() => handleSort("preferred_coverage")}
              className="py-3 px-3 text-center cursor-pointer select-none hover:text-zinc-200 font-medium hidden lg:table-cell"
            >
              Pref. Skills {renderSortIndicator("preferred_coverage")}
            </th>
            <th className="py-3 px-3 text-center font-medium w-28">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800/60">
          {sortedCandidates.map((c) => {
            const isSelected = c.candidate_id === selectedId;
            const displayName = c.name || c.candidate_name;
            const finalScore = c.final_score ?? c.scores?.final_score ?? 0;
            const reqScore = c.required_coverage ?? c.scores?.required_skill_coverage ?? 0;
            const keyScore = c.lexical_score ?? c.scores?.contextual_lexical_relevance ?? 0;
            const semScore = c.semantic_score ?? c.scores?.semantic_requirement_alignment ?? 0;
            const prefScore = c.preferred_coverage ?? c.scores?.preferred_skill_coverage ?? 0;

            return (
              <tr
                key={c.candidate_id}
                onClick={() => onSelectCandidate(c.candidate_id)}
                className={`
                  cursor-pointer transition-colors duration-150
                  ${isSelected ? "bg-blue-500/10 border-l-4 border-l-blue-500" : "hover:bg-zinc-800/40"}
                `}
              >
                <td className="py-3.5 px-3">
                  <span
                    className={`
                      inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold
                      ${c.rank === 1 ? "bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/40" :
                        c.rank === 2 ? "bg-zinc-400/20 text-zinc-200 ring-1 ring-zinc-400/40" :
                        c.rank === 3 ? "bg-orange-500/20 text-orange-300 ring-1 ring-orange-500/40" :
                        "bg-zinc-800 text-zinc-400"}
                    `}
                  >
                    #{c.rank}
                  </span>
                </td>
                <td className="py-3.5 px-4">
                  <div>
                    <div className="text-zinc-100 font-medium flex items-center gap-2">
                      {displayName}
                      {c.rank === 1 && (
                        <span className="text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                          Top Match
                        </span>
                      )}
                    </div>
                    <div className="text-zinc-500 text-xs mt-0.5 flex items-center gap-2">
                      <span>{c.candidate_id}</span>
                      <span>•</span>
                      <span>{c.matched_required.length} required matched</span>
                      {c.missing_required.length > 0 && (
                        <>
                          <span>•</span>
                          <span className="text-red-400/80">{c.missing_required.length} missing</span>
                        </>
                      )}
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 text-center">
                  <ScoreBadge value={finalScore} size="md" />
                </td>
                <td className="py-3.5 px-3 text-center hidden sm:table-cell">
                  <ScoreBadge value={reqScore} size="sm" />
                </td>
                <td className="py-3.5 px-3 text-center hidden md:table-cell">
                  <ScoreBadge value={keyScore} size="sm" />
                </td>
                <td className="py-3.5 px-3 text-center hidden md:table-cell">
                  <ScoreBadge value={semScore} size="sm" />
                </td>
                <td className="py-3.5 px-3 text-center hidden lg:table-cell">
                  <ScoreBadge value={prefScore} size="sm" />
                </td>
                <td className="py-3.5 px-3 text-center" onClick={(e) => e.stopPropagation()}>
                  <div className="flex items-center justify-center gap-1.5">
                    <button
                      onClick={() => onSelectCandidate(c.candidate_id)}
                      className={`
                        text-xs px-2.5 py-1 rounded transition-colors
                        ${isSelected ? "bg-blue-600 text-white font-medium" : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"}
                      `}
                    >
                      {isSelected ? "Viewing" : "Review"}
                    </button>
                    {onCompareWithAnother && (
                      <button
                        title="Compare with another candidate"
                        onClick={() => onCompareWithAnother(c.candidate_id)}
                        className="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 transition-colors"
                      >
                        VS
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
