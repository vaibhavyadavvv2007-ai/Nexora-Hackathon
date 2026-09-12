// ============================================================
// Nexora API — Backend-to-Frontend Data Adapters
// Safely converts raw FastAPI Pydantic responses into strict UI domain models.
// Ensures UI components remain completely decoupled from backend schema variations.
// ============================================================

import {
  CandidateEvaluation,
  EvaluationResult,
  Evidence,
  JobDescription,
  MatchEvidence,
  PairwiseComparison,
  ProcessingStatus,
  Requirement,
  ResumeBatchUploadResponse,
  ScoreBreakdown,
  StartAnalysisResponse,
} from "@/types";

/**
 * Normalizes an arbitrary requirement or skill representation into a structured Requirement.
 */
export function normalizeRequirement(
  item: unknown,
  fallbackType: Requirement["type"] = "required",
  index: number = 0
): Requirement {
  if (!item || typeof item !== "object") {
    const text = String(item || `Requirement-${index + 1}`);
    return {
      id: `req-${index + 1}`,
      name: text,
      type: fallbackType,
      canonical_name: text.toLowerCase().replace(/\s+/g, "_"),
      weight: 1.0,
      critical: fallbackType === "required",
      source_text: text,
    };
  }

  const obj = item as Record<string, unknown>;

  // Check if it's already a Requirement
  if ("id" in obj && "name" in obj && "type" in obj) {
    return {
      id: String(obj.id),
      name: String(obj.name),
      type: (obj.type as Requirement["type"]) || fallbackType,
      canonical_name: String(obj.canonical_name || obj.name).toLowerCase(),
      weight: typeof obj.weight === "number" ? obj.weight : 1.0,
      critical: typeof obj.critical === "boolean" ? obj.critical : fallbackType === "required",
      source_text: String(obj.source_text || obj.name || ""),
    };
  }

  // Check if it's a backend Skill (canonical_name / surface_form or name / canonical)
  const name = String(obj.name || obj.surface_form || obj.canonical_name || `Skill-${index + 1}`);
  const canonical = String(obj.canonical_name || obj.canonical || name).toLowerCase();

  return {
    id: `req-${canonical}-${index + 1}`,
    name,
    type: fallbackType,
    canonical_name: canonical,
    weight: 1.0,
    critical: fallbackType === "required",
    source_text: name,
  };
}

/**
 * Normalizes an Evidence or EvidenceChunk into a UI Evidence model.
 */
export function normalizeEvidence(item: unknown, index: number = 0): Evidence {
  if (!item || typeof item !== "object") {
    return {
      text: String(item || ""),
      section: "experience",
      page: 1,
      source_file: "resume.pdf",
      confidence: 1.0,
      match_type: "exact",
      similarity: null,
    };
  }

  const obj = item as Record<string, unknown>;

  return {
    text: String(obj.text || ""),
    section: (obj.section as Evidence["section"]) || "experience",
    page: typeof obj.page === "number" ? obj.page : 1,
    source_file: String(obj.source_file || `candidate_evidence_${index + 1}.pdf`),
    confidence: typeof obj.confidence === "number" ? obj.confidence : 1.0,
    match_type: (obj.match_type as Evidence["match_type"]) || "exact",
    similarity: typeof obj.similarity === "number" ? obj.similarity : null,
  };
}

/**
 * Normalizes a MatchEvidence pair.
 */
export function normalizeMatchEvidence(item: unknown, index: number = 0): MatchEvidence {
  if (!item || typeof item !== "object") {
    const text = String(item || `Match-${index + 1}`);
    return {
      requirement: normalizeRequirement(text, "required", index),
      evidence: normalizeEvidence(text, index),
      match_type: "exact",
      confidence: 1.0,
      similarity: null,
    };
  }

  const obj = item as Record<string, unknown>;
  return {
    requirement: normalizeRequirement(obj.requirement, "required", index),
    evidence: normalizeEvidence(obj.evidence, index),
    match_type: (obj.match_type as MatchEvidence["match_type"]) || "exact",
    confidence: typeof obj.confidence === "number" ? obj.confidence : 1.0,
    similarity: typeof obj.similarity === "number" ? obj.similarity : null,
  };
}

/**
 * Adapts raw candidate data (from backend Pydantic models or mock JSON)
 * into a strictly typed CandidateEvaluation for frontend components.
 */
export function adaptCandidate(raw: unknown, index: number = 0): CandidateEvaluation {
  if (!raw || typeof raw !== "object") {
    return {
      candidate_id: `CAND-${index + 1}`,
      name: `Candidate ${index + 1}`,
      rank: index + 1,
      final_score: 0.5,
      required_coverage: 0.5,
      semantic_score: 0.5,
      lexical_score: 0.5,
      preferred_coverage: 0.5,
      matched_required: [],
      matched_preferred: [],
      missing_required: [],
      keyword_matches: [],
      semantic_matches: [],
      evidence: [],
      explanation: "No evaluation data provided.",
    };
  }

  const obj = raw as Record<string, unknown>;
  const candidateId = String(obj.candidate_id || obj.id || `CAND-${index + 1}`);
  const candidateName = String(
    obj.candidate_name || obj.name || obj.applicant_name || `Candidate ${candidateId}`
  );

  // Handle nested backend scores vs flattened frontend scores
  const scoresObj = (obj.scores && typeof obj.scores === "object" ? obj.scores : {}) as Record<
    string,
    unknown
  >;

  const finalScore =
    typeof scoresObj.final_score === "number"
      ? scoresObj.final_score
      : typeof obj.final_score === "number"
      ? obj.final_score
      : 0;

  const requiredCoverage =
    typeof scoresObj.required_skill_coverage === "number"
      ? scoresObj.required_skill_coverage
      : typeof obj.required_coverage === "number"
      ? obj.required_coverage
      : 0;

  const semanticScore =
    typeof scoresObj.semantic_requirement_alignment === "number"
      ? scoresObj.semantic_requirement_alignment
      : typeof obj.semantic_score === "number"
      ? obj.semantic_score
      : 0;

  const lexicalScore =
    typeof scoresObj.contextual_lexical_relevance === "number"
      ? scoresObj.contextual_lexical_relevance
      : typeof obj.lexical_score === "number"
      ? obj.lexical_score
      : 0;

  const preferredCoverage =
    typeof scoresObj.preferred_skill_coverage === "number"
      ? scoresObj.preferred_skill_coverage
      : typeof obj.preferred_coverage === "number"
      ? obj.preferred_coverage
      : 0;

  const scoreBreakdown: ScoreBreakdown = {
    required_skill_coverage: requiredCoverage,
    semantic_requirement_alignment: semanticScore,
    contextual_lexical_relevance: lexicalScore,
    preferred_skill_coverage: preferredCoverage,
    final_score: finalScore,
  };

  // Normalize requirement and evidence collections
  const rawMatchedReq = Array.isArray(obj.matched_required) ? obj.matched_required : [];
  const matchedRequired = rawMatchedReq.map((r, i) => normalizeRequirement(r, "required", i));

  const rawMatchedPref = Array.isArray(obj.matched_preferred) ? obj.matched_preferred : [];
  const matchedPreferred = rawMatchedPref.map((r, i) => normalizeRequirement(r, "preferred", i));

  const rawMissingReq = Array.isArray(obj.missing_required) ? obj.missing_required : [];
  const missingRequired = rawMissingReq.map((r, i) => normalizeRequirement(r, "required", i));

  const rawKeyMatches = Array.isArray(obj.keyword_matches) ? obj.keyword_matches : [];
  const keywordMatches = rawKeyMatches.map((m, i) => normalizeMatchEvidence(m, i));

  const rawSemMatches = Array.isArray(obj.semantic_matches) ? obj.semantic_matches : [];
  const semanticMatches = rawSemMatches.map((m, i) => normalizeMatchEvidence(m, i));

  const rawEvidence = Array.isArray(obj.evidence) ? obj.evidence : [];
  const evidence = rawEvidence.map((e, i) => normalizeEvidence(e, i));

  const rank = typeof obj.rank === "number" && obj.rank > 0 ? obj.rank : index + 1;

  // Synthesize concise fallback explanation if backend omitted one
  const explanation =
    typeof obj.explanation === "string" && obj.explanation.trim().length > 0
      ? obj.explanation.trim()
      : `${candidateName} achieved an overall score of ${(finalScore * 100).toFixed(
          0
        )}% with ${(requiredCoverage * 100).toFixed(
          0
        )}% required skill coverage and high semantic alignment.`;

  return {
    candidate_id: candidateId,
    name: candidateName,
    candidate_name: candidateName,
    rank,
    final_score: finalScore,
    required_coverage: requiredCoverage,
    semantic_score: semanticScore,
    lexical_score: lexicalScore,
    preferred_coverage: preferredCoverage,
    scores: scoreBreakdown,
    matched_required: matchedRequired,
    matched_preferred: matchedPreferred,
    missing_required: missingRequired,
    keyword_matches: keywordMatches,
    semantic_matches: semanticMatches,
    evidence,
    explanation,
    parsing_status: (obj.parsing_status as CandidateEvaluation["parsing_status"]) || "success",
    parsing_warnings: Array.isArray(obj.parsing_warnings)
      ? obj.parsing_warnings.map(String)
      : undefined,
  };
}

/**
 * Adapts an array of candidates, ensuring rank ordering.
 */
export function adaptCandidateList(raw: unknown): CandidateEvaluation[] {
  if (!Array.isArray(raw)) return [];
  const list = raw.map((item, idx) => adaptCandidate(item, idx));
  return list.sort((a, b) => a.rank - b.rank);
}

/**
 * Adapts raw Job Description payload.
 */
export function adaptJobDescription(raw: unknown): JobDescription {
  if (!raw || typeof raw !== "object") {
    return {
      id: "jd-default",
      title: "Job Description",
      requirements: [],
      required_skills: [],
      preferred_skills: [],
      responsibilities: [],
    };
  }

  const obj = raw as Record<string, unknown>;
  const rawReqs = Array.isArray(obj.requirements) ? obj.requirements : [];

  return {
    id: String(obj.id || "jd-001"),
    title: String(obj.title || "Job Position"),
    source_file: obj.source_file ? String(obj.source_file) : undefined,
    raw_text: obj.raw_text ? String(obj.raw_text) : undefined,
    requirements: rawReqs.map((r, i) => normalizeRequirement(r, "required", i)),
    required_skills: Array.isArray(obj.required_skills)
      ? obj.required_skills.map(String)
      : [],
    preferred_skills: Array.isArray(obj.preferred_skills)
      ? obj.preferred_skills.map(String)
      : [],
    responsibilities: Array.isArray(obj.responsibilities)
      ? obj.responsibilities.map(String)
      : [],
  };
}

/**
 * Adapts pipeline processing status.
 */
export function adaptProcessingStatus(raw: unknown): ProcessingStatus {
  if (!raw || typeof raw !== "object") {
    return {
      stage: "idle",
      progress: 0,
      message: "Ready",
      jd_processed: false,
      resumes_processed: 0,
      resumes_total: 0,
      semantic_model_status: "idle",
      keyword_engine_status: "idle",
      ranking_status: "idle",
      failed_resumes: [],
    };
  }

  const obj = raw as Record<string, unknown>;

  return {
    stage: (obj.stage as ProcessingStatus["stage"]) || "idle",
    progress: typeof obj.progress === "number" ? obj.progress : 0,
    message: String(obj.message || ""),
    jd_processed: Boolean(obj.jd_processed),
    resumes_processed: typeof obj.resumes_processed === "number" ? obj.resumes_processed : 0,
    resumes_total: typeof obj.resumes_total === "number" ? obj.resumes_total : 0,
    semantic_model_status:
      (obj.semantic_model_status as ProcessingStatus["semantic_model_status"]) || "idle",
    keyword_engine_status:
      (obj.keyword_engine_status as ProcessingStatus["keyword_engine_status"]) || "idle",
    ranking_status: (obj.ranking_status as ProcessingStatus["ranking_status"]) || "idle",
    failed_resumes: Array.isArray(obj.failed_resumes)
      ? obj.failed_resumes.map((f: unknown) => {
          const fo = (f || {}) as Record<string, unknown>;
          return {
            filename: String(fo.filename || "unknown_file"),
            reason: String(fo.reason || "Parsing failed"),
          };
        })
      : [],
  };
}

/**
 * Adapts full evaluation results response.
 */
export function adaptEvaluationResult(raw: unknown): EvaluationResult {
  if (!raw || typeof raw !== "object") {
    return {
      job_description: adaptJobDescription(null),
      candidates: [],
      processing_time_ms: 0,
      model_version: "nexora-engine-v1.0",
    };
  }

  const obj = raw as Record<string, unknown>;
  const candidates = Array.isArray(obj.candidates)
    ? adaptCandidateList(obj.candidates)
    : [];

  return {
    job_description: adaptJobDescription(obj.job_description),
    candidates,
    processing_time_ms:
      typeof obj.processing_time_ms === "number" ? obj.processing_time_ms : 0,
    model_version: String(obj.model_version || "nexora-engine-v1.0"),
    failed_candidates: Array.isArray(obj.failed_candidates)
      ? obj.failed_candidates.map((fc: unknown) => {
          const fco = (fc || {}) as Record<string, unknown>;
          return {
            filename: String(fco.filename || "unknown"),
            reason: String(fco.reason || "Evaluation failed"),
          };
        })
      : undefined,
  };
}

/**
 * Adapts pairwise comparison response.
 */
export function adaptPairwiseComparison(raw: unknown): PairwiseComparison | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }

  const obj = raw as Record<string, unknown>;
  if (!obj.candidate_a_id || !obj.candidate_b_id) {
    return null;
  }

  return {
    candidate_a_id: String(obj.candidate_a_id),
    candidate_b_id: String(obj.candidate_b_id),
    winner_id: String(obj.winner_id || obj.candidate_a_id),
    score_delta: typeof obj.score_delta === "number" ? obj.score_delta : 0,
    required_skill_delta:
      typeof obj.required_skill_delta === "number" ? obj.required_skill_delta : 0,
    semantic_delta: typeof obj.semantic_delta === "number" ? obj.semantic_delta : 0,
    lexical_delta: typeof obj.lexical_delta === "number" ? obj.lexical_delta : undefined,
    explanation: String(obj.explanation || "Pairwise comparison analysis completed."),
    advantages_a: Array.isArray(obj.advantages_a) ? obj.advantages_a.map(String) : [],
    advantages_b: Array.isArray(obj.advantages_b) ? obj.advantages_b.map(String) : [],
    missing_skills_diff:
      obj.missing_skills_diff && typeof obj.missing_skills_diff === "object"
        ? {
            only_a_missing: Array.isArray(
              (obj.missing_skills_diff as Record<string, unknown>).only_a_missing
            )
              ? (
                  (obj.missing_skills_diff as Record<string, unknown>).only_a_missing as unknown[]
                ).map(String)
              : [],
            only_b_missing: Array.isArray(
              (obj.missing_skills_diff as Record<string, unknown>).only_b_missing
            )
              ? (
                  (obj.missing_skills_diff as Record<string, unknown>).only_b_missing as unknown[]
                ).map(String)
              : [],
            both_missing: Array.isArray(
              (obj.missing_skills_diff as Record<string, unknown>).both_missing
            )
              ? (
                  (obj.missing_skills_diff as Record<string, unknown>).both_missing as unknown[]
                ).map(String)
              : [],
          }
        : undefined,
    key_evidence_diff: Array.isArray(obj.key_evidence_diff)
      ? obj.key_evidence_diff.map((e, idx) => normalizeEvidence(e, idx))
      : undefined,
  };
}

/**
 * Adapts batch upload response.
 */
export function adaptResumeUploadBatchResponse(raw: unknown): ResumeBatchUploadResponse {
  if (!raw || typeof raw !== "object") {
    return { uploaded: 0, failed: [] };
  }

  const obj = raw as Record<string, unknown>;
  return {
    uploaded: typeof obj.uploaded === "number" ? obj.uploaded : 0,
    failed: Array.isArray(obj.failed)
      ? obj.failed.map((f: unknown) => {
          const fo = (f || {}) as Record<string, unknown>;
          return {
            filename: String(fo.filename || "unknown"),
            reason: String(fo.reason || "Upload error"),
          };
        })
      : [],
    job_id: obj.job_id ? String(obj.job_id) : undefined,
    files: Array.isArray(obj.files) ? obj.files.map(String) : undefined,
  };
}

/**
 * Adapts pipeline start analysis response.
 */
export function adaptStartAnalysisResponse(raw: unknown): StartAnalysisResponse {
  if (!raw || typeof raw !== "object") {
    return { task_id: `task-${Date.now()}` };
  }

  const obj = raw as Record<string, unknown>;
  return {
    task_id: String(obj.task_id || `task-${Date.now()}`),
    status: obj.status ? String(obj.status) : undefined,
  };
}
