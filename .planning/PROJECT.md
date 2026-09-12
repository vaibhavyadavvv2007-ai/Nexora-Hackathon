# Nexora — Smart Shortlisting Engine

## Project Context
- **Event**: InternLoom AI Hackathon
- **Objective**: Build an explainable, dual-signal candidate evaluation and shortlisting engine that ranks 15–18 resume PDFs against a single Job Description (JD) PDF.
- **Key Tenet**: The ranking engine must **NOT** simply dump the JD and resumes into an LLM and request a score. It relies on deterministic parsing, genuine keyword matching, local sentence embedding semantic matching, mathematical score fusion, and evidence-backed explanations.

---

## Approved Architecture

### 1. Job Description (JD) Processing
```
JD PDF Extraction (PyMuPDF)
 └── Structured Requirements
      ├── Required Skills (must-have)
      ├── Preferred Skills (nice-to-have)
      ├── Responsibilities & Domain Context
      └── Requirement Evidence Expectations
```

### 2. Resume Processing
```
Resume PDF Extraction (PyMuPDF)
 └── Section Detection (Work Experience, Skills, Education, Projects, Certifications)
      └── Normalization & Clean Tokenization
           ├── Evidence Chunks (sentences / bullet points tied to section & context)
           └── Normalized Skills (standardized aliases & canonical skill tags)
```

### 3. Dual Matching Engines

#### Engine A: Keyword Matching Engine
- Exact skill matching
- Conservative aliases (e.g. `k8s` -> `Kubernetes`, `ReactJS` -> `React`)
- Phrase matching (multi-word terms like "Machine Learning", "System Design")
- Fuzzy matching where justified via `rapidfuzz` (with high threshold to prevent false positives)
- Optional BM25 lexical relevance
- Section-aware evidence weighting (e.g. skills proven in `Work Experience` weighted higher than standalone list)
- Duplicate suppression (repeated mentions do not artificially inflate scores)

#### Engine B: Semantic Matching Engine
- Local sentence-transformers (starting with `sentence-transformers/all-MiniLM-L6-v2`)
- Requirement-to-resume-evidence matching (sentence/chunk level)
- Cosine similarity computation via `scikit-learn`
- Strongest evidence retention per requirement
- Strict similarity thresholding
- Distinction between:
  - **Exact**: Identical or direct alias match
  - **Related**: High semantic alignment on similar concepts/tools
  - **Inferred**: Contextual domain application without explicit naming

### 4. Score Fusion Formula
The overall candidate score is computed deterministically:
$$\text{Final Score} = 0.35 \times S_{\text{req}} + 0.35 \times S_{\text{semantic}} + 0.20 \times S_{\text{lexical}} + 0.10 \times S_{\text{pref}}$$

Where:
- $S_{\text{req}}$ = Explicit named required skill coverage ratio $[0.0, 1.0]$
- $S_{\text{semantic}}$ = Semantic requirement-to-evidence alignment $[0.0, 1.0]$
- $S_{\text{lexical}}$ = BM25/lexical context relevance $[0.0, 1.0]$
- $S_{\text{pref}}$ = Explicit named preferred skill coverage ratio $[0.0, 1.0]$

**Critical Integrity Requirement**: All intermediate component scores, extracted evidence chunks, and matched/missing skill lists must be persisted in candidate evaluation records. Contextual lexical relevance must not simply duplicate required skill coverage.

---

### 5. Explanations & Comparative Features

#### Deterministic Explanations
- Template-backed and derived directly from structured evaluation records
- Must never invent skills or hallucinate experience
- Mandatory breakdown:
  - Top 3 candidates: Deep-dive justification with supporting evidence quotes
  - Matched skills and explicitly highlighted **missing required skills**
  - Component score radar/bar breakdown

#### Pairwise Comparison Engine
- Feature: *"Why did Candidate X rank above Candidate Y?"*
- Compares stored evaluation records (skill delta, semantic evidence strength, required skill gaps)
- Computed deterministically without re-running or delegating ranking logic to an LLM.

---

## Technical Stack & Constraints

### Approved Tech Stack
- **Backend Language & Framework**: Python 3.10+, FastAPI, Pydantic
- **PDF Extraction**: `PyMuPDF` (`fitz`)
- **Embeddings & Semantic Search**: `sentence-transformers` (`all-MiniLM-L6-v2`), `scikit-learn`
- **Lexical & Fuzzy Search**: `rank-bm25`, `rapidfuzz`
- **Testing**: `pytest` with synthetic inline fixtures
- **Frontend (Future)**: Next.js, React, TypeScript, Tailwind CSS (not implemented yet)

### Strict Scope Boundaries
- **DO NOT ADD**:
  - Microservices or distributed queues
  - Authentication or user management
  - Databases (SQLite / PostgreSQL) — evaluation records remain in-memory / JSON structured output
  - Multi-job description support
  - Ruflo or heavy LLM agent frameworks
  - Unnecessary LLM orchestration (rankings and explanations are evidence-driven)

---

## Current Status & Next Actions
- **Current State**: Real JD PDF and 15–18 resume PDFs are pending delivery.
- **Immediate Task**: Establish repository foundation, data models, module interfaces, mock-driven unit tests, dependency configuration, and documentation.
- **Hold**: No hardcoding of actual JD requirements, candidate names, or imaginary candidate weights until real PDFs are provided.
