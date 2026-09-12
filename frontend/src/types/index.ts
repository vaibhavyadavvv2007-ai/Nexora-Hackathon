// ============================================================
// Nexora Frontend — Core Domain Type Definitions
// Defines authoritative frontend interfaces matching backend JSON contracts
// ============================================================

export type RequirementType = "required" | "preferred" | "responsibility";

export type MatchType =
  | "exact"
  | "alias"
  | "phrase"
  | "fuzzy"
  | "semantic_exact"
  | "semantic_related"
  | "semantic_inferred"
  | "lexical";

export type SectionType =
  | "experience"
  | "skills"
  | "projects"
  | "education"
  | "certifications"
  | "summary"
  | "header"
  | "other";

/**
 * Structured requirement parsed from the Job Description.
 */
export interface Requirement {
  id: string;
  name: string;
  type: RequirementType;
  canonical_name: string;
  weight: number;
  critical: boolean;
  source_text: string;
}

/**
 * Skill entity with normalized canonical identifier.
 */
export interface Skill {
  name: string;
  canonical: string;
}

/**
 * Granular text evidence extracted from a resume or job description document.
 */
export interface Evidence {
  text: string;
  section: SectionType;
  page: number;
  source_file: string;
  confidence: number;
  match_type: MatchType;
  similarity: number | null;
}

/**
 * Association of a specific JD requirement with extracted candidate evidence.
 */
export interface MatchEvidence {
  requirement: Requirement;
  evidence: Evidence;
  match_type: MatchType;
  confidence: number;
  similarity?: number | null;
}

/**
 * Legacy EvidenceChunk for backward compatibility with existing components.
 */
export interface EvidenceChunk {
  id: string;
  text: string;
  section: SectionType;
  page: number;
  confidence: number;
  source_file?: string;
}

/**
 * Detailed component score breakdown.
 */
export interface ScoreBreakdown {
  required_skill_coverage: number;       // Weight: 0.35
  semantic_requirement_alignment: number;// Weight: 0.35
  contextual_lexical_relevance: number;  // Weight: 0.20
  preferred_skill_coverage: number;      // Weight: 0.10
  final_score: number;
}

/**
 * Full candidate evaluation dossier as returned by the ranking pipeline.
 */
export interface CandidateEvaluation {
  candidate_id: string;
  name: string;
  candidate_name?: string; // compatibility alias
  rank: number;
  final_score: number;
  required_coverage: number;
  semantic_score: number;
  lexical_score: number;
  preferred_coverage: number;
  scores?: ScoreBreakdown;
  matched_required: Requirement[];
  matched_preferred: Requirement[];
  missing_required: Requirement[];
  keyword_matches: MatchEvidence[];
  semantic_matches: MatchEvidence[];
  evidence: Evidence[];
  explanation: string;
  // Partial failure metadata
  parsing_status?: "success" | "warning" | "error";
  parsing_warnings?: string[];
}

/**
 * Pairwise contrastive comparison between two candidate evaluations.
 */
export interface PairwiseComparison {
  candidate_a_id: string;
  candidate_b_id: string;
  winner_id: string;
  score_delta: number;
  required_skill_delta: number;
  semantic_delta: number;
  lexical_delta?: number;
  explanation: string;
  advantages_a: string[];
  advantages_b: string[];
  missing_skills_diff?: {
    only_a_missing: string[];
    only_b_missing: string[];
    both_missing: string[];
  };
  key_evidence_diff?: Evidence[];
}

/**
 * Structured job description input and metadata.
 */
export interface JobDescription {
  id: string;
  title: string;
  source_file?: string;
  raw_text?: string;
  requirements: Requirement[];
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
}

/**
 * Pipeline processing telemetry and status.
 */
export interface ProcessingStatus {
  stage: "idle" | "uploading" | "parsing" | "matching" | "ranking" | "complete" | "error";
  progress: number; // 0-100
  message: string;
  jd_processed: boolean;
  resumes_processed: number;
  resumes_total: number;
  semantic_model_status: "idle" | "loading" | "encoding" | "ready" | "error";
  keyword_engine_status: "idle" | "indexing" | "matching" | "ready" | "error";
  ranking_status: "idle" | "computing" | "complete" | "error";
  failed_resumes: { filename: string; reason: string }[];
}

/**
 * Top-level response from batch candidate evaluation.
 */
export interface EvaluationResult {
  job_description: JobDescription;
  candidates: CandidateEvaluation[];
  processing_time_ms: number;
  model_version: string;
  failed_candidates?: { filename: string; reason: string }[];
}

/**
 * Data source mode configuration.
 */
export type DataSourceMode = "mock" | "api";

// ============================================================
// Raw Backend Payloads & API Response Envelopes
// Used by adapters to translate FastAPI Pydantic responses into UI models
// ============================================================

export interface BackendScoreStructure {
  required_skill_coverage?: number | null;
  semantic_requirement_alignment?: number | null;
  contextual_lexical_relevance?: number | null;
  preferred_skill_coverage?: number | null;
  final_score?: number | null;
}

export interface BackendCandidateEvaluation {
  candidate_id: string;
  candidate_name?: string;
  name?: string;
  scores?: BackendScoreStructure;
  matched_required?: (Requirement | Skill | string)[];
  matched_preferred?: (Requirement | Skill | string)[];
  missing_required?: (Requirement | string)[];
  semantic_matches?: MatchEvidence[];
  keyword_matches?: MatchEvidence[];
  evidence?: (Evidence | EvidenceChunk)[];
  rank?: number | null;
  final_score?: number | null;
  required_coverage?: number | null;
  semantic_score?: number | null;
  lexical_score?: number | null;
  preferred_coverage?: number | null;
  explanation?: string;
  parsing_status?: "success" | "warning" | "error";
  parsing_warnings?: string[];
}

export interface ResumeBatchUploadResponse {
  uploaded: number;
  failed: { filename: string; reason: string }[];
  job_id?: string;
  files?: string[];
}

export interface StartAnalysisResponse {
  task_id: string;
  status?: string;
}

// ============================================================
// Endpoint Contract Definitions (FastAPI Integration)
// ============================================================

export interface FastApiValidationErrorItem {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface FastApiErrorResponse {
  detail: string | FastApiValidationErrorItem[];
}

export interface RequestLifecycleOptions {
  signal?: AbortSignal;
  timeoutMs?: number;
}

// 1. JD Upload Contract
export interface JobUploadParams {
  file: File;
  title?: string;
}
export type JobUploadResponse = JobDescription;

// 2. Resume Batch Upload Contract
export interface ResumeBatchUploadParams {
  files: File[];
  job_id?: string;
}

// 3. Start Analysis Contract
export interface StartAnalysisParams {
  job_id: string;
  candidate_ids?: string[];
  resume_files?: File[];
}

// 4. Analysis Status Contract
export interface AnalysisStatusParams {
  task_id: string;
  mockStage?: ProcessingStatus["stage"];
}
export type AnalysisStatusResponse = ProcessingStatus;

// 5. Ranked Candidates Contract
export interface RankedCandidatesParams {
  job_id?: string;
  sort_by?: "rank" | "final_score" | "required_coverage" | "semantic_score" | "lexical_score";
  min_score?: number;
}
export type RankedCandidatesResponse = EvaluationResult;

// 6. Candidate Detail Contract
export interface CandidateDetailParams {
  candidate_id: string;
  job_id?: string;
}
export type CandidateDetailResponse = CandidateEvaluation;

// 7. Pairwise Comparison Contract
export interface PairwiseComparisonParams {
  candidate_a_id: string;
  candidate_b_id: string;
  job_id?: string;
}
export type PairwiseComparisonResponse = PairwiseComparison;


