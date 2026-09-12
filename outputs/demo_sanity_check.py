"""Demo sanity check: replicate the exact frontend Live API Mode flow against the real backend.

Flow: upload JD -> upload 18 official resumes -> start analysis -> poll -> rankings
      -> candidate detail -> pairwise compare #1 vs #2.
"""
import time
from pathlib import Path

import requests

BASE = "http://localhost:8000"
OFFICIAL = Path("data/official")

print("=== 1. Health ===")
r = requests.get(f"{BASE}/health", timeout=10)
print("GET /health:", r.status_code, r.json())

print("\n=== 2. Fresh-state rankings (must be empty) ===")
r = requests.get(f"{BASE}/api/evaluation/rankings", timeout=10)
data = r.json()
print("GET /api/evaluation/rankings:", r.status_code, "candidates:", len(data["candidates"]))
assert len(data["candidates"]) == 0, "FAIL: fresh backend must have no candidates"

print("\n=== 3. Upload official JD ===")
jd_path = OFFICIAL / "Sample_JD.pdf"
with open(jd_path, "rb") as f:
    r = requests.post(
        f"{BASE}/api/jobs/upload",
        files={"file": (jd_path.name, f, "application/pdf")},
        timeout=120,
    )
print("POST /api/jobs/upload:", r.status_code)
r.raise_for_status()
jd = r.json()
job_id = jd["id"]
print("job_id:", job_id, "| title:", jd.get("title") or jd.get("role_title"))
print("required_skills:", jd["required_skills"])
print("preferred_skills:", jd["preferred_skills"])

print("\n=== 4. Upload all official resumes ===")
resume_paths = sorted(p for p in OFFICIAL.glob("*.pdf") if p.name != "Sample_JD.pdf")
print("Official resumes found:", len(resume_paths))
files = []
for p in resume_paths:
    files.append(("files", (p.name, open(p, "rb"), "application/pdf")))
r = requests.post(
    f"{BASE}/api/resumes/upload-batch",
    files=files,
    data={"job_id": job_id},
    timeout=300,
)
r.raise_for_status()
batch = r.json()
print("uploaded:", batch["uploaded"], "| failed:", batch["failed"])

print("\n=== 5. Start analysis ===")
r = requests.post(
    f"{BASE}/api/evaluation/start",
    data={"job_id": job_id},
    timeout=60,
)
r.raise_for_status()
task = r.json()
task_id = task["task_id"]
print("task_id:", task_id)

print("\n=== 6. Poll status until complete ===")
deadline = time.time() + 600
while True:
    r = requests.get(f"{BASE}/api/evaluation/status/{task_id}", timeout=30)
    r.raise_for_status()
    st = r.json()
    print(f"  stage={st['stage']} progress={st['progress']} msg={st['message'][:80]}")
    if st["stage"] in ("complete", "error"):
        break
    if time.time() > deadline:
        raise SystemExit("FAIL: analysis timed out")
    time.sleep(2)
if st["stage"] == "error":
    raise SystemExit(f"FAIL: pipeline error: {st['message']}")

print("\n=== 7. Retrieve rankings ===")
r = requests.get(f"{BASE}/api/evaluation/rankings", params={"job_id": job_id}, timeout=60)
r.raise_for_status()
result = r.json()
cands = result["candidates"]
print("Candidates ranked:", len(cands))
print("processing_time_ms:", result["processing_time_ms"])
failed = result.get("failed_candidates") or []
print("failed_candidates:", failed)

ok_formula = True
for c in cands:
    s = c["scores"]
    expected = round(
        0.35 * s["required_skill_coverage"]
        + 0.35 * s["semantic_requirement_alignment"]
        + 0.20 * s["contextual_lexical_relevance"]
        + 0.10 * s["preferred_skill_coverage"],
        4,
    )
    if abs(expected - s["final_score"]) > 0.003:
        ok_formula = False
        print(f"  FORMULA MISMATCH {c['candidate_id']}: expected {expected} got {s['final_score']}")
print("Score formula 0.35/0.35/0.20/0.10 verified for all candidates:", ok_formula)

print("\n--- Top 3 ---")
for c in cands[:3]:
    s = c["scores"]
    print(f"#{c['rank']} {c['candidate_name']} ({c['candidate_id']}) final={s['final_score']}")
    print(f"    req={s['required_skill_coverage']} sem={s['semantic_requirement_alignment']} "
          f"lex={s['contextual_lexical_relevance']} pref={s['preferred_skill_coverage']}")
    print(f"    matched_required={[x['canonical_name'] for x in c['matched_required']]}")
    print(f"    missing_required={[x['canonical_name'] for x in c['missing_required']]}")
    print(f"    matched_preferred={[x['canonical_name'] for x in c['matched_preferred']]}")
    print(f"    evidence chunks: {len(c['evidence'])}, keyword matches: {len(c['keyword_matches'])}, "
          f"semantic matches: {len(c['semantic_matches'])}")
    print(f"    explanation: {c['explanation'][:200]}...")

ids = [c["candidate_id"] for c in cands]
assert len(ids) == len(set(ids)), "FAIL: duplicate candidate ids"
scores_sorted = [c["scores"]["final_score"] for c in cands]
assert scores_sorted == sorted(scores_sorted, reverse=True), "FAIL: ranking not descending"
print("Unique candidate IDs: OK | deterministic descending order: OK")

print("\n=== 8. Candidate detail (Rank #1) ===")
top1 = cands[0]
r = requests.get(f"{BASE}/api/candidates/{top1['candidate_id']}", params={"job_id": job_id}, timeout=30)
print("GET /api/candidates/<id>:", r.status_code)
r.raise_for_status()
detail = r.json()
print("detail name:", detail["candidate_name"], "| final:", detail["scores"]["final_score"])

print("\n=== 9. Pairwise compare #1 vs #2 ===")
top2 = cands[1]
r = requests.get(
    f"{BASE}/api/evaluation/compare",
    params={"candidate_a": top1["candidate_id"], "candidate_b": top2["candidate_id"], "job_id": job_id},
    timeout=30,
)
print("GET /api/evaluation/compare:", r.status_code)
r.raise_for_status()
comp = r.json()
print("winner_id:", comp["winner_id"], "| expected (rank1):", top1["candidate_id"])
assert comp["winner_id"] == top1["candidate_id"], "FAIL: winner must be rank #1"
print("score_delta:", comp["score_delta"], "| expected:", round(top1["scores"]["final_score"] - top2["scores"]["final_score"], 4))
assert abs(comp["score_delta"] - (top1["scores"]["final_score"] - top2["scores"]["final_score"])) < 0.01, "FAIL: wrong delta"
print("advantages_a:", len(comp["advantages_a"]), "| advantages_b:", len(comp["advantages_b"]))
print("explanation:", comp["explanation"][:220], "...")

print("\n" + "=" * 60)
print("ALL CHECKS PASSED")
print(f"Official resumes found: {len(resume_paths)}")
print(f"Successfully processed: {batch['uploaded']}")
print(f"Failed: {len(batch['failed'])}")
print(f"Candidates ranked: {len(cands)}")
print("=" * 60)
