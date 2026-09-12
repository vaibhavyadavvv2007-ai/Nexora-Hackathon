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
  const [searchQuery, setSearchQuery] = useState("");
  const [filterMode, setFilterMode] = useState<"all" | "no_missing" | "top_tier">("all");

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === "rank" || field === "name");
    }
  };

  const filteredAndSortedCandidates = useMemo(() => {
    let list = [...candidates];

    // Text search query filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.candidate_id.toLowerCase().includes(q) ||
          c.matched_required.some((r) => r.name.toLowerCase().includes(q))
      );
    }

    // Category filter
    if (filterMode === "no_missing") {
      list = list.filter((c) => c.missing_required.length === 0);
    } else if (filterMode === "top_tier") {
      list = list.filter((c) => c.final_score >= 0.70);
    }

    // Sort
    return list.sort((a, b) => {
      let valA: number | string = 0;
      let valB: number | string = 0;

      switch (sortField) {
        case "rank":
          valA = a.rank;
          valB = b.rank;
          break;
        case "name":
          valA = a.name;
          valB = b.name;
          break;
        case "final_score":
          valA = a.final_score;
          valB = b.final_score;
          break;
        case "required_coverage":
          valA = a.required_coverage;
          valB = b.required_coverage;
          break;
        case "lexical_score":
          valA = a.lexical_score;
          valB = b.lexical_score;
          break;
        case "semantic_score":
          valA = a.semantic_score;
          valB = b.semantic_score;
          break;
        case "preferred_coverage":
          valA = a.preferred_coverage;
          valB = b.preferred_coverage;
          break;
      }

      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [candidates, sortField, sortAsc, searchQuery, filterMode]);

  const renderSortIndicator = (field: SortField) => {
    if (sortField !== field) {
      return <span className="opacity-25 ml-1 select-none">↕</span>;
    }
    return <span className="text-blue-400 font-bold ml-1 select-none">{sortAsc ? "▲" : "▼"}</span>;
  };

  return (
    <div className="space-y-3">
      {/* Search & Quick Filters Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5">
        <div className="relative flex-1 max-w-sm">
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search candidate name, ID, or verified skill…"
            className="w-full bg-zinc-900 border border-zinc-700/80 rounded-md pl-8 pr-3 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            aria-label="Filter candidates list"
          />
          <svg className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-zinc-500 font-mono hidden md:inline">Filter:</span>
          <button
            onClick={() => setFilterMode("all")}
            className={`text-xs px-2.5 py-1 rounded transition-colors ${
              filterMode === "all"
                ? "bg-zinc-700 text-white font-medium"
                : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
            }`}
          >
            All ({candidates.length})
          </button>
          <button
            onClick={() => setFilterMode("top_tier")}
            className={`text-xs px-2.5 py-1 rounded transition-colors ${
              filterMode === "top_tier"
                ? "bg-blue-600 text-white font-medium"
                : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
            }`}
          >
            Top Tier (≥70%)
          </button>
          <button
            onClick={() => setFilterMode("no_missing")}
            className={`text-xs px-2.5 py-1 rounded transition-colors ${
              filterMode === "no_missing"
                ? "bg-emerald-700 text-white font-medium"
                : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
            }`}
          >
            Zero Missing Req
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-900/50 shadow-sm">
        <table className="w-full text-left text-sm" role="table" aria-label="Candidate Shortlisting Leaderboard">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/80 text-zinc-400 text-xs">
              <th
                onClick={() => handleSort("rank")}
                className="py-3 px-3 cursor-pointer select-none hover:text-zinc-200 font-medium w-16"
                aria-sort={sortField === "rank" ? (sortAsc ? "ascending" : "descending") : "none"}
              >
                Rank {renderSortIndicator("rank")}
              </th>
              <th
                onClick={() => handleSort("name")}
                className="py-3 px-4 cursor-pointer select-none hover:text-zinc-200 font-medium"
                aria-sort={sortField === "name" ? (sortAsc ? "ascending" : "descending") : "none"}
              >
                Candidate {renderSortIndicator("name")}
              </th>
              <th
                onClick={() => handleSort("final_score")}
                className="py-3 px-3 text-center cursor-pointer select-none hover:text-zinc-200 font-medium"
                aria-sort={sortField === "final_score" ? (sortAsc ? "ascending" : "descending") : "none"}
              >
                Final Score {renderSortIndicator("final_score")}
              </th>
              <th
                onClick={() => handleSort("required_coverage")}
                className="py-3 px-3 text-center cursor-pointer select-none hover:text-zinc-200 font-medium hidden sm:table-cell"
                title="Coverage of mandatory required skills (Weight: 35%)"
                aria-sort={sortField === "required_coverage" ? (sortAsc ? "ascending" : "descending") : "none"}
              >
                Req. Skills {renderSortIndicator("required_coverage")}
              </th>
              <th
                onClick={() => handleSort("lexical_score")}
                className="py-3 px-3 text-center cursor-pointer select-none hover:text-zinc-200 font-medium hidden md:table-cell"
                title="BM25 Lexical Keyword Relevance (Weight: 25%)"
                aria-sort={sortField === "lexical_score" ? (sortAsc ? "ascending" : "descending") : "none"}
              >
                Keyword {renderSortIndicator("lexical_score")}
              </th>
              <th
                onClick={() => handleSort("semantic_score")}
                className="py-3 px-3 text-center cursor-pointer select-none hover:text-zinc-200 font-medium hidden md:table-cell"
                title="Sentence-Transformer Semantic Alignment (Weight: 30%)"
                aria-sort={sortField === "semantic_score" ? (sortAsc ? "ascending" : "descending") : "none"}
              >
                Semantic {renderSortIndicator("semantic_score")}
              </th>
              <th
                onClick={() => handleSort("preferred_coverage")}
                className="py-3 px-3 text-center cursor-pointer select-none hover:text-zinc-200 font-medium hidden lg:table-cell"
                title="Preferred / Bonus Skills Coverage (Weight: 10%)"
                aria-sort={sortField === "preferred_coverage" ? (sortAsc ? "ascending" : "descending") : "none"}
              >
                Pref. Skills {renderSortIndicator("preferred_coverage")}
              </th>
              <th className="py-3 px-3 text-center font-medium w-28">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {filteredAndSortedCandidates.map((c) => {
              const isSelected = c.candidate_id === selectedId;

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
                        {c.name}
                        {c.rank === 1 && (
                          <span className="text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                            Top Match
                          </span>
                        )}
                        {c.parsing_status === "warning" && (
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40" title="Partial parsing note">
                            ⚠ Note
                          </span>
                        )}
                      </div>
                      <div className="text-zinc-500 text-xs mt-0.5 flex items-center gap-2">
                        <span className="font-mono">{c.candidate_id}</span>
                        <span>•</span>
                        <span className="text-emerald-400/90">{c.matched_required.length} verified</span>
                        {c.missing_required.length > 0 ? (
                          <>
                            <span>•</span>
                            <span className="text-red-400/90">{c.missing_required.length} missing</span>
                          </>
                        ) : (
                          <>
                            <span>•</span>
                            <span className="text-emerald-400">0 gaps</span>
                          </>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="py-3.5 px-3 text-center">
                    <ScoreBadge value={c.final_score} size="md" />
                  </td>
                  <td className="py-3.5 px-3 text-center hidden sm:table-cell">
                    <ScoreBadge value={c.required_coverage} size="sm" />
                  </td>
                  <td className="py-3.5 px-3 text-center hidden md:table-cell">
                    <ScoreBadge value={c.lexical_score} size="sm" />
                  </td>
                  <td className="py-3.5 px-3 text-center hidden md:table-cell">
                    <ScoreBadge value={c.semantic_score} size="sm" />
                  </td>
                  <td className="py-3.5 px-3 text-center hidden lg:table-cell">
                    <ScoreBadge value={c.preferred_coverage} size="sm" />
                  </td>
                  <td className="py-3.5 px-3 text-center" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-center gap-1.5">
                      <button
                        onClick={() => onSelectCandidate(c.candidate_id)}
                        className={`
                          text-xs px-2.5 py-1 rounded transition-colors font-medium
                          ${isSelected ? "bg-blue-600 text-white" : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"}
                        `}
                      >
                        {isSelected ? "Viewing" : "Review"}
                      </button>
                      {onCompareWithAnother && (
                        <button
                          title={`Compare ${c.name} with another candidate`}
                          onClick={() => onCompareWithAnother(c.candidate_id)}
                          className="text-xs px-2 py-1 rounded bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 transition-colors font-mono"
                        >
                          VS
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {filteredAndSortedCandidates.length === 0 && (
              <tr>
                <td colSpan={8} className="py-8 text-center text-zinc-500 text-xs italic">
                  No candidates match the filter &ldquo;{searchQuery}&rdquo;.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
