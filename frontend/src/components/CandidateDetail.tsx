"use client";

import { CandidateEvaluation } from "@/types";
import ScoreBar, { ScoreBadge } from "./ScoreBar";

interface CandidateDetailProps {
  candidate: CandidateEvaluation;
  onClose: () => void;
  onCompare: (id: string) => void;
  allCandidates: CandidateEvaluation[];
}

export default function CandidateDetail({
  candidate,
  onClose,
  onCompare,
  allCandidates,
}: CandidateDetailProps) {
  const c = candidate;
  const displayName = c.name || c.candidate_name;
  const finalScore = c.final_score ?? c.scores?.final_score ?? 0;
  const reqScore = c.required_coverage ?? c.scores?.required_skill_coverage ?? 0;
  const keyScore = c.lexical_score ?? c.scores?.contextual_lexical_relevance ?? 0;
  const semScore = c.semantic_score ?? c.scores?.semantic_requirement_alignment ?? 0;
  const prefScore = c.preferred_coverage ?? c.scores?.preferred_skill_coverage ?? 0;

  const otherCandidates = allCandidates.filter((oc) => oc.candidate_id !== c.candidate_id);

  return (
    <div className="border border-zinc-800 rounded-lg bg-zinc-900/90 shadow-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800 bg-zinc-900">
        <div className="flex items-center gap-3">
          <span
            className={`
              inline-flex items-center justify-center w-9 h-9 rounded-full text-sm font-bold
              ${c.rank === 1 ? "bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/40" :
                c.rank === 2 ? "bg-zinc-400/20 text-zinc-200 ring-1 ring-zinc-400/40" :
                c.rank === 3 ? "bg-orange-500/20 text-orange-300 ring-1 ring-orange-500/40" :
                "bg-zinc-800 text-zinc-400"}
            `}
          >
            #{c.rank}
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-zinc-100">{displayName}</h3>
              <span className="text-xs font-mono text-zinc-500 bg-zinc-800/80 px-1.5 py-0.5 rounded">
                {c.candidate_id}
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">
              Candidate Dossier · Ranked {c.rank} of {allCandidates.length}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] uppercase tracking-wider text-zinc-500 block">Overall Score</span>
            <ScoreBadge value={finalScore} size="lg" />
          </div>
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-zinc-200 transition-colors p-1.5 rounded-md hover:bg-zinc-800"
            aria-label="Close detail view"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <div className="p-5 space-y-6 max-h-[calc(100vh-220px)] overflow-y-auto">
        {/* Score Breakdown Bars */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              Deterministic Score Transparency
            </h4>
            <span className="text-[11px] text-zinc-500">Weights: 35% Req · 30% Sem · 25% Lex · 10% Pref</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 bg-zinc-950/40 p-3.5 rounded-lg border border-zinc-800/80">
            <ScoreBar value={reqScore} label="Required Skill Coverage (35%)" color="bg-blue-500" />
            <ScoreBar value={semScore} label="Semantic Requirement Alignment (30%)" color="bg-cyan-500" />
            <ScoreBar value={keyScore} label="Contextual Keyword Score (25%)" color="bg-violet-500" />
            <ScoreBar value={prefScore} label="Preferred Skill Coverage (10%)" color="bg-teal-500" />
          </div>
        </section>

        {/* Skill Verification Analysis */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Matched Required Skills */}
          <div className="rounded-lg border border-emerald-900/30 bg-emerald-950/10 p-4">
            <div className="flex items-center justify-between mb-2.5">
              <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Matched Required Skills ({c.matched_required.length})
              </h4>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {c.matched_required.map((s) => (
                <span
                  key={s.canonical}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-medium"
                >
                  <svg className="w-3 h-3 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  {s.name}
                </span>
              ))}
              {c.matched_required.length === 0 && (
                <span className="text-xs text-zinc-500 italic">No required skills verified</span>
              )}
            </div>
          </div>

          {/* Missing Required Skills */}
          <div className="rounded-lg border border-red-900/30 bg-red-950/10 p-4">
            <div className="flex items-center justify-between mb-2.5">
              <h4 className="text-xs font-semibold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
                <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                Missing Required Skills ({c.missing_required.length})
              </h4>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {c.missing_required.map((r) => (
                <span
                  key={r.id}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-red-500/15 text-red-300 border border-red-500/30 font-medium"
                >
                  <svg className="w-3 h-3 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  {r.text}
                </span>
              ))}
              {c.missing_required.length === 0 && (
                <span className="text-xs text-emerald-400 flex items-center gap-1">
                  ✓ 100% required skill coverage — zero gaps
                </span>
              )}
            </div>
          </div>
        </section>

        {/* Matched Preferred Skills */}
        {c.matched_preferred.length > 0 && (
          <section className="rounded-lg border border-teal-900/30 bg-teal-950/10 p-4">
            <h4 className="text-xs font-semibold text-teal-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <svg className="w-4 h-4 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              </svg>
              Matched Preferred Skills ({c.matched_preferred.length})
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {c.matched_preferred.map((s) => (
                <span
                  key={s.canonical}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-teal-500/15 text-teal-300 border border-teal-500/30 font-medium"
                >
                  ★ {s.name}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Evidence Verification — Keyword Evidence */}
        <section>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-violet-400 inline-block"></span>
              Keyword Extraction Evidence ({c.keyword_matches.length})
            </h4>
            <span className="text-[11px] text-zinc-500">Exact & phrase matches cited directly from resume text</span>
          </div>
          <div className="space-y-2">
            {c.keyword_matches.map((m, i) => (
              <div key={i} className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3 hover:border-zinc-700 transition-colors">
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-xs font-semibold text-violet-300">{m.requirement.text}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                      {m.match_type}
                    </span>
                    <span className="text-xs font-mono text-zinc-400">
                      {Math.round(m.confidence * 100)}% conf
                    </span>
                  </div>
                </div>
                <blockquote className="text-xs text-zinc-300 italic border-l-2 border-violet-500/50 pl-2.5 py-0.5 bg-violet-500/5 rounded-r">
                  &ldquo;{m.evidence.text}&rdquo;
                </blockquote>
                <div className="flex items-center gap-3 text-[10px] text-zinc-500 mt-2 font-mono">
                  <span>Section: {m.evidence.section}</span>
                  <span>•</span>
                  <span>Page {m.evidence.page}</span>
                  <span>•</span>
                  <span>Source: {m.evidence.source_file}</span>
                </div>
              </div>
            ))}
            {c.keyword_matches.length === 0 && (
              <p className="text-xs text-zinc-500 italic p-3 bg-zinc-950/40 rounded border border-zinc-800">
                No keyword evidence cited for this candidate.
              </p>
            )}
          </div>
        </section>

        {/* Evidence Verification — Semantic Evidence */}
        <section>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block"></span>
              Semantic Alignment Evidence ({c.semantic_matches.length})
            </h4>
            <span className="text-[11px] text-zinc-500">Sentence transformer contextual alignment</span>
          </div>
          <div className="space-y-2">
            {c.semantic_matches.map((m, i) => (
              <div key={i} className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3 hover:border-zinc-700 transition-colors">
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-xs font-semibold text-cyan-300">{m.requirement.text}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                      {m.match_type}
                    </span>
                    <span className="text-xs font-mono text-cyan-400">
                      sim: {m.similarity !== undefined ? Math.round(m.similarity * 100) : "—"}%
                    </span>
                  </div>
                </div>
                <blockquote className="text-xs text-zinc-300 italic border-l-2 border-cyan-500/50 pl-2.5 py-0.5 bg-cyan-500/5 rounded-r">
                  &ldquo;{m.evidence.text}&rdquo;
                </blockquote>
                <div className="flex items-center gap-3 text-[10px] text-zinc-500 mt-2 font-mono">
                  <span>Section: {m.evidence.section}</span>
                  <span>•</span>
                  <span>Page {m.evidence.page}</span>
                </div>
              </div>
            ))}
            {c.semantic_matches.length === 0 && (
              <p className="text-xs text-zinc-500 italic p-3 bg-zinc-950/40 rounded border border-zinc-800">
                No semantic matches recorded for this candidate.
              </p>
            )}
          </div>
        </section>

        {/* Narrative Explanation */}
        <section>
          <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
            Deterministic Decision Narrative
          </h4>
          <div className="text-sm text-zinc-200 leading-relaxed bg-zinc-950/80 rounded-lg p-4 border border-zinc-800">
            {c.explanation}
          </div>
        </section>

        {/* Pairwise Comparison Links */}
        {otherCandidates.length > 0 && (
          <section className="pt-2 border-t border-zinc-800/80">
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2.5">
              Launch Comparison with Candidate:
            </h4>
            <div className="flex flex-wrap gap-2">
              {otherCandidates.map((oc) => (
                <button
                  key={oc.candidate_id}
                  onClick={() => onCompare(oc.candidate_id)}
                  className="text-xs px-3 py-1.5 rounded-md border border-zinc-700/80 bg-zinc-800/60 text-zinc-300 hover:text-white hover:border-blue-500 hover:bg-blue-500/10 transition-colors flex items-center gap-1.5"
                >
                  <span className="text-zinc-500 font-mono">#{oc.rank}</span>
                  <span>vs {oc.name || oc.candidate_name}</span>
                </button>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
