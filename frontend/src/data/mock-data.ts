// ============================================================
// Mock Data — Clearly labeled synthetic candidates
// These are NOT real people. Used for UI development and demo only.
// ============================================================

import {
  CandidateEvaluation,
  EvaluationResult,
  JobDescriptionInput,
  PairwiseComparison,
  ProcessingStatus,
} from "@/types";

export const MOCK_JOB_DESCRIPTION: JobDescriptionInput = {
  id: "jd-mock-001",
  title: "Senior Full-Stack Engineer (AI / Search Focus)",
  raw_text: "Seeking an experienced Senior Full-Stack Engineer to architect and build high-performance search and retrieval applications. Strong skills in React, TypeScript, Node.js, and PostgreSQL required. Familiarity with Docker, CI/CD pipelines, GraphQL, and cloud services (AWS) highly preferred.",
  required_skills: [
    "React",
    "TypeScript",
    "Node.js",
    "PostgreSQL",
    "REST APIs",
    "Git",
    "CI/CD",
    "Docker",
  ],
  preferred_skills: [
    "GraphQL",
    "Kubernetes",
    "AWS",
    "Redis",
    "Terraform",
  ],
  responsibilities: [
    "Design and build scalable web applications with responsive UIs",
    "Lead code reviews, enforce engineering standards, and mentor junior engineers",
    "Collaborate cross-functionally with product, design, and machine learning teams",
    "Maintain CI/CD pipelines, telemetry, and automated deployment infrastructure",
  ],
};

export const MOCK_CANDIDATES: CandidateEvaluation[] = [
  {
    candidate_id: "MOCK-CAND-001",
    name: "Mock Candidate Alpha (Full-Stack Lead)",
    candidate_name: "Mock Candidate Alpha (Full-Stack Lead)",
    rank: 1,
    final_score: 0.87,
    required_coverage: 0.875, // 7 of 8
    semantic_score: 0.82,
    lexical_score: 0.91,
    preferred_coverage: 0.6, // 3 of 5
    scores: {
      final_score: 0.87,
      required_skill_coverage: 0.875,
      semantic_requirement_alignment: 0.82,
      contextual_lexical_relevance: 0.91,
      preferred_skill_coverage: 0.6,
    },
    matched_required: [
      { name: "React", canonical: "react" },
      { name: "TypeScript", canonical: "typescript" },
      { name: "Node.js", canonical: "nodejs" },
      { name: "PostgreSQL", canonical: "postgresql" },
      { name: "REST APIs", canonical: "rest-apis" },
      { name: "Git", canonical: "git" },
      { name: "Docker", canonical: "docker" },
    ],
    matched_preferred: [
      { name: "AWS", canonical: "aws" },
      { name: "GraphQL", canonical: "graphql" },
      { name: "Redis", canonical: "redis" },
    ],
    missing_required: [
      { id: "req-cicd", text: "CI/CD pipeline configuration", type: "required" },
    ],
    keyword_matches: [
      {
        requirement: { id: "req-react", text: "React experience", type: "required" },
        evidence: {
          id: "ev-001",
          text: "Architected production React applications serving 50k+ DAU with TypeScript and clean state management.",
          section: "experience",
          page: 1,
          confidence: 0.96,
          source_file: "mock_resume_alpha.pdf",
        },
        match_type: "exact",
        confidence: 0.96,
      },
      {
        requirement: { id: "req-node", text: "Node.js backend development", type: "required" },
        evidence: {
          id: "ev-002",
          text: "Developed low-latency RESTful microservices using Node.js and Express connected to PostgreSQL clusters.",
          section: "experience",
          page: 1,
          confidence: 0.94,
          source_file: "mock_resume_alpha.pdf",
        },
        match_type: "exact",
        confidence: 0.94,
      },
      {
        requirement: { id: "req-docker", text: "Docker containerization", type: "required" },
        evidence: {
          id: "ev-003",
          text: "Containerized 6 distributed services using multi-stage Docker builds and docker-compose for dev/staging environments.",
          section: "experience",
          page: 2,
          confidence: 0.90,
          source_file: "mock_resume_alpha.pdf",
        },
        match_type: "exact",
        confidence: 0.90,
      },
      {
        requirement: { id: "req-pg", text: "PostgreSQL relational databases", type: "required" },
        evidence: {
          id: "ev-004",
          text: "Designed normalized schemas, optimized slow B-tree indexing, and managed partitioned PostgreSQL tables.",
          section: "experience",
          page: 2,
          confidence: 0.92,
          source_file: "mock_resume_alpha.pdf",
        },
        match_type: "exact",
        confidence: 0.92,
      },
    ],
    semantic_matches: [
      {
        requirement: {
          id: "req-scalable",
          text: "Design and build scalable web applications",
          type: "responsibility",
        },
        evidence: {
          id: "ev-005",
          text: "Architected a horizontally scalable event-driven data ingestion pipeline processing 10M+ events/day with 99.95% uptime.",
          section: "experience",
          page: 1,
          confidence: 0.91,
          source_file: "mock_resume_alpha.pdf",
        },
        match_type: "semantic_exact",
        confidence: 0.91,
        similarity: 0.89,
      },
      {
        requirement: {
          id: "req-mentor",
          text: "Lead code reviews and mentor junior engineers",
          type: "responsibility",
        },
        evidence: {
          id: "ev-006",
          text: "Supervised and mentored 4 junior and mid-level software engineers through structured pair programming and code quality guidelines.",
          section: "experience",
          page: 2,
          confidence: 0.88,
          source_file: "mock_resume_alpha.pdf",
        },
        match_type: "semantic_exact",
        confidence: 0.88,
        similarity: 0.87,
      },
    ],
    explanation:
      "Rank #1: Candidate Alpha achieves top position with 87.5% required skill coverage (7 of 8), pairing React/TypeScript frontend mastery with Node.js and PostgreSQL database expertise. Keyword match is highest across all applicants (0.91), and semantic alignment confirms demonstrated ownership of scalable architecture and team mentorship. Missing CI/CD configuration is the primary gap.",
  },
  {
    candidate_id: "MOCK-CAND-002",
    name: "Mock Candidate Beta (Product Engineer)",
    candidate_name: "Mock Candidate Beta (Product Engineer)",
    rank: 2,
    final_score: 0.76,
    required_coverage: 0.75, // 6 of 8
    semantic_score: 0.73,
    lexical_score: 0.80,
    preferred_coverage: 0.4, // 2 of 5
    scores: {
      final_score: 0.76,
      required_skill_coverage: 0.75,
      semantic_requirement_alignment: 0.73,
      contextual_lexical_relevance: 0.80,
      preferred_skill_coverage: 0.4,
    },
    matched_required: [
      { name: "React", canonical: "react" },
      { name: "TypeScript", canonical: "typescript" },
      { name: "Node.js", canonical: "nodejs" },
      { name: "REST APIs", canonical: "rest-apis" },
      { name: "Git", canonical: "git" },
      { name: "CI/CD", canonical: "cicd" },
    ],
    matched_preferred: [
      { name: "AWS", canonical: "aws" },
      { name: "Kubernetes", canonical: "kubernetes" },
    ],
    missing_required: [
      { id: "req-pg", text: "PostgreSQL database experience", type: "required" },
      { id: "req-docker", text: "Docker containerization", type: "required" },
    ],
    keyword_matches: [
      {
        requirement: { id: "req-react", text: "React experience", type: "required" },
        evidence: {
          id: "ev-010",
          text: "Built modern interactive dashboards in React and TypeScript with component test suites.",
          section: "experience",
          page: 1,
          confidence: 0.91,
          source_file: "mock_resume_beta.pdf",
        },
        match_type: "exact",
        confidence: 0.91,
      },
      {
        requirement: { id: "req-cicd", text: "CI/CD pipelines", type: "required" },
        evidence: {
          id: "ev-011",
          text: "Authored GitHub Actions workflows for continuous integration, automated unit testing, and ECS deployment.",
          section: "experience",
          page: 2,
          confidence: 0.89,
          source_file: "mock_resume_beta.pdf",
        },
        match_type: "exact",
        confidence: 0.89,
      },
    ],
    semantic_matches: [
      {
        requirement: {
          id: "req-scalable",
          text: "Design and build scalable web applications",
          type: "responsibility",
        },
        evidence: {
          id: "ev-012",
          text: "Delivered responsive web features adopted by 15k active users with measurable reduction in page load latency.",
          section: "experience",
          page: 1,
          confidence: 0.74,
          source_file: "mock_resume_beta.pdf",
        },
        match_type: "semantic_related",
        confidence: 0.74,
        similarity: 0.75,
      },
    ],
    explanation:
      "Rank #2: Candidate Beta demonstrates balanced full-stack execution with 75% required skill coverage and notable CI/CD automated deployment skills. Primary limitations are absence of explicit PostgreSQL and Docker evidence. Semantic depth is moderate, confirming clean product feature delivery but lesser high-volume systems architecture than Alpha.",
  },
  {
    candidate_id: "MOCK-CAND-003",
    name: "Mock Candidate Gamma (Cloud & Platform Specialist)",
    candidate_name: "Mock Candidate Gamma (Cloud & Platform Specialist)",
    rank: 3,
    final_score: 0.71,
    required_coverage: 0.625, // 5 of 8
    semantic_score: 0.70,
    lexical_score: 0.76,
    preferred_coverage: 0.8, // 4 of 5
    scores: {
      final_score: 0.71,
      required_skill_coverage: 0.625,
      semantic_requirement_alignment: 0.70,
      contextual_lexical_relevance: 0.76,
      preferred_skill_coverage: 0.8,
    },
    matched_required: [
      { name: "React", canonical: "react" },
      { name: "TypeScript", canonical: "typescript" },
      { name: "PostgreSQL", canonical: "postgresql" },
      { name: "Git", canonical: "git" },
      { name: "Docker", canonical: "docker" },
    ],
    matched_preferred: [
      { name: "GraphQL", canonical: "graphql" },
      { name: "Kubernetes", canonical: "kubernetes" },
      { name: "AWS", canonical: "aws" },
      { name: "Terraform", canonical: "terraform" },
    ],
    missing_required: [
      { id: "req-node", text: "Node.js runtime development", type: "required" },
      { id: "req-rest", text: "REST API architectural patterns", type: "required" },
      { id: "req-cicd", text: "CI/CD automation pipelines", type: "required" },
    ],
    keyword_matches: [
      {
        requirement: { id: "req-docker", text: "Docker containerization", type: "required" },
        evidence: {
          id: "ev-020",
          text: "Constructed containerized environments with Docker and orchestrated microservices across Kubernetes clusters.",
          section: "experience",
          page: 1,
          confidence: 0.93,
          source_file: "mock_resume_gamma.pdf",
        },
        match_type: "exact",
        confidence: 0.93,
      },
    ],
    semantic_matches: [
      {
        requirement: {
          id: "req-scalable",
          text: "Design and build scalable web applications",
          type: "responsibility",
        },
        evidence: {
          id: "ev-021",
          text: "Built cloud-native infrastructure automation using Terraform and AWS EKS ensuring high availability and fault isolation.",
          section: "projects",
          page: 2,
          confidence: 0.72,
          source_file: "mock_resume_gamma.pdf",
        },
        match_type: "semantic_related",
        confidence: 0.72,
        similarity: 0.73,
      },
    ],
    explanation:
      "Rank #3: Candidate Gamma possesses exceptional cloud infrastructure and DevOps acumen, leading all candidates in preferred skill coverage (80% with Kubernetes, Terraform, AWS, and GraphQL). However, 3 missing core requirements (Node.js, REST APIs, CI/CD) suppress the fused score because required skills carry 3.5x higher weight than preferred skills in the ranking model.",
  },
  {
    candidate_id: "MOCK-CAND-004",
    name: "Mock Candidate Delta (Frontend Specialist)",
    candidate_name: "Mock Candidate Delta (Frontend Specialist)",
    rank: 4,
    final_score: 0.62,
    required_coverage: 0.50, // 4 of 8
    semantic_score: 0.65,
    lexical_score: 0.68,
    preferred_coverage: 0.2, // 1 of 5
    scores: {
      final_score: 0.62,
      required_skill_coverage: 0.50,
      semantic_requirement_alignment: 0.65,
      contextual_lexical_relevance: 0.68,
      preferred_skill_coverage: 0.2,
    },
    matched_required: [
      { name: "React", canonical: "react" },
      { name: "Node.js", canonical: "nodejs" },
      { name: "REST APIs", canonical: "rest-apis" },
      { name: "Git", canonical: "git" },
    ],
    matched_preferred: [
      { name: "Redis", canonical: "redis" },
    ],
    missing_required: [
      { id: "req-ts", text: "TypeScript static typing", type: "required" },
      { id: "req-pg", text: "PostgreSQL relational database", type: "required" },
      { id: "req-cicd", text: "CI/CD deployment pipelines", type: "required" },
      { id: "req-docker", text: "Docker containerization", type: "required" },
    ],
    keyword_matches: [
      {
        requirement: { id: "req-react", text: "React experience", type: "required" },
        evidence: {
          id: "ev-030",
          text: "Built customer dashboards and forms using React with JavaScript ES6 and CSS modules.",
          section: "experience",
          page: 1,
          confidence: 0.84,
          source_file: "mock_resume_delta.pdf",
        },
        match_type: "exact",
        confidence: 0.84,
      },
    ],
    semantic_matches: [
      {
        requirement: {
          id: "req-collab",
          text: "Collaborate with product and design teams",
          type: "responsibility",
        },
        evidence: {
          id: "ev-031",
          text: "Partnered with UX researchers, designers, and sprint leads to iterate on UI components based on weekly usability tests.",
          section: "experience",
          page: 1,
          confidence: 0.82,
          source_file: "mock_resume_delta.pdf",
        },
        match_type: "semantic_exact",
        confidence: 0.82,
        similarity: 0.85,
      },
    ],
    explanation:
      "Rank #4: Candidate Delta matches half of the required specifications (4 of 8). While React and client-server REST communication are present, the absence of TypeScript, PostgreSQL, and containerization restricts overall suitability for a senior full-stack mandate.",
  },
  {
    candidate_id: "MOCK-CAND-005",
    name: "Mock Candidate Epsilon (Database Analyst)",
    candidate_name: "Mock Candidate Epsilon (Database Analyst)",
    rank: 5,
    final_score: 0.48,
    required_coverage: 0.375, // 3 of 8
    semantic_score: 0.50,
    lexical_score: 0.52,
    preferred_coverage: 0.0, // 0 of 5
    scores: {
      final_score: 0.48,
      required_skill_coverage: 0.375,
      semantic_requirement_alignment: 0.50,
      contextual_lexical_relevance: 0.52,
      preferred_skill_coverage: 0.0,
    },
    matched_required: [
      { name: "Git", canonical: "git" },
      { name: "REST APIs", canonical: "rest-apis" },
      { name: "PostgreSQL", canonical: "postgresql" },
    ],
    matched_preferred: [],
    missing_required: [
      { id: "req-react", text: "React frontend framework", type: "required" },
      { id: "req-ts", text: "TypeScript programming", type: "required" },
      { id: "req-node", text: "Node.js runtime environment", type: "required" },
      { id: "req-cicd", text: "CI/CD deployment pipelines", type: "required" },
      { id: "req-docker", text: "Docker containerization", type: "required" },
    ],
    keyword_matches: [
      {
        requirement: { id: "req-pg", text: "PostgreSQL database experience", type: "required" },
        evidence: {
          id: "ev-040",
          text: "Administered relational PostgreSQL databases, wrote stored procedures, and performed query optimization.",
          section: "experience",
          page: 1,
          confidence: 0.88,
          source_file: "mock_resume_epsilon.pdf",
        },
        match_type: "exact",
        confidence: 0.88,
      },
    ],
    semantic_matches: [],
    explanation:
      "Rank #5: Candidate Epsilon demonstrates strong backend SQL and PostgreSQL database administration, but lacks 5 required full-stack technologies (React, TypeScript, Node.js, Docker, CI/CD) and has 0% preferred skill coverage, placing them at the bottom of the candidate pool.",
  },
];

export const MOCK_PAIRWISE_COMPARISONS: Record<string, PairwiseComparison> = {
  "MOCK-CAND-001_vs_MOCK-CAND-002": {
    candidate_a_id: "MOCK-CAND-001",
    candidate_b_id: "MOCK-CAND-002",
    winner_id: "MOCK-CAND-001",
    score_delta: 0.11,
    required_skill_delta: 0.125,
    semantic_delta: 0.09,
    explanation:
      "Candidate Alpha outranks Candidate Beta primarily due to higher required skill coverage (87.5% vs 75.0%) — Alpha validates 7 of 8 core requirements while Beta validates 6 of 8. Alpha demonstrates verified PostgreSQL and Docker proficiencies that Beta lacks. Furthermore, Alpha's semantic alignment score is superior (+0.09) with demonstrated experience operating high-throughput event architectures (10M+ events/day) versus Beta's product-scale experience (15k users).",
    advantages_a: [
      "Higher required skill coverage (+12.5% — 7/8 vs 6/8 skills)",
      "PostgreSQL database design & indexing verified in resume",
      "Docker multi-stage containerization verified in resume",
      "Superior semantic alignment in distributed systems architecture (0.82 vs 0.73)",
      "Higher lexical relevance across full JD vocabulary (0.91 vs 0.80)",
      "More preferred skill matches (AWS, GraphQL, Redis vs AWS, Kubernetes)",
    ],
    advantages_b: [
      "Explicit GitHub Actions CI/CD automation experience (missing in Alpha)",
      "Active Kubernetes cluster management experience",
    ],
  },
  "MOCK-CAND-001_vs_MOCK-CAND-003": {
    candidate_a_id: "MOCK-CAND-001",
    candidate_b_id: "MOCK-CAND-003",
    winner_id: "MOCK-CAND-001",
    score_delta: 0.16,
    required_skill_delta: 0.25,
    semantic_delta: 0.12,
    explanation:
      "Candidate Alpha leads Candidate Gamma by a decisive 16-point final score delta (0.87 vs 0.71). Although Gamma holds higher preferred skill coverage (80% vs 60%) through DevOps tooling, the ranking model mathematically weights required skills at 35% compared to preferred skills at 10%. Gamma's 3 missing core requirements (Node.js, REST APIs, and CI/CD) create an insurmountable deficit against Alpha's full-stack balance.",
    advantages_a: [
      "Substantially higher required coverage (+25.0% — 87.5% vs 62.5%)",
      "Node.js backend microservices expertise (critical missing requirement in Gamma)",
      "RESTful API design and implementation (missing requirement in Gamma)",
      "Superior semantic alignment (+0.12) in full-stack web application development",
    ],
    advantages_b: [
      "Higher preferred skill coverage (80% vs 60%)",
      "Deep Infrastructure-as-Code (Terraform) experience",
      "Hands-on Kubernetes cluster orchestration experience",
    ],
  },
  "MOCK-CAND-002_vs_MOCK-CAND-003": {
    candidate_a_id: "MOCK-CAND-002",
    candidate_b_id: "MOCK-CAND-003",
    winner_id: "MOCK-CAND-002",
    score_delta: 0.05,
    required_skill_delta: 0.125,
    semantic_delta: 0.03,
    explanation:
      "Candidate Beta edges out Candidate Gamma by 5 points. Beta matches 6 of 8 required skills (including Node.js and CI/CD pipelines) versus Gamma's 5 of 8. Gamma holds significant infrastructure credentials (Kubernetes, Terraform), but because required skills carry 3.5x more weight than preferred skills in the ranking model, Beta's direct alignment with day-to-day web application development responsibilities prevails.",
    advantages_a: [
      "Direct Node.js backend experience present",
      "Production CI/CD deployment automation verified",
      "Higher required skill coverage (75.0% vs 62.5%)",
    ],
    advantages_b: [
      "Superior preferred skill coverage (80% vs 40%)",
      "Docker containerization verified (missing in Beta)",
      "PostgreSQL relational database expertise (missing in Beta)",
      "Terraform cloud automation expertise",
    ],
  },
  "MOCK-CAND-003_vs_MOCK-CAND-004": {
    candidate_a_id: "MOCK-CAND-003",
    candidate_b_id: "MOCK-CAND-004",
    winner_id: "MOCK-CAND-003",
    score_delta: 0.09,
    required_skill_delta: 0.125,
    semantic_delta: 0.05,
    explanation:
      "Candidate Gamma ranks above Candidate Delta due to higher required skill coverage (62.5% vs 50.0%) and far stronger preferred skill coverage (80.0% vs 20.0%). Delta is missing TypeScript, PostgreSQL, and Docker, whereas Gamma has verified TypeScript, PostgreSQL, and Docker evidence.",
    advantages_a: [
      "TypeScript static typing verified in resume (missing in Delta)",
      "PostgreSQL relational database verified in resume (missing in Delta)",
      "Docker containerization verified in resume (missing in Delta)",
      "4 preferred skills matched (GraphQL, K8s, AWS, Terraform) vs 1 for Delta",
    ],
    advantages_b: [
      "Node.js backend experience present",
      "REST API design experience present",
    ],
  },
  "MOCK-CAND-004_vs_MOCK-CAND-005": {
    candidate_a_id: "MOCK-CAND-004",
    candidate_b_id: "MOCK-CAND-005",
    winner_id: "MOCK-CAND-004",
    score_delta: 0.14,
    required_skill_delta: 0.125,
    semantic_delta: 0.15,
    explanation:
      "Candidate Delta outperforms Candidate Epsilon primarily through modern frontend stack presence. Delta has React and Node.js capabilities, while Epsilon completely lacks frontend and application tier competencies.",
    advantages_a: [
      "React modern frontend experience verified",
      "Node.js application development verified",
      "Semantic collaboration and product feature experience",
    ],
    advantages_b: [
      "PostgreSQL database administration verified",
    ],
  },
};

export function getMockEvaluationResult(): EvaluationResult {
  return {
    job_description: MOCK_JOB_DESCRIPTION,
    candidates: MOCK_CANDIDATES,
    processing_time_ms: 1840,
    model_version: "nexora-engine-v1.0.0-mock",
  };
}

export function getMockProcessingStatus(stage: ProcessingStatus["stage"]): ProcessingStatus {
  const stages: Record<ProcessingStatus["stage"], ProcessingStatus> = {
    idle: { stage: "idle", progress: 0, message: "System ready. Upload a Job Description and Resumes to evaluate.", candidates_processed: 0, candidates_total: 0 },
    uploading: { stage: "uploading", progress: 20, message: "Ingesting JD and candidate resume documents…", candidates_processed: 0, candidates_total: 5 },
    parsing: { stage: "parsing", progress: 40, message: "Extracting structured text, sections, and candidate entities…", candidates_processed: 2, candidates_total: 5 },
    matching: { stage: "matching", progress: 65, message: "Executing dual-signal keyword & semantic embedding alignment…", candidates_processed: 4, candidates_total: 5 },
    ranking: { stage: "ranking", progress: 85, message: "Fusing scores deterministically and compiling evidence dossiers…", candidates_processed: 5, candidates_total: 5 },
    complete: { stage: "complete", progress: 100, message: "Evaluation complete. 5 candidate dossiers generated with evidence.", candidates_processed: 5, candidates_total: 5 },
    error: { stage: "error", progress: 0, message: "Evaluation pipeline failed. Please check backend service logs.", candidates_processed: 0, candidates_total: 0 },
  };
  return stages[stage];
}

export function getMockPairwiseComparison(
  candidateAId: string,
  candidateBId: string
): PairwiseComparison | null {
  const key1 = `${candidateAId}_vs_${candidateBId}`;
  if (MOCK_PAIRWISE_COMPARISONS[key1]) return MOCK_PAIRWISE_COMPARISONS[key1];

  const key2 = `${candidateBId}_vs_${candidateAId}`;
  if (MOCK_PAIRWISE_COMPARISONS[key2]) {
    const orig = MOCK_PAIRWISE_COMPARISONS[key2];
    return {
      candidate_a_id: candidateAId,
      candidate_b_id: candidateBId,
      winner_id: orig.winner_id,
      score_delta: orig.score_delta,
      required_skill_delta: -orig.required_skill_delta,
      semantic_delta: -orig.semantic_delta,
      explanation: orig.explanation,
      advantages_a: orig.advantages_b,
      advantages_b: orig.advantages_a,
    };
  }

  // Dynamic fallback for any candidate pair
  const cA = MOCK_CANDIDATES.find((c) => c.candidate_id === candidateAId);
  const cB = MOCK_CANDIDATES.find((c) => c.candidate_id === candidateBId);
  if (!cA || !cB) return null;

  const winner = cA.final_score >= cB.final_score ? cA : cB;
  const loser = winner === cA ? cB : cA;
  const delta = Math.round(Math.abs(cA.final_score - cB.final_score) * 100) / 100;
  const reqDelta = Math.round(Math.abs(cA.required_coverage - cB.required_coverage) * 100) / 100;
  const semDelta = Math.round(Math.abs(cA.semantic_score - cB.semantic_score) * 100) / 100;

  return {
    candidate_a_id: candidateAId,
    candidate_b_id: candidateBId,
    winner_id: winner.candidate_id,
    score_delta: delta,
    required_skill_delta: reqDelta,
    semantic_delta: semDelta,
    explanation: `${winner.name} ranks above ${loser.name} with an overall score delta of ${Math.round(delta * 100)} points. ${winner.name} achieves ${Math.round(winner.required_coverage * 100)}% required skill coverage compared to ${Math.round(loser.required_coverage * 100)}% for ${loser.name}.`,
    advantages_a: cA.matched_required.map((s) => `Required skill: ${s.name}`),
    advantages_b: cB.matched_required.map((s) => `Required skill: ${s.name}`),
  };
}

export function getMockCandidateById(id: string): CandidateEvaluation | null {
  return MOCK_CANDIDATES.find((c) => c.candidate_id === id) || null;
}
