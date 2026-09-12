# Roadmap: Nexora — Smart Shortlisting Engine

## Milestone 1: Hackathon MVP

- [ ] **Phase 1: Project Foundation, Data Contracts & Interfaces**
  - Establish dependency management (`requirements.txt`, `pyproject.toml`).
  - Implement Pydantic data schemas: `JobDescription`, `CandidateResume`, `EvidenceChunk`, `ScoreBreakdown`, `EvaluationRecord`, `PairwiseComparison`.
  - Define abstract base protocols for Parsers, Keyword Engine, Semantic Engine, Scorer, and Explainer.
  - Implement configuration management (`config.py`).
  - Create synthetic inline fixtures and unit tests for models and interfaces.

- [ ] **Phase 2: PDF Parsing & Normalization Pipeline**
  - Implement PyMuPDF-based text extractor for JD and Resumes.
  - Build resume section segmenter (Experience, Skills, Education, Projects).
  - Implement evidence chunker (sentence/bullet extraction with section tags).
  - Build canonical skill normalization dictionary and alias resolver.
  - Test parsing with synthetic in-memory PDF/text fixtures.

- [ ] **Phase 3: Dual Matching Engines**
  - **Engine A (Keyword)**: Exact matches, alias expansions, rapidfuzz fuzzy matching, section-weighted evidence, duplicate suppression.
  - **Engine B (Semantic)**: Sentence-transformers (`all-MiniLM-L6-v2`) embeddings, scikit-learn cosine similarity, best-evidence extraction, classification (Exact/Related/Inferred).
  - Build unit tests verifying both engines operate independently and contribute distinct scores.

- [ ] **Phase 4: Score Fusion & Deterministic Ranking**
  - Implement fusion scoring formula:
    $$\text{Final Score} = 0.35 \times S_{\text{req}} + 0.35 \times S_{\text{semantic}} + 0.20 \times S_{\text{lexical}} + 0.10 \times S_{\text{pref}}$$
  - Implement deterministic sorting with explicit tie-breaker rules.
  - Construct comprehensive `EvaluationRecord` capturing all intermediate signals, component scores, and evidence pointers.

- [ ] **Phase 5: Explanation Engine & Pairwise Differential**
  - Build template-backed explanation generator for Top 3 candidates (strictly factual, evidence-based).
  - Implement explicit matched vs missing required skills reporting.
  - Implement pairwise comparator: *"Why did Candidate X rank above Candidate Y?"* evaluating recorded metrics side-by-side without LLM recalculation.
  - Unit test explanation consistency and lack of hallucination.

- [ ] **Phase 6: Real Data Calibration & Batch Pipeline** *(Awaiting real PDFs)*
  - Batch runner script processing 1 JD PDF + 15–18 Resume PDFs from `data/`.
  - Output exporter generating structured JSON and Markdown audit logs in `outputs/`.
  - Error inspection and threshold calibration against actual documents.

- [ ] **Phase 7: Interactive Streamlit Dashboard**
  - Candidate ranking leaderboard with visual badges and score breakdown.
  - Candidate detail view: matched skills, missing required skills, and supporting evidence quotes.
  - Interactive pairwise comparison tool ("Compare Candidate X vs Y").
