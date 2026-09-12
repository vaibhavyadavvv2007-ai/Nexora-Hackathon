# Nexora Smart Shortlisting Engine — FastAPI Integration Contract

This document defines the authoritative, frozen integration contract between the **Nexora Frontend** and the **FastAPI Backend / ML Pipeline**.

---

## Architecture Principles

1. **Contract-First & Type-Safe**: All schemas correspond 1:1 with frontend TypeScript domain models in [`frontend/src/types/index.ts`](file:///c:/Users/Pawan/Desktop/Nexora-Hackathon/frontend/src/types/index.ts).
2. **Deterministic Scoring**: The fused score follows:
   $$\text{Final Score} = 0.35 \cdot S_{\text{req}} + 0.30 \cdot S_{\text{sem}} + 0.25 \cdot S_{\text{lex}} + 0.10 \cdot S_{\text{pref}}$$
3. **No Hallucinated Signals**: All matches must link to concrete candidate evidence chunks with section attribution (`experience`, `skills`, `projects`, `education`, `certifications`, `summary`) and page numbers.
4. **Dual-Mode Decoupling**: The frontend can run in `mock` mode (fully offline with realistic fixtures) or `api` mode against FastAPI.

---

## Base Configuration

- **Default Base URL**: `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_BASE_URL`)
- **Default Timeout**: 15,000 ms (cancellable via standard `AbortController`)
- **Central Endpoint Config**: [`frontend/src/lib/api/config.ts`](file:///c:/Users/Pawan/Desktop/Nexora-Hackathon/frontend/src/lib/api/config.ts)

---

## Standard Error Schema (FastAPI)

All error responses from FastAPI should return the standard Pydantic error structure:

```json
// Detail string (HTTPException)
{
  "detail": "Descriptive error message"
}

// Or validation error array (422 Unprocessable Entity)
{
  "detail": [
    {
      "loc": ["body", "file"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 1. Job Description Upload & Parsing

Uploads a single Job Description document (PDF, DOCX, or TXT) or raw text. The backend parser extracts structured requirements, canonical skill names, weights, and criticality.

### Endpoint Specification
- **HTTP Method**: `POST`
- **Path**: `/api/jobs/upload`
- **Content-Type**: `multipart/form-data`

### Request
```http
POST /api/jobs/upload HTTP/1.1
Host: localhost:8000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="Senior_Frontend_Architect.pdf"
Content-Type: application/pdf

<binary data>
------WebKitFormBoundary--
```
*Optional fields*:
- `title` (`string`, form-data): Custom title override.
- `raw_text` (`string`, form-data): Alternative to binary file upload.

### Response (`200 OK` or `201 Created`)
```json
{
  "id": "jd-2026-09-001",
  "title": "Senior Frontend Architect",
  "source_file": "Senior_Frontend_Architect.pdf",
  "raw_text": "We are seeking a Senior Frontend Architect...",
  "requirements": [
    {
      "id": "req-001",
      "name": "React Framework",
      "type": "required",
      "canonical_name": "react",
      "weight": 1.0,
      "critical": true,
      "source_text": "3+ years production experience with modern React, hooks, and component architecture."
    },
    {
      "id": "req-002",
      "name": "TypeScript Production",
      "type": "required",
      "canonical_name": "typescript",
      "weight": 1.0,
      "critical": true,
      "source_text": "Deep proficiency in TypeScript 5+, strict mode, and enterprise type systems."
    },
    {
      "id": "req-003",
      "name": "Next.js App Router",
      "type": "preferred",
      "canonical_name": "nextjs",
      "weight": 0.8,
      "critical": false,
      "source_text": "Experience with Next.js App Router, SSR, and hybrid rendering architectures."
    }
  ],
  "required_skills": ["react", "typescript", "tailwindcss", "rest_api"],
  "preferred_skills": ["nextjs", "graphql", "zustand", "docker"],
  "responsibilities": [
    "Design and scale high-throughput web applications",
    "Lead architectural reviews and mentor senior engineers",
    "Establish frontend telemetry, CI/CD, and performance budgets"
  ]
}
```

### Error Responses
- `400 Bad Request`: Unsupported file format (e.g. `.exe`, `.bin`).
  ```json
  { "detail": "Unsupported file format. Allowed: .pdf, .docx, .txt" }
  ```
- `422 Unprocessable Entity`: File is empty or unreadable (corrupt PDF).
  ```json
  { "detail": "Failed to extract text from PDF. Document appears corrupt or password-protected." }
  ```
- `500 Internal Server Error`: Parser engine exception.

### Loading State (Frontend)
- **UI Trigger**: User drops file in `UploadPanel`.
- **Indicators**: Ingest drawer shows animated spinner, file upload progress bar (0% $\rightarrow$ 100%), input drag area is disabled to prevent duplicate submissions.
- **Client Handling**: Calling `uploadJobDescription(file, { signal })`.

### Failure State (Frontend)
- **UI Banner**: Red alert toast in drawer with error detail.
- **Action**: Retains file selection with a "Retry Upload" button; keeps previously loaded JD in memory.

---

## 2. Resume Batch Upload

Accepts multiple resume documents simultaneously (PDF, DOCX, TXT) for ingestion and staging.

### Endpoint Specification
- **HTTP Method**: `POST`
- **Path**: `/api/resumes/upload-batch`
- **Content-Type**: `multipart/form-data`

### Request
```http
POST /api/resumes/upload-batch HTTP/1.1
Host: localhost:8000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="job_id"

jd-2026-09-001
------WebKitFormBoundary
Content-Disposition: form-data; name="files"; filename="alex_rivera_resume.pdf"
Content-Type: application/pdf

<binary data>
------WebKitFormBoundary
Content-Disposition: form-data; name="files"; filename="marcus_vance_cv.pdf"
Content-Type: application/pdf

<binary data>
------WebKitFormBoundary--
```

### Response (`200 OK` or `207 Multi-Status`)
```json
{
  "uploaded": 5,
  "job_id": "jd-2026-09-001",
  "files": [
    "alex_rivera_resume.pdf",
    "marcus_vance_cv.pdf",
    "elena_rostova_resume.pdf",
    "priya_sharma_resume.pdf",
    "david_kim_resume.pdf"
  ],
  "failed": [
    {
      "filename": "corrupt_file.bin",
      "reason": "Unsupported file extension"
    }
  ]
}
```

### Error Responses
- `400 Bad Request`: No files provided in payload.
  ```json
  { "detail": "No resume files attached to batch upload request." }
  ```
- `413 Payload Too Large`: Batch exceeds size limit (>50MB total).
- `500 Internal Server Error`: Disk write or staging failure.

### Loading State (Frontend)
- **UI Trigger**: User adds batch files in `UploadPanel`.
- **Indicators**: Resume counter updates dynamically (`Uploading X / Y files...`), animated progress bar.
- **Client Handling**: Calling `uploadResumes(files, jobId, { signal })`.

### Failure State (Frontend)
- **UI Banner**: Yellow warning badge listing corrupt files that failed ingestion while acknowledging successfully uploaded files.
- **Action**: User can proceed with valid subset or upload replacement files.

---

## 3. Start Analysis Pipeline

Triggers the asynchronous evaluation pipeline (JD requirement chunking $\rightarrow$ Resume OCR/parsing $\rightarrow$ BM25 keyword matching $\rightarrow$ Embedding cosine scoring $\rightarrow$ Score fusion $\rightarrow$ Ranking).

### Endpoint Specification
- **HTTP Method**: `POST`
- **Path**: `/api/evaluation/start`
- **Content-Type**: `application/json` or `multipart/form-data`

### Request
```http
POST /api/evaluation/start HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "job_id": "jd-2026-09-001",
  "candidate_ids": ["CAND-001", "CAND-002", "CAND-003"]
}
```

### Response (`202 Accepted`)
```json
{
  "task_id": "task-eval-89240182",
  "status": "queued"
}
```

### Error Responses
- `400 Bad Request`: Missing `job_id`.
  ```json
  { "detail": "Field 'job_id' is required to trigger evaluation." }
  ```
- `404 Not Found`: `job_id` does not exist in backend database.
- `409 Conflict`: Analysis task is already actively running for this `job_id`.
  ```json
  { "detail": "Task task-eval-89240182 is already running for job jd-2026-09-001." }
  ```

### Loading State (Frontend)
- **UI Trigger**: Clicking "Run Candidate Shortlisting" button.
- **Indicators**: Processing overlay appears; `ProcessingBar` mounts at top with stage set to `uploading` / `parsing`.
- **Client Handling**: Calling `startAnalysis(jobId, files, { signal })`.

### Failure State (Frontend)
- **UI Banner**: Prominent error card above dashboard.
- **Action**: Resets pipeline state to `idle`, returns user to file staging view.

---

## 4. Pipeline Analysis Telemetry & Status Polling

Retrieves granular stage progress and subsystem telemetry for an active evaluation task.

### Endpoint Specification
- **HTTP Method**: `GET`
- **Path**: `/api/evaluation/status/{task_id}`

### Request
```http
GET /api/evaluation/status/task-eval-89240182 HTTP/1.1
Host: localhost:8000
```

### Response (`200 OK`)
```json
{
  "stage": "matching",
  "progress": 68,
  "message": "Computing dense vector similarity across 5 candidate dossiers...",
  "jd_processed": true,
  "resumes_processed": 5,
  "resumes_total": 5,
  "semantic_model_status": "encoding",
  "keyword_engine_status": "ready",
  "ranking_status": "idle",
  "failed_resumes": []
}
```

#### Valid `stage` Enum Values
- `"idle"`: No task running.
- `"uploading"`: Staging files on backend.
- `"parsing"`: Document OCR and section extraction.
- `"matching"`: Lexical (BM25) and Semantic (Embeddings) alignment.
- `"ranking"`: Score fusion and deterministic rank calculation.
- `"complete"`: All results computed and ready for retrieval.
- `"error"`: Pipeline encountered fatal error.

### Error Responses
- `404 Not Found`: Task ID not found or expired.
  ```json
  { "detail": "Evaluation task 'task-eval-89240182' not found." }
  ```
- `500 Internal Server Error`: Pipeline worker crash.

### Loading State (Frontend)
- **UI Trigger**: Active polling loop while `stage !== "complete" && stage !== "error"`.
- **Indicators**: `ProcessingBar` updates percentage (0–100%), pulsating blue indicator on the active stage pill.
- **Client Handling**: Polling via `getAnalysisStatus(taskId, undefined, { signal })` every 1,000 ms.

### Failure State (Frontend)
- **UI Banner**: `ProcessingBar` transitions to red border; displays failure message and aborts polling.
- **Action**: Offers "Retry Pipeline" button.

---

## 5. Ranked Candidates Leaderboard

Fetches the complete evaluation results for all processed candidates, ordered by `rank` (ascending) / `final_score` (descending).

### Endpoint Specification
- **HTTP Method**: `GET`
- **Path**: `/api/evaluation/rankings`
- **Query Parameters**:
  - `job_id` (`string`, optional): Filter results by Job ID.
  - `sort_by` (`string`, optional): Sorting metric (`rank`, `final_score`, `required_coverage`, `semantic_score`, `lexical_score`).
  - `min_score` (`float`, optional): Filter out candidates below threshold ($0.0 - 1.0$).

### Request
```http
GET /api/evaluation/rankings?job_id=jd-2026-09-001 HTTP/1.1
Host: localhost:8000
```

### Response (`200 OK`)
```json
{
  "job_description": {
    "id": "jd-2026-09-001",
    "title": "Senior Frontend Architect",
    "source_file": "Senior_Frontend_Architect.pdf",
    "requirements": [...],
    "required_skills": ["react", "typescript", "tailwindcss", "rest_api"],
    "preferred_skills": ["nextjs", "graphql", "zustand", "docker"],
    "responsibilities": [...]
  },
  "candidates": [
    {
      "candidate_id": "CAND-001",
      "name": "Alex Rivera",
      "rank": 1,
      "final_score": 0.87,
      "required_coverage": 0.875,
      "semantic_score": 0.82,
      "lexical_score": 0.91,
      "preferred_coverage": 0.60,
      "scores": {
        "required_skill_coverage": 0.875,
        "semantic_requirement_alignment": 0.82,
        "contextual_lexical_relevance": 0.91,
        "preferred_skill_coverage": 0.60,
        "final_score": 0.87
      },
      "matched_required": [...],
      "matched_preferred": [...],
      "missing_required": [...],
      "keyword_matches": [...],
      "semantic_matches": [...],
      "evidence": [...],
      "explanation": "Top overall match with exceptional lexical density and verified React architecture experience.",
      "parsing_status": "success",
      "parsing_warnings": []
    }
  ],
  "processing_time_ms": 1420,
  "model_version": "nexora-engine-v1.0"
}
```

*Note*: The frontend adapter automatically normalizes backend payloads whether scores are nested in `scores: ScoreStructure` or provided as top-level fields.

### Error Responses
- `404 Not Found`: No evaluation found for `job_id`.
- `425 Too Early`: Pipeline still executing.
  ```json
  { "detail": "Evaluation in progress. Current stage: 'matching'." }
  ```
- `500 Internal Server Error`: Result serialization failure.

### Loading State (Frontend)
- **UI Trigger**: Initial page mount or upon pipeline completion.
- **Indicators**: Leaderboard skeleton rows (pulse animation), disabled sort buttons.
- **Client Handling**: Calling `getRankings(jobId, { signal })`.

### Failure State (Frontend)
- **UI Banner**: "Unable to load candidate rankings" banner with link to fallback to Mock Data.
- **Action**: Retains previous results if available; prevents crashing the dashboard.

---

## 6. Individual Candidate Dossier & Evidence Detail

Retrieves granular evaluation details, verbatim resume citations, keyword match excerpts, and missing requirement gaps for a single applicant.

### Endpoint Specification
- **HTTP Method**: `GET`
- **Path**: `/api/candidates/{candidate_id}`
- **Query Parameters**:
  - `job_id` (`string`, optional): Target Job context.

### Request
```http
GET /api/candidates/CAND-001?job_id=jd-2026-09-001 HTTP/1.1
Host: localhost:8000
```

### Response (`200 OK`)
```json
{
  "candidate_id": "CAND-001",
  "name": "Alex Rivera",
  "candidate_name": "Alex Rivera",
  "rank": 1,
  "final_score": 0.87,
  "required_coverage": 0.875,
  "semantic_score": 0.82,
  "lexical_score": 0.91,
  "preferred_coverage": 0.60,
  "scores": {
    "required_skill_coverage": 0.875,
    "semantic_requirement_alignment": 0.82,
    "contextual_lexical_relevance": 0.91,
    "preferred_skill_coverage": 0.60,
    "final_score": 0.87
  },
  "matched_required": [
    {
      "id": "req-001",
      "name": "React Framework",
      "type": "required",
      "canonical_name": "react",
      "weight": 1.0,
      "critical": true,
      "source_text": "3+ years production experience with modern React..."
    }
  ],
  "matched_preferred": [
    {
      "id": "req-003",
      "name": "Next.js App Router",
      "type": "preferred",
      "canonical_name": "nextjs",
      "weight": 0.8,
      "critical": false,
      "source_text": "Experience with Next.js App Router..."
    }
  ],
  "missing_required": [
    {
      "id": "req-004",
      "name": "GraphQL Client Architecture",
      "type": "required",
      "canonical_name": "graphql",
      "weight": 0.7,
      "critical": false,
      "source_text": "Production experience with Apollo/Relay GraphQL schemas."
    }
  ],
  "keyword_matches": [
    {
      "requirement": { "id": "req-001", "name": "React Framework", "canonical_name": "react", "type": "required", "weight": 1.0, "critical": true, "source_text": "React" },
      "evidence": {
        "text": "Architected micro-frontend platform using React 18 and Next.js, serving 40k daily active users.",
        "section": "experience",
        "page": 1,
        "source_file": "alex_rivera_resume.pdf",
        "confidence": 0.97,
        "match_type": "exact",
        "similarity": null
      },
      "match_type": "exact",
      "confidence": 0.97,
      "similarity": null
    }
  ],
  "semantic_matches": [
    {
      "requirement": { "id": "req-002", "name": "State Management & Reactivity", "canonical_name": "state_management", "type": "required", "weight": 0.9, "critical": true, "source_text": "State management" },
      "evidence": {
        "text": "Created reactive event-driven client store managing synchronization across multiple browser tabs.",
        "section": "experience",
        "page": 2,
        "source_file": "alex_rivera_resume.pdf",
        "confidence": 0.88,
        "match_type": "semantic_related",
        "similarity": 0.84
      },
      "match_type": "semantic_related",
      "confidence": 0.88,
      "similarity": 0.84
    }
  ],
  "evidence": [
    {
      "text": "Architected micro-frontend platform using React 18 and Next.js...",
      "section": "experience",
      "page": 1,
      "source_file": "alex_rivera_resume.pdf",
      "confidence": 0.97,
      "match_type": "exact",
      "similarity": null
    }
  ],
  "explanation": "Rank #1: Demonstrates exhaustive production React expertise with 7 of 8 required skills explicitly evidenced in work history.",
  "parsing_status": "success",
  "parsing_warnings": []
}
```

### Error Responses
- `404 Not Found`: Candidate ID does not exist.
  ```json
  { "detail": "Candidate 'CAND-999' not found." }
  ```
- `500 Internal Server Error`.

### Loading State (Frontend)
- **UI Trigger**: Clicking candidate row in table or podium card in Top 3.
- **Indicators**: Detail dossier side-panel displays shimmer loaders across metric cards and evidence tabs.
- **Client Handling**: Calling `getCandidate(candidateId, jobId, { signal })`.

### Failure State (Frontend)
- **UI Banner**: "Unable to load dossier for candidate" message inside the dossier panel with a "Close" button. Table row remains selected.

---

## 7. Pairwise Contrastive Comparison

Generates a contrastive audit explaining exactly **why Candidate A ranked above Candidate B**, computing metric deltas, exclusive advantages, and evidence divergence.

### Endpoint Specification
- **HTTP Method**: `GET`
- **Path**: `/api/evaluation/compare`
- **Query Parameters**:
  - `candidate_a` (`string`, required): First candidate ID.
  - `candidate_b` (`string`, required): Second candidate ID.
  - `job_id` (`string`, optional): Target Job context.

### Request
```http
GET /api/evaluation/compare?candidate_a=CAND-001&candidate_b=CAND-002&job_id=jd-2026-09-001 HTTP/1.1
Host: localhost:8000
```

### Response (`200 OK`)
```json
{
  "candidate_a_id": "CAND-001",
  "candidate_b_id": "CAND-002",
  "winner_id": "CAND-001",
  "score_delta": 0.11,
  "required_skill_delta": 0.125,
  "semantic_delta": 0.08,
  "lexical_delta": 0.14,
  "explanation": "Alex Rivera ranked #1 (+11% delta) primarily due to superior required skill coverage (87.5% vs 75.0%) and higher contextual lexical relevance in production systems.",
  "advantages_a": [
    "Production React Architecture: Alex has verified enterprise experience (50k DAU) vs Marcus's agency projects",
    "Strict TypeScript Competency: 4 citations in Alex's experience section vs 1 in Marcus's skills list",
    "Lower Missing Critical Skills: Alex has 1 missing requirement vs Marcus's 2 missing requirements"
  ],
  "advantages_b": [
    "GraphQL Schema Design: Marcus evidenced production Apollo server design which Alex lacks",
    "Kubernetes & Docker Deployment: Marcus cited cloud container orchestration"
  ],
  "missing_skills_diff": {
    "only_a_missing": ["graphql"],
    "only_b_missing": ["typescript_strict", "nextjs_app_router"],
    "both_missing": ["web_workers"]
  },
  "key_evidence_diff": [
    {
      "text": "Architected micro-frontend platform using React 18 and Next.js (Alex Rivera, p.1)",
      "section": "experience",
      "page": 1,
      "source_file": "alex_rivera_resume.pdf",
      "confidence": 0.97,
      "match_type": "exact",
      "similarity": null
    }
  ]
}
```

### Error Responses
- `400 Bad Request`: Same candidate ID provided for both A and B, or missing parameters.
  ```json
  { "detail": "Parameters 'candidate_a' and 'candidate_b' must specify distinct candidate IDs." }
  ```
- `404 Not Found`: Either candidate A or candidate B is not in the evaluation index.
  ```json
  { "detail": "Candidate 'CAND-007' not found for comparison." }
  ```
- `500 Internal Server Error`.

### Loading State (Frontend)
- **UI Trigger**: Clicking "Compare" button on leaderboard or podium.
- **Indicators**: Comparison modal opens with pulsing placeholder cards for Candidate A, Candidate B, and the Delta Score indicator.
- **Client Handling**: Calling `compareCandidates(candA, candB, jobId, { signal })`.

### Failure State (Frontend)
- **UI Banner**: Modal displays "Comparison unavailable for selected candidates" notice while keeping candidate dropdown pickers active to select an alternate pair.

---

## 8. Summary Table of Frontend Operations

All 7 operations are accessible via [`frontend/src/services/api.ts`](file:///c:/Users/Pawan/Desktop/Nexora-Hackathon/frontend/src/services/api.ts):

| Operation | Service Function | Backend Route | Response Model |
|---|---|---|---|
| **1. JD Upload** | `uploadJobDescription(file, options?)` | `POST /api/jobs/upload` | `JobDescription` |
| **2. Resume Batch** | `uploadResumes(files, jobId?, options?)` | `POST /api/resumes/upload-batch` | `ResumeBatchUploadResponse` |
| **3. Start Analysis** | `startAnalysis(jobId, files?, options?)` | `POST /api/evaluation/start` | `StartAnalysisResponse` |
| **4. Analysis Status** | `getAnalysisStatus(taskId, stage?, options?)` | `GET /api/evaluation/status/{taskId}` | `ProcessingStatus` |
| **5. Ranked Candidates** | `getRankings(jobId?, options?)` | `GET /api/evaluation/rankings` | `EvaluationResult` |
| **6. Candidate Detail** | `getCandidate(candidateId, jobId?, options?)` | `GET /api/candidates/{candidateId}` | `CandidateEvaluation` |
| **7. Pairwise Compare** | `compareCandidates(candA, candB, jobId?, options?)` | `GET /api/evaluation/compare` | `PairwiseComparison` |
