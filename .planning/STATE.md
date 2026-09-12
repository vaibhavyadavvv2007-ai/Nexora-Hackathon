# Project State: Nexora — Smart Shortlisting Engine

## Current Status
- **Phase**: Phase 1 — Foundation, Data Contracts & Protocols (COMPLETED)
- **Active Milestone**: Milestone 1 (Hackathon MVP)
- **Test Results**: 21/21 tests passing (pytest)
- **Real Data Status**: Real JD PDF and 15–18 resume PDFs are pending delivery.
- **Next Phase**: Phase 2 — PDF Parsing & Text Normalization Pipeline (Paused, awaiting user signal)

---

## Architectural Decisions
1. **Dual Matching Signals**:
   - Keyword Engine: exact, aliases, phrase, rapidfuzz fuzzy, section-weighted, duplicate suppressed, BM25 lexical relevance.
   - Semantic Engine: local `all-MiniLM-L6-v2`, cosine similarity, top-evidence extraction, thresholding.
2. **Scoring Design**:
   - $S_{\text{final}} = 0.35 \times S_{\text{req}} + 0.35 \times S_{\text{semantic}} + 0.20 \times S_{\text{lexical}} + 0.10 \times S_{\text{pref}}$
   - Normalized to $[0, 1]$; weights configurable via `Settings`.
3. **Deterministic Explanations & Pairwise Comparison**:
   - Evidence-driven, template-backed, zero hallucination.
   - Explicit matched vs missing required skills policy: named skill presence is authoritative; semantic similarity does NOT convert missing into matched.
   - Pairwise comparison ("Why did Candidate X beat Candidate Y?") compares pre-computed evaluation records directly without LLM re-ranking.
4. **Strict Boundaries**:
   - No databases, no auth, no microservices, no multi-JD, no Ruflo, no imaginary resume fabrication.

---

## Artifact Index
- Project Overview: [.planning/PROJECT.md](file:///c:/Users/yadav/OneDrive/Desktop/nexora/.planning/PROJECT.md)
- Requirements: [.planning/REQUIREMENTS.md](file:///c:/Users/yadav/OneDrive/Desktop/nexora/.planning/REQUIREMENTS.md)
- Roadmap: [.planning/ROADMAP.md](file:///c:/Users/yadav/OneDrive/Desktop/nexora/.planning/ROADMAP.md)
- Workflow Config: [.planning/config.json](file:///c:/Users/yadav/OneDrive/Desktop/nexora/.planning/config.json)

