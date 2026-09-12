# Nexora — Smart Shortlisting Engine

**Explainable AI candidate shortlisting for technical hiring.**

Recruiters evaluating a stack of resumes against one role face a trade-off: keyword filtering misses semantically relevant experience, while LLM-first scoring can produce rankings without transparent, verifiable evidence. Nexora takes a third path — it independently evaluates explicit required skills, semantic alignment, and contextual lexical relevance, then combines them through a fixed scoring function into a deterministic ranking where every placement is backed by resume evidence with page and section context. **Nexora doesn't just rank candidates — it explains why.**

> **Nexora never uses an LLM to assign a candidate score.**

---

## Quick Demo

```bash
# 1. Backend (Python 3.10+)
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --port 8000

# 2. Frontend (Node 18+)
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**, switch to **Live API Mode**, click **Ingest Documents**, upload `data/official/Sample_JD.pdf` plus the `Resume_*.pdf` batch, and start the analysis (≈40 s; the first run downloads the local embedding model once).

---

## Why Nexora?

Every placement in a Nexora ranking answers three questions:

1. **Does the candidate explicitly have the required skill?** → Required Skill Coverage
2. **Does their experience semantically align with the requirement?** → Semantic Requirement Alignment
3. **Does the surrounding resume context support that relevance?** → Contextual Lexical Relevance

These signals are evaluated separately and combined through a fixed scoring function — no signal is hidden inside a model's output, and none can silently dominate the ranking.

| Aspect | LLM-first scoring | Nexora |
|---|---|---|
| Scoring | Opaque, model-generated score | Four measurable components with explicit weights |
| Evidence | Generated or difficult to trace | Stored resume evidence with section/page context |
| Explicit skills | Model interpretation | Alias-normalized explicit matching |
| Reproducibility | Model output may vary between runs | Deterministic scoring and tie-breaking |

---

## Core Explainability Principle

> **Semantic similarity never overrides explicit skill evidence.**

JD requires **MongoDB**. The resume contains **PostgreSQL**:

- **MongoDB → missing required skill**
- PostgreSQL → may appear as *related semantic evidence*
- PostgreSQL does **not** become MongoDB

`matched_required` / `missing_required` are decided exclusively by the explicit matching engine over alias-normalized canonical skills. Semantic output is stored in a separate field and contributes only its own 35% weight — so paraphrase-level similarity can never quietly convert a missing named technology into a match.

---

## How It Works

At a glance:

```text
JD + Resume PDFs
  ↓ PDF extraction (PyMuPDF · reading-order blocks · page preservation · scan detection)
  ↓ JD / resume parsing (typed requirements · sections · evidence chunks with page + confidence)
  ↓ Normalization (conservative alias map · dedup · no blind merges)
  ↓ Explicit / keyword matching (exact + alias · RapidFuzz fallback · duplicate suppression)
  ↓ Semantic matching (all-MiniLM-L6-v2, local · cosine similarity · strongest evidence per requirement)
  ↓ Contextual lexical relevance (BM25 against JD vocabulary)
  ↓ Score fusion (fixed weights · all components bounded to [0, 1])
  ↓ Deterministic ranking (strict tie-breaking hierarchy)
  ↓ Evidence-backed explanation (templates over stored records)
  ↓ Pairwise comparison (score deltas + missing-skill diff between any two candidates)
```

Pipeline detail:

```text
                    ┌─────────────────────────────────────────────┐
                    │                INGESTION                    │
   JD PDF ──────────▶  PyMuPDF extraction · reading-order blocks  │
   Resume PDFs ─────▶  page preservation · scan/quality detection │
                    └──────────────────┬──────────────────────────┘
                                       ▼
                    ┌─────────────────────────────────────────────┐
                    │                 PARSING                     │
                    │  JD  → role, requirements (required /       │
                    │        preferred / responsibilities)        │
                    │  CV  → sections, skills, evidence chunks    │
                    │        (text + section + page + confidence) │
                    └──────────────────┬──────────────────────────┘
                                       ▼
                    ┌─────────────────────────────────────────────┐
                    │            NORMALIZATION                    │
                    │  conservative alias map (k8s → kubernetes,  │
                    │  ReactJS → react) · dedup · no blind merges │
                    │  (PostgreSQL ≠ MongoDB, Express ≠ Node.js)  │
                    └──────────────────┬──────────────────────────┘
                                       ▼
              ┌────────────────────────┴───────────────────────┐
              ▼                                                ▼
   ┌──────────────────────┐                      ┌──────────────────────────┐
   │  ENGINE A · KEYWORD  │                      │  ENGINE B · SEMANTIC     │
   │  exact + alias match │                      │  sentence-transformers   │
   │  RapidFuzz fallback  │                      │  (all-MiniLM-L6-v2, local)│
   │  BM25 lexical relev. │                      │  cosine similarity,      │
   │  duplicate suppressed│                      │  strongest-evidence-per- │
   │                      │                      │  requirement             │
   └──────────┬───────────┘                      └────────────┬─────────────┘
              └────────────────────────┬───────────────────────┘
                                       ▼
                    ┌─────────────────────────────────────────────┐
                    │        FUSION → RANKING → EXPLANATION       │
                    │  fixed-weight fusion · deterministic tie-   │
                    │  breaking · template-backed dossiers ·      │
                    │  pairwise comparison                        │
                    └─────────────────────────────────────────────┘
```

**Implementation notes supported by the code:** extraction preserves page numbers and reading-order text blocks (sorted by position within each page); resumes are segmented into sections with per-chunk confidence; skill aliases are normalized conservatively (Kubernetes for `k8s`, React for `ReactJS`) without blind merging of distinct technologies; every evidence chunk carries its source section, page, and confidence for later citation.

---

## The Score

```
Final Score =
    0.35 × Required Skill Coverage
  + 0.35 × Semantic Requirement Alignment
  + 0.20 × Contextual Lexical Relevance
  + 0.10 × Preferred Skill Coverage
```

- **Required Skill Coverage (35%)** — the fraction of the JD's required skills explicitly present in the resume, via exact match or an approved alias.
- **Semantic Requirement Alignment (35%)** — cosine similarity between each requirement and the candidate's strongest matching evidence, computed locally with sentence-transformers.
- **Contextual Lexical Relevance (20%)** — BM25 relevance of the resume's text against the JD vocabulary; it measures how well the surrounding context supports relevance, and is *not* simple keyword counting.
- **Preferred Skill Coverage (10%)** — the fraction of preferred (nice-to-have) skills explicitly present.

Guarantees:

- Every component is bounded to `[0, 1]`.
- The weights sum to exactly 1.0 and are validated when configuration loads.
- The frontend renders the backend's score components as-is — it does **not** compute scores or re-rank candidates.
- Where a UI label reads "Keyword" (e.g., the leaderboard column), that field is **Contextual Lexical Relevance**.

---

## Deterministic Ranking

For the same input documents, the ranking pipeline is deterministic. Ties break through a strict hierarchy:

```text
final_score → required coverage → semantic score → lexical score → preferred coverage → candidate_id
```

Verified end-to-end on the official dataset: two independent backend runs over the same files produce the same ranking.

---

## Tech stack

**Backend** — Python 3.10+, FastAPI, Pydantic v2, PyMuPDF, sentence-transformers (`all-MiniLM-L6-v2`, runs locally on CPU), scikit-learn, RapidFuzz, rank-bm25, pytest

**Frontend** — Next.js (App Router), React 19, TypeScript, Tailwind CSS 4

**Runtime posture** — in-memory evaluation store (no database), background task execution with status polling, zero external API calls at inference time

---

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- The first analysis run downloads the MiniLM embedding model (~90 MB) to the local HuggingFace cache

### Backend

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --port 8000
```

Verify: `curl http://localhost:8000/health` → `{"status": "ok"}`

> **Windows note:** install a CPU-only torch wheel first (`pip install torch --index-url https://download.pytorch.org/whl/cpu`) to avoid pulling multi-GB CUDA packages.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

`.env.local` defaults to the live backend:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_DATA_SOURCE=api
```

### Running an evaluation

1. A fresh backend always starts with **zero candidates** — no stale results
2. **Ingest Documents** → upload the JD and the resume batch (`data/official/`)
3. **Start Shortlisting Analysis** → progress streams through parsing → matching → ranking
4. Explore the leaderboard, open any dossier for evidence with page numbers, and use **Compare Pair** for head-to-head analysis

**Mock Mode** (header toggle) renders five synthetic candidates instantly — useful for UI demos without the backend. It is strictly separated: Live API Mode only ever displays backend results, and a backend failure shows an error banner instead of silently falling back to mock data.

---

## API reference

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/api/jobs/upload` | Upload + parse a JD PDF → structured requirements |
| GET | `/api/jobs/{job_id}` | Retrieve a parsed JD |
| POST | `/api/resumes/upload-batch` | Batch-upload resumes with per-file fault isolation |
| POST | `/api/evaluation/start` | Trigger the pipeline (background task) |
| GET | `/api/evaluation/status/{task_id}` | Poll stage / progress / failed files |
| GET | `/api/evaluation/rankings` | Full ranked dossiers with score breakdowns |
| GET | `/api/evaluation/compare` | Deterministic pairwise comparison (`candidate_a`, `candidate_b`) |
| GET | `/api/candidates/{candidate_id}` | Single candidate dossier |

A complete end-to-end verification script (uploads the official dataset, polls, validates the fusion formula per candidate, checks ranking order and pairwise deltas) lives at [`outputs/demo_sanity_check.py`](outputs/demo_sanity_check.py).

---

## Project structure

```text
nexora/
├── backend/
│   ├── app/                  # FastAPI routes, schemas, in-memory store
│   ├── config/               # Typed settings (weights, thresholds — validated)
│   ├── core/
│   │   ├── parsing/          # PDF extraction, JD/resume parsers, sections
│   │   ├── normalization/    # Skill alias canonicalization
│   │   ├── matching/         # Keyword + semantic engines, BM25
│   │   ├── ranking/          # Score fusion, deterministic ranker
│   │   ├── explanations/     # Template-backed, evidence-citing explainer
│   │   └── pipeline.py       # End-to-end orchestrator
│   ├── models/               # Pydantic domain models
│   └── tests/                # 170 tests (unit + integration)
├── frontend/
│   ├── src/app/              # Dashboard page
│   ├── src/components/       # Leaderboard, dossier, comparison, upload UI
│   ├── src/lib/api/          # Typed client, adapters, endpoint registry
│   ├── src/lib/mock/         # Mock Mode fixtures (isolated from Live)
│   └── tests/                # 7 contract/adapter tests
├── data/
│   ├── official/             # Official JD + 18 resume PDFs
│   └── stress_test_resumes/  # Robustness fixtures (not used for results)
└── outputs/                  # Verification scripts and run logs
```

---

## Design guarantees

1. **No LLM anywhere in the scoring path.** Embeddings are local sentence-transformers; every other stage is deterministic code.
2. **Explicit beats semantic.** `matched_required` / `missing_required` are decided exclusively by the explicit matching engine over alias-normalized canonical skills. Semantic output lands in a separate `semantic_matches` field and feeds only its own 35% weight.
3. **Explanations cannot invent facts.** The explainer is a template over stored evaluation records — skill names, coverage counts, and score deltas come from the record, not from generation.
4. **Failed files fail loudly.** Corrupt/empty/scanned PDFs are flagged per-file (e.g., `NEEDS_OCR`, failed list) and never silently become low-scoring candidates; one bad file never aborts the batch.
5. **Fresh start is actually fresh.** The backend boots with an empty store; candidates exist only after explicit ingestion and analysis. Restarting the backend clears all state.
6. **Everything is auditable.** Every score component, matched/missing skill, and evidence quote (with section and page number) is retrievable per candidate.

---

## Testing

```bash
# Backend (170 tests)
cd backend && python -m pytest tests/ -v

# Frontend (7 tests)
cd frontend && npm test && npm run build
```

Coverage highlights: PDF edge cases (empty, malformed, encrypted, scanned, multi-column reading order), parser contracts, alias normalization (including the PostgreSQL ≠ MongoDB invariant), score-fusion math, rank tie-breaking, and full HTTP integration of the official workflow.

---

## Acknowledgments

Built with FastAPI, PyMuPDF, sentence-transformers, Next.js, and Tailwind CSS for the InternLoom AI Hackathon.
