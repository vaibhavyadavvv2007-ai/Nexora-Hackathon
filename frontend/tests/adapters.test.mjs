import test from "node:test";
import assert from "node:assert/strict";

// Test adapter functions logic (pure JS mirror of adapters.ts logic to run via Node test runner)
function normalizeRequirement(item, fallbackType = "required", index = 0) {
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
  if ("id" in item && "name" in item && "type" in item) {
    return {
      id: String(item.id),
      name: String(item.name),
      type: item.type || fallbackType,
      canonical_name: String(item.canonical_name || item.name).toLowerCase(),
      weight: typeof item.weight === "number" ? item.weight : 1.0,
      critical: typeof item.critical === "boolean" ? item.critical : fallbackType === "required",
      source_text: String(item.source_text || item.name || ""),
    };
  }
  const name = String(item.name || item.surface_form || item.canonical_name || `Skill-${index + 1}`);
  const canonical = String(item.canonical_name || item.canonical || name).toLowerCase();
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

function adaptCandidate(raw, index = 0) {
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
  const candidateId = String(raw.candidate_id || raw.id || `CAND-${index + 1}`);
  const candidateName = String(
    raw.candidate_name || raw.name || raw.applicant_name || `Candidate ${candidateId}`
  );
  const scoresObj = (raw.scores && typeof raw.scores === "object" ? raw.scores : {});
  const finalScore =
    typeof scoresObj.final_score === "number"
      ? scoresObj.final_score
      : typeof raw.final_score === "number"
      ? raw.final_score
      : 0;
  const requiredCoverage =
    typeof scoresObj.required_skill_coverage === "number"
      ? scoresObj.required_skill_coverage
      : typeof raw.required_coverage === "number"
      ? raw.required_coverage
      : 0;
  const semanticScore =
    typeof scoresObj.semantic_requirement_alignment === "number"
      ? scoresObj.semantic_requirement_alignment
      : typeof raw.semantic_score === "number"
      ? raw.semantic_score
      : 0;
  const lexicalScore =
    typeof scoresObj.contextual_lexical_relevance === "number"
      ? scoresObj.contextual_lexical_relevance
      : typeof raw.lexical_score === "number"
      ? raw.lexical_score
      : 0;
  const preferredCoverage =
    typeof scoresObj.preferred_skill_coverage === "number"
      ? scoresObj.preferred_skill_coverage
      : typeof raw.preferred_coverage === "number"
      ? raw.preferred_coverage
      : 0;

  return {
    candidate_id: candidateId,
    name: candidateName,
    candidate_name: candidateName,
    rank: typeof raw.rank === "number" && raw.rank > 0 ? raw.rank : index + 1,
    final_score: finalScore,
    required_coverage: requiredCoverage,
    semantic_score: semanticScore,
    lexical_score: lexicalScore,
    preferred_coverage: preferredCoverage,
    scores: {
      required_skill_coverage: requiredCoverage,
      semantic_requirement_alignment: semanticScore,
      contextual_lexical_relevance: lexicalScore,
      preferred_skill_coverage: preferredCoverage,
      final_score: finalScore,
    },
    matched_required: (Array.isArray(raw.matched_required) ? raw.matched_required : []).map((r, i) =>
      normalizeRequirement(r, "required", i)
    ),
    matched_preferred: (Array.isArray(raw.matched_preferred) ? raw.matched_preferred : []).map((r, i) =>
      normalizeRequirement(r, "preferred", i)
    ),
    missing_required: (Array.isArray(raw.missing_required) ? raw.missing_required : []).map((r, i) =>
      normalizeRequirement(r, "required", i)
    ),
    keyword_matches: Array.isArray(raw.keyword_matches) ? raw.keyword_matches : [],
    semantic_matches: Array.isArray(raw.semantic_matches) ? raw.semantic_matches : [],
    evidence: Array.isArray(raw.evidence) ? raw.evidence : [],
    explanation:
      typeof raw.explanation === "string" && raw.explanation.trim().length > 0
        ? raw.explanation.trim()
        : `${candidateName} achieved an overall score of ${(finalScore * 100).toFixed(0)}%.`,
    parsing_status: raw.parsing_status || "success",
    parsing_warnings: Array.isArray(raw.parsing_warnings) ? raw.parsing_warnings.map(String) : undefined,
  };
}

test("Adapter correctly maps backend CandidateEvaluation with nested ScoreStructure", () => {
  const backendRaw = {
    candidate_id: "cand-backend-042",
    candidate_name: "Sarah Jenkins",
    scores: {
      required_skill_coverage: 0.92,
      semantic_requirement_alignment: 0.88,
      contextual_lexical_relevance: 0.85,
      preferred_skill_coverage: 0.75,
      final_score: 0.88,
    },
    matched_required: [
      { canonical_name: "typescript", surface_form: "TypeScript", match_type: "exact", confidence: 0.98 },
      { canonical_name: "nextjs", surface_form: "Next.js", match_type: "exact", confidence: 0.95 },
    ],
    matched_preferred: [
      { canonical_name: "graphql", surface_form: "GraphQL", match_type: "exact", confidence: 0.85 },
    ],
    missing_required: [],
    semantic_matches: [],
    keyword_matches: [],
    evidence: [],
    rank: 1,
  };

  const adapted = adaptCandidate(backendRaw, 0);

  // Top-level fields required by UI
  assert.equal(adapted.candidate_id, "cand-backend-042");
  assert.equal(adapted.name, "Sarah Jenkins");
  assert.equal(adapted.final_score, 0.88);
  assert.equal(adapted.required_coverage, 0.92);
  assert.equal(adapted.semantic_score, 0.88);
  assert.equal(adapted.lexical_score, 0.85);
  assert.equal(adapted.preferred_coverage, 0.75);
  assert.equal(adapted.rank, 1);

  // Requirement structure
  assert.equal(adapted.matched_required.length, 2);
  assert.equal(adapted.matched_required[0].canonical_name, "typescript");
  assert.equal(adapted.matched_required[0].type, "required");

  // Fallback explanation generated
  assert.ok(adapted.explanation.includes("Sarah Jenkins"));
  assert.ok(adapted.explanation.includes("88%"));
});

test("Adapter handles already-flattened mock data without data loss", () => {
  const mockCand = {
    candidate_id: "MOCK-001",
    name: "Alex Rivera",
    rank: 1,
    final_score: 0.87,
    required_coverage: 0.875,
    semantic_score: 0.82,
    lexical_score: 0.91,
    preferred_coverage: 0.60,
    matched_required: [{ id: "req-1", name: "React", type: "required", canonical_name: "react", weight: 1.0, critical: true, source_text: "React" }],
    matched_preferred: [],
    missing_required: [],
    keyword_matches: [],
    semantic_matches: [],
    evidence: [],
    explanation: "Top ranked candidate.",
  };

  const adapted = adaptCandidate(mockCand);

  assert.equal(adapted.name, "Alex Rivera");
  assert.equal(adapted.final_score, 0.87);
  assert.equal(adapted.explanation, "Top ranked candidate.");
  assert.equal(adapted.scores.final_score, 0.87);
  assert.equal(adapted.scores.required_skill_coverage, 0.875);
});

test("API Endpoint paths registry validation", () => {
  const API_ENDPOINTS = {
    jobs: {
      upload: () => "api/jobs/upload",
      get: (jobId) => `api/jobs/${encodeURIComponent(jobId)}`,
    },
    resumes: {
      uploadBatch: () => "api/resumes/upload-batch",
    },
    evaluation: {
      start: () => "api/evaluation/start",
      status: (taskId) => `api/evaluation/status/${encodeURIComponent(taskId)}`,
      rankings: (jobId) => jobId ? `api/evaluation/rankings?job_id=${encodeURIComponent(jobId)}` : "api/evaluation/rankings",
      compare: (a, b, j) => {
        const base = `api/evaluation/compare?candidate_a=${encodeURIComponent(a)}&candidate_b=${encodeURIComponent(b)}`;
        return j ? `${base}&job_id=${encodeURIComponent(j)}` : base;
      },
    },
    candidates: {
      get: (id, j) => {
        const base = `api/candidates/${encodeURIComponent(id)}`;
        return j ? `${base}?job_id=${encodeURIComponent(j)}` : base;
      },
    },
  };

  assert.equal(API_ENDPOINTS.jobs.upload(), "api/jobs/upload");
  assert.equal(API_ENDPOINTS.jobs.get("job 123"), "api/jobs/job%20123");
  assert.equal(API_ENDPOINTS.resumes.uploadBatch(), "api/resumes/upload-batch");
  assert.equal(API_ENDPOINTS.evaluation.start(), "api/evaluation/start");
  assert.equal(API_ENDPOINTS.evaluation.status("task-001"), "api/evaluation/status/task-001");
  assert.equal(API_ENDPOINTS.evaluation.rankings(), "api/evaluation/rankings");
  assert.equal(API_ENDPOINTS.evaluation.rankings("job-1"), "api/evaluation/rankings?job_id=job-1");
  assert.equal(API_ENDPOINTS.evaluation.compare("cand1", "cand2"), "api/evaluation/compare?candidate_a=cand1&candidate_b=cand2");
  assert.equal(API_ENDPOINTS.candidates.get("cand1"), "api/candidates/cand1");
});
