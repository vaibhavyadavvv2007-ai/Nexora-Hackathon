// ============================================================
// Nexora Mock Dataset — Isolated Synthetic Test Fixtures
// Clearly labeled mock data for frontend testing and demo mode
// ============================================================

import {
  CandidateEvaluation,
  EvaluationResult,
  JobDescription,
  PairwiseComparison,
  ProcessingStatus,
  Requirement,
} from "@/types";

// Standard canonical requirements for the mock job description
export const MOCK_REQUIREMENTS: Requirement[] = [
  {
    id: "req-001",
    name: "React Frontend Framework",
    canonical_name: "react",
    type: "required",
    weight: 1.0,
    critical: true,
    source_text: "3+ years production experience with modern React, hooks, and component architecture.",
  },
  {
    id: "req-002",
    name: "TypeScript Typing",
    canonical_name: "typescript",
    type: "required",
    weight: 1.0,
    critical: true,
    source_text: "Strong TypeScript proficiency with strict type checking in enterprise applications.",
  },
  {
    id: "req-003",
    name: "Node.js Backend Runtime",
    canonical_name: "nodejs",
    type: "required",
    weight: 0.9,
    critical: true,
    source_text: "Demonstrated backend server development in Node.js (Express, Nest, or Fastify).",
  },
  {
    id: "req-004",
    name: "PostgreSQL Relational DB",
    canonical_name: "postgresql",
    type: "required",
    weight: 0.9,
    critical: true,
    source_text: "Hands-on schema design, query optimization, and indexing with PostgreSQL.",
  },
  {
    id: "req-005",
    name: "REST API Design",
    canonical_name: "rest_api",
    type: "required",
    weight: 0.8,
    critical: false,
    source_text: "Design, implementation, and documentation of resilient RESTful HTTP APIs.",
  },
  {
    id: "req-006",
    name: "Git Version Control",
    canonical_name: "git",
    type: "required",
    weight: 0.7,
    critical: false,
    source_text: "Collaborative Git branching workflows and code review processes.",
  },
  {
    id: "req-007",
    name: "CI/CD Pipeline Automation",
    canonical_name: "cicd",
    type: "required",
    weight: 0.8,
    critical: true,
    source_text: "Experience building and maintaining automated CI/CD pipelines (GitHub Actions, GitLab CI).",
  },
  {
    id: "req-008",
    name: "Docker Containerization",
    canonical_name: "docker",
    type: "required",
    weight: 0.8,
    critical: false,
    source_text: "Multi-stage Docker containerization and service orchestration via docker-compose.",
  },
  // Preferred requirements
  {
    id: "pref-001",
    name: "GraphQL Query Language",
    canonical_name: "graphql",
    type: "preferred",
    weight: 0.6,
    critical: false,
    source_text: "Familiarity with GraphQL schema design and client integration (Apollo/Relay).",
  },
  {
    id: "pref-002",
    name: "Kubernetes Orchestration",
    canonical_name: "kubernetes",
    type: "preferred",
    weight: 0.7,
    critical: false,
    source_text: "Experience managing containerized services on Kubernetes clusters.",
  },
  {
    id: "pref-003",
    name: "AWS Cloud Services",
    canonical_name: "aws",
    type: "preferred",
    weight: 0.7,
    critical: false,
    source_text: "Deployment and architectural experience on AWS (ECS, S3, RDS, Lambda).",
  },
  {
    id: "pref-004",
    name: "Redis In-Memory Caching",
    canonical_name: "redis",
    type: "preferred",
    weight: 0.5,
    critical: false,
    source_text: "Redis caching patterns, session storage, or pub/sub implementation.",
  },
  {
    id: "pref-005",
    name: "Terraform Infrastructure as Code",
    canonical_name: "terraform",
    type: "preferred",
    weight: 0.6,
    critical: false,
    source_text: "Infrastructure provisioned using declarative Terraform modules.",
  },
];

export const MOCK_JOB_DESCRIPTION: JobDescription = {
  id: "mock-jd-senior-fullstack",
  title: "Senior Full-Stack Engineer (Search & AI Systems)",
  source_file: "Senior_FullStack_Engineer_JD.pdf",
  raw_text:
    "We are seeking a Senior Full-Stack Engineer to architect, build, and scale our next-generation search and intelligence platform. You will lead technical delivery from React/TypeScript frontends through high-throughput Node.js microservices and PostgreSQL data stores. Experience with Docker containerization, automated CI/CD pipelines, and cloud services (AWS) is essential.",
  requirements: MOCK_REQUIREMENTS,
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
  preferred_skills: ["GraphQL", "Kubernetes", "AWS", "Redis", "Terraform"],
  responsibilities: [
    "Architect responsive, accessible web applications with modern state management.",
    "Implement low-latency REST and streaming API endpoints with robust error boundaries.",
    "Optimize relational database queries, migration plans, and data models.",
    "Lead code quality standards, automated testing suites, and developer mentorship.",
  ],
};

export const MOCK_CANDIDATES: CandidateEvaluation[] = [
  {
    candidate_id: "MOCK-CAND-001",
    name: "Synthetic Candidate Alpha",
    candidate_name: "Synthetic Candidate Alpha",
    rank: 1,
    final_score: 0.87,
    required_coverage: 0.875, // 7/8
    semantic_score: 0.82,
    lexical_score: 0.91,
    preferred_coverage: 0.6, // 3/5
    scores: {
      final_score: 0.87,
      required_skill_coverage: 0.875,
      semantic_requirement_alignment: 0.82,
      contextual_lexical_relevance: 0.91,
      preferred_skill_coverage: 0.6,
    },
    matched_required: MOCK_REQUIREMENTS.filter((r) =>
      ["req-001", "req-002", "req-003", "req-004", "req-005", "req-006", "req-008"].includes(r.id)
    ),
    matched_preferred: MOCK_REQUIREMENTS.filter((r) =>
      ["pref-001", "pref-003", "pref-004"].includes(r.id)
    ),
    missing_required: MOCK_REQUIREMENTS.filter((r) => r.id === "req-007"),
    keyword_matches: [
      {
        requirement: MOCK_REQUIREMENTS[0], // React
        evidence: {
          text: "Architected production React web application serving 50k+ daily active users with TypeScript and custom hooks.",
          section: "experience",
          page: 1,
          source_file: "mock_resume_alpha.pdf",
          confidence: 0.96,
          match_type: "exact",
          similarity: null,
        },
        match_type: "exact",
        confidence: 0.96,
      },
      {
        requirement: MOCK_REQUIREMENTS[2], // Node.js
        evidence: {
          text: "Developed low-latency RESTful microservices using Node.js and Express connected to PostgreSQL clusters.",
          section: "experience",
          page: 1,
          source_file: "mock_resume_alpha.pdf",
          confidence: 0.94,
          match_type: "exact",
          similarity: null,
        },
        match_type: "exact",
        confidence: 0.94,
      },
      {
        requirement: MOCK_REQUIREMENTS[3], // PostgreSQL
        evidence: {
          text: "Designed normalized schemas, optimized query plans with EXPLAIN ANALYZE, and managed PostgreSQL replicas.",
          section: "experience",
          page: 2,
          source_file: "mock_resume_alpha.pdf",
          confidence: 0.92,
          match_type: "exact",
          similarity: null,
        },
        match_type: "exact",
        confidence: 0.92,
      },
      {
        requirement: MOCK_REQUIREMENTS[7], // Docker
        evidence: {
          text: "Containerized multi-tier applications using multi-stage Docker builds to reduce image size by 65%.",
          section: "experience",
          page: 2,
          source_file: "mock_resume_alpha.pdf",
          confidence: 0.90,
          match_type: "exact",
          similarity: null,
        },
        match_type: "exact",
        confidence: 0.90,
      },
    ],
    semantic_matches: [
      {
        requirement: {
          id: "resp-001",
          name: "High-Throughput Systems Architecture",
          canonical_name: "scalable_architecture",
          type: "responsibility",
          weight: 1.0,
          critical: false,
          source_text: "Architect responsive, accessible web applications with modern state management.",
        },
        evidence: {
          text: "Engineered horizontally scalable event ingestion pipeline handling 10M+ events daily with 99.95% service uptime.",
          section: "experience",
          page: 1,
          source_file: "mock_resume_alpha.pdf",
          confidence: 0.91,
          match_type: "semantic_exact",
          similarity: 0.89,
        },
        match_type: "semantic_exact",
        confidence: 0.91,
        similarity: 0.89,
      },
      {
        requirement: {
          id: "resp-004",
          name: "Developer Mentorship & Code Quality",
          canonical_name: "mentorship",
          type: "responsibility",
          weight: 0.8,
          critical: false,
          source_text: "Lead code quality standards, automated testing suites, and developer mentorship.",
        },
        evidence: {
          text: "Supervised and mentored 4 junior and mid-level software engineers through structured weekly pair programming.",
          section: "experience",
          page: 2,
          source_file: "mock_resume_alpha.pdf",
          confidence: 0.88,
          match_type: "semantic_exact",
          similarity: 0.87,
        },
        match_type: "semantic_exact",
        confidence: 0.88,
        similarity: 0.87,
      },
    ],
    evidence: [
      {
        text: "Architected production React web application serving 50k+ daily active users with TypeScript and custom hooks.",
        section: "experience",
        page: 1,
        source_file: "mock_resume_alpha.pdf",
        confidence: 0.96,
        match_type: "exact",
        similarity: null,
      },
      {
        text: "Engineered horizontally scalable event ingestion pipeline handling 10M+ events daily with 99.95% service uptime.",
        section: "experience",
        page: 1,
        source_file: "mock_resume_alpha.pdf",
        confidence: 0.91,
        match_type: "semantic_exact",
        similarity: 0.89,
      },
    ],
    explanation:
      "Rank #1: Candidate Alpha achieves top placement with 87.5% required skill coverage (7 of 8). Demonstrates verified depth in React, TypeScript, Node.js, and PostgreSQL. Holds the highest lexical relevance score in the cohort (0.91) and verified semantic evidence of scalable system design. Missing CI/CD pipeline automation is the primary gap.",
    parsing_status: "success",
  },
  {
    candidate_id: "MOCK-CAND-002",
    name: "Synthetic Candidate Beta",
    candidate_name: "Synthetic Candidate Beta",
    rank: 2,
    final_score: 0.76,
    required_coverage: 0.75, // 6/8
    semantic_score: 0.73,
    lexical_score: 0.80,
    preferred_coverage: 0.4, // 2/5
    scores: {
      final_score: 0.76,
      required_skill_coverage: 0.75,
      semantic_requirement_alignment: 0.73,
      contextual_lexical_relevance: 0.80,
      preferred_skill_coverage: 0.4,
    },
    matched_required: MOCK_REQUIREMENTS.filter((r) =>
      ["req-001", "req-002", "req-003", "req-005", "req-006", "req-007"].includes(r.id)
    ),
    matched_preferred: MOCK_REQUIREMENTS.filter((r) =>
      ["pref-002", "pref-003"].includes(r.id)
    ),
    missing_required: MOCK_REQUIREMENTS.filter((r) =>
      ["req-004", "req-008"].includes(r.id)
    ), // PostgreSQL, Docker
    keyword_matches: [
      {
        requirement: MOCK_REQUIREMENTS[0], // React
        evidence: {
          text: "Built interactive web dashboards in React and TypeScript with component unit test suites.",
          section: "experience",
          page: 1,
          source_file: "mock_resume_beta.pdf",
          confidence: 0.91,
          match_type: "exact",
          similarity: null,
        },
        match_type: "exact",
        confidence: 0.91,
      },
      {
        requirement: MOCK_REQUIREMENTS[6], // CI/CD
        evidence: {
          text: "Configured GitHub Actions CI/CD workflows for continuous integration, linting, and automated staging releases.",
          section: "experience",
          page: 2,
          source_file: "mock_resume_beta.pdf",
          confidence: 0.89,
          match_type: "exact",
          similarity: null,
        },
        match_type: "exact",
        confidence: 0.89,
      },
    ],
    semantic_matches: [
      {
        requirement: {
          id: "resp-001",
          name: "High-Throughput Systems Architecture",
          canonical_name: "scalable_architecture",
          type: "responsibility",
          weight: 1.0,
          critical: false,
          source_text: "Architect responsive, accessible web applications with modern state management.",
        },
        evidence: {
          text: "Delivered responsive web features adopted by 15k active users with measurable reduction in page load latency.",
          section: "experience",
          page: 1,
          source_file: "mock_resume_beta.pdf",
          confidence: 0.74,
          match_type: "semantic_related",
          similarity: 0.75,
        },
        match_type: "semantic_related",
        confidence: 0.74,
        similarity: 0.75,
      },
    ],
    evidence: [
      {
        text: "Configured GitHub Actions CI/CD workflows for continuous integration, linting, and automated staging releases.",
        section: "experience",
        page: 2,
        source_file: "mock_resume_beta.pdf",
        confidence: 0.89,
        match_type: "exact",
        similarity: null,
      },
    ],
    explanation:
      "Rank #2: Candidate Beta shows balanced full-stack execution with 75% required coverage (6 of 8) and strong verified CI/CD automation. Missing explicit PostgreSQL and Docker evidence restricts higher ranking.",
    parsing_status: "success",
  },
  {
    candidate_id: "MOCK-CAND-003",
    name: "Synthetic Candidate Gamma",
    candidate_name: "Synthetic Candidate Gamma",
    rank: 3,
    final_score: 0.71,
    required_coverage: 0.625, // 5/8
    semantic_score: 0.70,
    lexical_score: 0.76,
    preferred_coverage: 0.8, // 4/5
    scores: {
      final_score: 0.71,
      required_skill_coverage: 0.625,
      semantic_requirement_alignment: 0.70,
      contextual_lexical_relevance: 0.76,
      preferred_skill_coverage: 0.8,
    },
    matched_required: MOCK_REQUIREMENTS.filter((r) =>
      ["req-001", "req-002", "req-004", "req-006", "req-008"].includes(r.id)
    ),
    matched_preferred: MOCK_REQUIREMENTS.filter((r) =>
      ["pref-001", "pref-002", "pref-003", "pref-005"].includes(r.id)
    ),
    missing_required: MOCK_REQUIREMENTS.filter((r) =>
      ["req-003", "req-005", "req-007"].includes(r.id)
    ), // Node, REST, CI/CD
    keyword_matches: [
      {
        requirement: MOCK_REQUIREMENTS[7], // Docker
        evidence: {
          text: "Constructed containerized environments with Docker and orchestrated microservices across Kubernetes clusters.",
          section: "experience",
          page: 1,
          source_file: "mock_resume_gamma.pdf",
          confidence: 0.93,
          match_type: "exact",
          similarity: null,
        },
        match_type: "exact",
        confidence: 0.93,
      },
    ],
    semantic_matches: [
      {
        requirement: {
          id: "resp-001",
          name: "Cloud-Native Infrastructure",
          canonical_name: "cloud_infrastructure",
          type: "responsibility",
          weight: 1.0,
          critical: false,
          source_text: "Deployment and architectural experience on AWS.",
        },
        evidence: {
          text: "Built cloud-native infrastructure automation using Terraform and AWS EKS ensuring high availability.",
          section: "projects",
          page: 2,
          source_file: "mock_resume_gamma.pdf",
          confidence: 0.72,
          match_type: "semantic_related",
          similarity: 0.73,
        },
        match_type: "semantic_related",
        confidence: 0.72,
        similarity: 0.73,
      },
    ],
    evidence: [
      {
        text: "Built cloud-native infrastructure automation using Terraform and AWS EKS ensuring high availability.",
        section: "projects",
        page: 2,
        source_file: "mock_resume_gamma.pdf",
        confidence: 0.72,
        match_type: "semantic_related",
        similarity: 0.73,
      },
    ],
    explanation:
      "Rank #3: Candidate Gamma possesses exceptional cloud infrastructure credentials, leading the cohort in preferred coverage (80% with Kubernetes, Terraform, AWS, GraphQL). However, 3 missing required skills (Node.js, REST APIs, CI/CD) suppress the overall score because required skills carry 3.5x higher weight in the mathematical fusion model.",
    parsing_status: "success",
  },
  {
    candidate_id: "MOCK-CAND-004",
    name: "Synthetic Candidate Delta",
    candidate_name: "Synthetic Candidate Delta",
    rank: 4,
    final_score: 0.62,
    required_coverage: 0.50, // 4/8
    semantic_score: 0.65,
    lexical_score: 0.68,
    preferred_coverage: 0.2, // 1/5
    scores: {
      final_score: 0.62,
      required_skill_coverage: 0.50,
      semantic_requirement_alignment: 0.65,
      contextual_lexical_relevance: 0.68,
      preferred_skill_coverage: 0.2,
    },
    matched_required: MOCK_REQUIREMENTS.filter((r) =>
      ["req-001", "req-003", "req-005", "req-006"].includes(r.id)
    ),
    matched_preferred: MOCK_REQUIREMENTS.filter((r) => r.id === "pref-004"),
    missing_required: MOCK_REQUIREMENTS.filter((r) =>
      ["req-002", "req-004", "req-007", "req-008"].includes(r.id)
    ), // TypeScript, PostgreSQL, CI/CD, Docker
    keyword_matches: [
      {
        requirement: MOCK_REQUIREMENTS[0], // React
        evidence: {
          text: "Built customer dashboards and forms using React with JavaScript ES6 and CSS modules.",
          section: "experience",
          page: 1,
          source_file: "mock_resume_delta.pdf",
          confidence: 0.84,
          match_type: "exact",
          similarity: null,
        },
        match_type: "exact",
        confidence: 0.84,
      },
    ],
    semantic_matches: [],
    evidence: [],
    explanation:
      "Rank #4: Candidate Delta matches half of the required specifications (4 of 8). React and REST experience are verified, but absence of TypeScript, PostgreSQL, Docker, and CI/CD presents significant technical risk.",
    parsing_status: "success",
  },
  {
    candidate_id: "MOCK-CAND-005",
    name: "Synthetic Candidate Epsilon",
    candidate_name: "Synthetic Candidate Epsilon",
    rank: 5,
    final_score: 0.48,
    required_coverage: 0.375, // 3/8
    semantic_score: 0.50,
    lexical_score: 0.52,
    preferred_coverage: 0.0, // 0/5
    scores: {
      final_score: 0.48,
      required_skill_coverage: 0.375,
      semantic_requirement_alignment: 0.50,
      contextual_lexical_relevance: 0.52,
      preferred_skill_coverage: 0.0,
    },
    matched_required: MOCK_REQUIREMENTS.filter((r) =>
      ["req-004", "req-005", "req-006"].includes(r.id)
    ),
    matched_preferred: [],
    missing_required: MOCK_REQUIREMENTS.filter((r) =>
      ["req-001", "req-002", "req-003", "req-007", "req-008"].includes(r.id)
    ),
    keyword_matches: [
      {
        requirement: MOCK_REQUIREMENTS[3], // PostgreSQL
        evidence: {
          text: "Administered relational PostgreSQL databases, wrote complex stored procedures, and performed query tuning.",
          section: "experience",
          page: 1,
          source_file: "mock_resume_epsilon.pdf",
          confidence: 0.88,
          match_type: "exact",
          similarity: null,
        },
        match_type: "exact",
        confidence: 0.88,
      },
    ],
    semantic_matches: [],
    evidence: [],
    explanation:
      "Rank #5: Candidate Epsilon possesses strong database administration experience, but lacks 5 required full-stack competencies including React and TypeScript frontend, placing them at the bottom of the candidate cohort.",
    parsing_status: "warning",
    parsing_warnings: ["Resume contained low text density in section: Projects. OCR fallback engaged."],
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
    lexical_delta: 0.11,
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
    missing_skills_diff: {
      only_a_missing: ["CI/CD Pipeline Automation"],
      only_b_missing: ["PostgreSQL Relational DB", "Docker Containerization"],
      both_missing: [],
    },
  },
  "MOCK-CAND-001_vs_MOCK-CAND-003": {
    candidate_a_id: "MOCK-CAND-001",
    candidate_b_id: "MOCK-CAND-003",
    winner_id: "MOCK-CAND-001",
    score_delta: 0.16,
    required_skill_delta: 0.25,
    semantic_delta: 0.12,
    lexical_delta: 0.15,
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
    missing_skills_diff: {
      only_a_missing: [],
      only_b_missing: ["Node.js Backend Runtime", "REST API Design"],
      both_missing: ["CI/CD Pipeline Automation"],
    },
  },
  "MOCK-CAND-002_vs_MOCK-CAND-003": {
    candidate_a_id: "MOCK-CAND-002",
    candidate_b_id: "MOCK-CAND-003",
    winner_id: "MOCK-CAND-002",
    score_delta: 0.05,
    required_skill_delta: 0.125,
    semantic_delta: 0.03,
    lexical_delta: 0.04,
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
    missing_skills_diff: {
      only_a_missing: ["PostgreSQL Relational DB", "Docker Containerization"],
      only_b_missing: ["Node.js Backend Runtime", "REST API Design", "CI/CD Pipeline Automation"],
      both_missing: [],
    },
  },
};

export function getMockEvaluationResult(): EvaluationResult {
  return {
    job_description: MOCK_JOB_DESCRIPTION,
    candidates: MOCK_CANDIDATES,
    processing_time_ms: 1840,
    model_version: "nexora-engine-v1.0.0-mock",
    failed_candidates: [],
  };
}

export function getMockProcessingStatus(stage: ProcessingStatus["stage"]): ProcessingStatus {
  const stages: Record<ProcessingStatus["stage"], ProcessingStatus> = {
    idle: {
      stage: "idle",
      progress: 0,
      message: "System idle. Awaiting document ingestion.",
      jd_processed: false,
      resumes_processed: 0,
      resumes_total: 5,
      semantic_model_status: "idle",
      keyword_engine_status: "idle",
      ranking_status: "idle",
      failed_resumes: [],
    },
    uploading: {
      stage: "uploading",
      progress: 20,
      message: "Uploading 1 Job Description and 5 Candidate Resumes...",
      jd_processed: true,
      resumes_processed: 1,
      resumes_total: 5,
      semantic_model_status: "idle",
      keyword_engine_status: "idle",
      ranking_status: "idle",
      failed_resumes: [],
    },
    parsing: {
      stage: "parsing",
      progress: 45,
      message: "Parsing text and segmenting document sections (Experience, Skills, Projects)...",
      jd_processed: true,
      resumes_processed: 3,
      resumes_total: 5,
      semantic_model_status: "loading",
      keyword_engine_status: "indexing",
      ranking_status: "idle",
      failed_resumes: [],
    },
    matching: {
      stage: "matching",
      progress: 70,
      message: "Executing dual-signal keyword matching and sentence-transformer embeddings...",
      jd_processed: true,
      resumes_processed: 5,
      resumes_total: 5,
      semantic_model_status: "encoding",
      keyword_engine_status: "matching",
      ranking_status: "idle",
      failed_resumes: [],
    },
    ranking: {
      stage: "ranking",
      progress: 90,
      message: "Computing deterministic fused scores and synthesizing evidence dossiers...",
      jd_processed: true,
      resumes_processed: 5,
      resumes_total: 5,
      semantic_model_status: "ready",
      keyword_engine_status: "ready",
      ranking_status: "computing",
      failed_resumes: [],
    },
    complete: {
      stage: "complete",
      progress: 100,
      message: "Shortlisting complete. 5 candidate dossiers generated with score transparency.",
      jd_processed: true,
      resumes_processed: 5,
      resumes_total: 5,
      semantic_model_status: "ready",
      keyword_engine_status: "ready",
      ranking_status: "complete",
      failed_resumes: [],
    },
    error: {
      stage: "error",
      progress: 0,
      message: "Evaluation pipeline encountered a server failure.",
      jd_processed: false,
      resumes_processed: 0,
      resumes_total: 0,
      semantic_model_status: "error",
      keyword_engine_status: "error",
      ranking_status: "error",
      failed_resumes: [{ filename: "corrupted_file.pdf", reason: "Invalid PDF format or OCR unreadable" }],
    },
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
      lexical_delta: orig.lexical_delta ? -orig.lexical_delta : undefined,
      explanation: orig.explanation,
      advantages_a: orig.advantages_b,
      advantages_b: orig.advantages_a,
      missing_skills_diff: orig.missing_skills_diff
        ? {
            only_a_missing: orig.missing_skills_diff.only_b_missing,
            only_b_missing: orig.missing_skills_diff.only_a_missing,
            both_missing: orig.missing_skills_diff.both_missing,
          }
        : undefined,
    };
  }

  // Dynamic fallback for arbitrary candidate comparisons
  const cA = MOCK_CANDIDATES.find((c) => c.candidate_id === candidateAId);
  const cB = MOCK_CANDIDATES.find((c) => c.candidate_id === candidateBId);
  if (!cA || !cB) return null;

  const winner = cA.final_score >= cB.final_score ? cA : cB;
  const delta = Math.round(Math.abs(cA.final_score - cB.final_score) * 100) / 100;
  const reqDelta = Math.round(Math.abs(cA.required_coverage - cB.required_coverage) * 100) / 100;
  const semDelta = Math.round(Math.abs(cA.semantic_score - cB.semantic_score) * 100) / 100;

  const aMissingNames = cA.missing_required.map((r) => r.name);
  const bMissingNames = cB.missing_required.map((r) => r.name);

  return {
    candidate_a_id: candidateAId,
    candidate_b_id: candidateBId,
    winner_id: winner.candidate_id,
    score_delta: delta,
    required_skill_delta: reqDelta,
    semantic_delta: semDelta,
    explanation: `${winner.name} ranks ahead with an overall score delta of ${Math.round(delta * 100)} points. ${winner.name} demonstrates ${Math.round(winner.required_coverage * 100)}% required skill coverage versus ${Math.round((winner === cA ? cB : cA).required_coverage * 100)}% for the competitor.`,
    advantages_a: cA.matched_required.map((r) => `Verified required skill: ${r.name}`),
    advantages_b: cB.matched_required.map((r) => `Verified required skill: ${r.name}`),
    missing_skills_diff: {
      only_a_missing: aMissingNames.filter((x) => !bMissingNames.includes(x)),
      only_b_missing: bMissingNames.filter((x) => !aMissingNames.includes(x)),
      both_missing: aMissingNames.filter((x) => bMissingNames.includes(x)),
    },
  };
}

export function getMockCandidateById(id: string): CandidateEvaluation | null {
  return MOCK_CANDIDATES.find((c) => c.candidate_id === id) || null;
}
