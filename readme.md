# Nexora — Smart Shortlisting Engine

**Explainable, dual-signal candidate shortlisting for technical hiring.**

Nexora ingests one Job Description PDF and a batch of 15–18 candidate resume PDFs, then produces a deterministic, evidence-backed ranking with per-candidate score breakdowns, matched/missing skills, page-level evidence quotes, and pairwise comparisons — **without ever asking an LLM to score a resume**.

> Built for the **InternLoom AI Hackathon**. The ranking engine relies on deterministic parsing, genuine keyword matching, locally-computed sentence embeddings, mathematical score fusion, and template-backed explanations. No LLM APIs, no cloud calls, no hallucinated evidence.

---

## Why Nexora is different

Most "AI resume screeners" hide a single LLM call behind a progress bar: unverifiable, non-deterministic, and unable to cite evidence. Nexora takes the opposite approach:

| | Typical LLM screener | Nexora |
|---|---|---|
| Scoring | One opaque LLM call | 4 deterministic signals, fused mathematically |
| Explanations | Generated prose (can hallucinate) | Templates filled from stored evaluation records |
| Evidence | None, or invented | Exact resume text with section + page number |
| Re-runs | Different scores every time | Bit-identical rankings across restarts |
| Skills | Whatever the model "thinks" | Explicit alias-normalized matching, verified in text |

**Core invariant:** if the JD requires *MongoDB* and the resume only says *PostgreSQL*, then MongoDB is reported as **missing**. Semantic similarity may surface the PostgreSQL experience as *related evidence* — it can never silently convert a missing named skill into a matched one.

---

## How it works

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
   │  exact + alias match │                      │  all-MiniLM-L6-v2 (local)│
   │  rapidfuzz fallback  │                      │  requirement ↔ evidence  │
   │  BM25 lexical relev. │                      │  cosine similarity,      │
   │  duplicate suppressed│                      │  strongest-evidence-per- │
   │                      │                      │  requirement, tiered     │
   └──────────┬───────────┘                      └────────────┬─────────────┘
              └────────────────────────┬───────────────────────┘
                                       ▼
                    ┌─────────────────────────────────────────────┐
                    │              SCORE FUSION                   │
                    │   Final = 0.35·Req + 0.35·Sem               │
                    │         + 0.20·Lex + 0.10·Pref              │
                    └──────────────────┬──────────────────────────┘
                                       ▼
                    ┌─────────────────────────────────────────────┐
                    │        RANKING + EXPLANATIONS               │
                    │  deterministic tie-breaking · template-     │
                    │  backed dossiers · pairwise comparison      │
                    └─────────────────────────────────────────────┘
```

### The score

Every candidate receives four component scores, each bounded to `[0, 1]`:

```
Final Score = 0.35 × Required Skill Coverage      (explicit named skills)
            + 0.35 × Semantic Requirement Alignment (local embeddings)
            + 0.20 × Contextual Lexical Relevance   (BM25 against JD vocabulary)
            + 0.10 × Preferred Skill Coverage       (explicit named skills)
```

Weights are validated to sum to 1.0 at config load. The frontend renders backend components as-is — it never recomputes or re-ranks.

### Ranking determinism

Ties are broken by a strict hierarchy: `final_score → required_coverage → semantic → lexical → preferred → candidate_id`. Two fresh backend runs over the same files produce identical rankings — verified end-to-end on the official dataset.

---

## Tech stack

**Backend** — Python 3.10+, FastAPI, Pydantic v2, PyMuPDF, sentence-transformers (`all-MiniLM-L6-v2`, runs locally on CPU), scikit-learn, rapidfuzz, rank-bm25, pytest

**Frontend** — Next.js (App Router), React 19, TypeScript, Tailwind CSS 4

**Runtime posture** — in-memory evaluation store (no database), background task execution with status polling, zero external API dependencies at inference time

---

## Getting started

### Prerequisites
- Python 3.10+
- Node.js 18+
- The first analysis run downloads the MiniLM embedding model (~90 MB) to the local HuggingFace cache

### 1. Backend

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --port 8000
```

Verify: `curl http://localhost:8000/health` → `{"status": "ok"}`

> **Windows note:** install a CPU-only torch wheel first (`pip install torch --index-url https://download.pytorch.org/whl/cpu`) to avoid pulling multi-GB CUDA packages.

### 2. Frontend

```bash
cd frontend
npm install
# .env.local already defaults to the live backend:
#   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
#   NEXT_PUBLIC_DATA_SOURCE=api
npm run dev
```

Open **http://localhost:3000**.

### 3. Run an evaluation

1. In the header, switch to **Live API Mode** (a fresh backend always starts with zero candidates — no stale results)
2. Click **Ingest Documents**
3. Upload the JD (`data/official/Sample_JD.pdf`) and the resume batch (`data/official/Resume_*.pdf`)
4. Click **Start Shortlisting Analysis** — progress streams through parsing → matching → ranking (~40 s, dominated by first-time model load)
5. Explore the leaderboard, open any dossier for evidence with page numbers, and use **Compare Pair** for head-to-head analysis

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

A complete end-to-end verification script (uploads the official dataset, polls, validates the fusion formula per candidate, checks determinism and pairwise deltas) lives at [`outputs/demo_sanity_check.py`](outputs/demo_sanity_check.py).

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
│   │   ├── ranking/          # Scorer fusion, deterministic ranker
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
2. **Explicit beats semantic.** `matched_required` / `missing_required` are decided exclusively by the keyword engine against alias-normalized canonical skills. Semantic output lands in a separate `semantic_matches` field and feeds only its own 35% weight.
3. **Explanations cannot invent facts.** The explainer is a template over stored evaluation records — skill names, coverage counts, and score deltas come from the record, not from generation.
4. **Failed files fail loudly.** Corrupt/empty/scanned PDFs are flagged per-file (`NEEDS_OCR`, failed list) and never silently become low-scoring candidates; one bad file never aborts the batch.
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
