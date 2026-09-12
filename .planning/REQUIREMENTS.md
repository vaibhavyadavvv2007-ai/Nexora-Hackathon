# Requirements: Nexora — Smart Shortlisting Engine

## 1. System Vision & Core Objectives
Nexora evaluates and ranks candidate resumes against a Job Description (JD) using a dual-signal pipeline (genuine keyword matching + genuine semantic matching). The engine generates transparent, auditable match scores and deterministic justifications.

---

## 2. Functional Requirements

### 2.1 Ingestion & Extraction (EXT)
- **EXT-01**: Ingest a single Job Description PDF and extract structured data:
  - Required skills (must-have)
  - Preferred skills (nice-to-have)
  - Responsibilities & context
  - Requirement chunks with metadata
- **EXT-02**: Ingest 15–18 Resume PDFs and extract structured sections:
  - Section identification (Experience, Education, Skills, Projects, Certifications)
  - Normalization of text (whitespace, casing, punctuation)
  - Evidence chunking (sentence/bullet point level preserved with section attribution)
- **EXT-03**: Skill normalization using canonical aliases (e.g. `k8s` -> `kubernetes`, `py` -> `python`).

### 2.2 Dual Matching Engines (ENG)
- **ENG-01 (Keyword Engine)**:
  - Exact skill matching across resume text and extracted skills.
  - Conservative alias resolution and phrase matching for multi-token technologies.
  - Fuzzy matching via `rapidfuzz` with calibrated strict threshold.
  - Section-weighted evidence scoring (e.g., skill demonstrated in Experience > mentioned in Skills section).
  - Duplicate suppression: duplicate mentions do not distort the keyword score.
- **ENG-02 (Semantic Engine)**:
  - Local embedding generation via `sentence-transformers/all-MiniLM-L6-v2`.
  - Pairwise requirement-to-evidence chunk cosine similarity computation.
  - Retain top evidence match per requirement chunk with similarity score.
  - Filter by calibrated similarity threshold and categorize match strength (Exact, Related, Inferred).
- **ENG-03 (Signal Independence & Materiality)**:
  - Keyword and semantic engines must execute independently.
  - Both keyword and semantic signals must materially influence final ranking.

### 2.3 Scoring & Ranking (SCR)
- **SCR-01**: Deterministic score fusion using the exact formula:
  $$\text{Final Score} = 0.35 \times S_{\text{req}} + 0.35 \times S_{\text{semantic}} + 0.20 \times S_{\text{lexical}} + 0.10 \times S_{\text{pref}}$$
- **SCR-02**: Calculate and record all individual component scores:
  - Required skill coverage ($S_{\text{req}}$)
  - Semantic requirement alignment ($S_{\text{semantic}}$)
  - Contextual lexical relevance ($S_{\text{lexical}}$)
  - Preferred skill coverage ($S_{\text{pref}}$)
- **SCR-03**: Produce deterministic ranking of all candidates from highest to lowest final score with tie-breaking rules (e.g. required skill coverage as primary tie-breaker).
- **SCR-04**: Store full evaluation records (metadata, scores, evidence quotes, matched skills, missing required skills) for every candidate.

### 2.4 Explanations & Comparisons (EXP)
- **EXP-01**: Generate deterministic, template-backed natural language explanations for the Top 3 candidates.
- **EXP-02**: Clearly display matched skills and explicitly highlight missing required skills for every evaluated candidate.
- **EXP-03**: Never hallucinate or invent skills/evidence not present in the extracted candidate record.
- **EXP-04 (Pairwise Comparison)**:
  - Implement "Why did Candidate X rank above Candidate Y?" feature.
  - Compare stored evaluation records directly (required skill delta, component score breakdown, key differentiators in semantic evidence).
  - Deterministic comparison without re-ranking or prompting an LLM.

### 2.5 User Interface & Presentation (UI)
- **UI-01**: Interactive UI (Streamlit) to view ranking table, score breakdowns, candidate dossiers, and radar/bar charts.
- **UI-02**: Side-by-side pairwise candidate comparison view.
- **UI-03**: Export summary report (JSON and Markdown) in `outputs/`.

---

## 3. Non-Functional & Operational Constraints

- **NFR-01 (Offline & Local Execution)**: Semantic embeddings and matching must execute locally via `all-MiniLM-L6-v2` without requiring external LLM API keys for basic scoring.
- **NFR-02 (No Bloat)**: No databases, no auth, no microservices, no multi-tenant infrastructure.
- **NFR-03 (Reproducibility & Testability)**: All algorithms must be deterministic; running the pipeline twice on identical input produces identical outputs.
- **NFR-04 (Synthetic Isolation)**: Current tests must use inline synthetic mock fixtures. No hallucinated resume PDFs or fabricated real applicant data.
