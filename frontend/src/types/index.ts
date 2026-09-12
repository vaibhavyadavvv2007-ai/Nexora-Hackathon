// ============================================================
// Nexora Frontend — Type Definitions
// Defines frontend interfaces matching future backend JSON contracts
// ============================================================

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

export type RequirementType = "required" | "preferred" | "responsibility";

export interface EvidenceChunk {
  id: string;
  text: string;
  section: SectionType;
  page: number;
  confidence: number;
  source_file?: string;
}

export interface Requirement {
  id: string;
  text: string;
  type: RequirementType;
}

export interface Skill {
  name: string;
  canonical: string;
}

export interface MatchEvidence {
  requirement: Requirement;
  evidence: EvidenceChunk;
  match_type: MatchType;
  confidence: number;
  similarity?: number;
}

export interface ScoreBreakdown {
  required_skill_coverage: number;
  semantic_requirement_alignment: number;
  contextual_lexical_relevance: number;
  preferred_skill_coverage: number;
  final_score: number;
}

/**
 * CandidateEvaluation contract
 * Matches backend evaluation output concepts
 */
export interface CandidateEvaluation {
  candidate_id: string;
  name: string;
  candidate_name?: string; // alias
  rank: number;
  final_score: number;
  required_coverage: number;
  semantic_score: number;
  lexical_score: number;
  preferred_coverage: number;
  scores?: ScoreBreakdown; // nested representation from backend
  matched_required: Skill[];
  matched_preferred: Skill[];
  missing_required: Requirement[];
  keyword_matches: MatchEvidence[];
  semantic_matches: MatchEvidence[];
  explanation: string;
}

export interface PairwiseComparison {
  candidate_a_id: string;
  candidate_b_id: string;
  winner_id: string;
  score_delta: number;
  required_skill_delta: number;
  semantic_delta: number;
  explanation: string;
  advantages_a: string[];
  advantages_b: string[];
}

export interface JobDescriptionInput {
  id: string;
  title: string;
  raw_text?: string;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
}

export interface ProcessingStatus {
  stage: "idle" | "uploading" | "parsing" | "matching" | "ranking" | "complete" | "error";
  progress: number; // 0-100
  message: string;
  candidates_processed: number;
  candidates_total: number;
}

export interface EvaluationResult {
  job_description: JobDescriptionInput;
  candidates: CandidateEvaluation[];
  processing_time_ms: number;
  model_version: string;
}
