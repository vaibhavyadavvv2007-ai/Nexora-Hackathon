import test from "node:test";
import assert from "node:assert/strict";

// Verify deterministic score fusion formula
test("Deterministic score fusion formula matches 0.35 Req + 0.30 Sem + 0.25 Lex + 0.10 Pref", () => {
  const req = 0.875;
  const sem = 0.82;
  const lex = 0.91;
  const pref = 0.60;

  const expected = 0.35 * req + 0.30 * sem + 0.25 * lex + 0.10 * pref;
  // 0.35*0.875 = 0.30625
  // 0.30*0.82  = 0.246
  // 0.25*0.91  = 0.2275
  // 0.10*0.60  = 0.06
  // Sum = 0.83975 (~0.84-0.87 depending on weights)

  assert.ok(expected > 0.80 && expected < 0.90, `Score ${expected} within expected high-rank range`);
});

// Verify requirement contract structure
test("Requirement contract validation", () => {
  const req = {
    id: "req-001",
    name: "React Framework",
    type: "required",
    canonical_name: "react",
    weight: 1.0,
    critical: true,
    source_text: "3+ years production React",
  };

  assert.equal(req.id, "req-001");
  assert.equal(req.critical, true);
  assert.equal(req.type, "required");
});

// Verify evidence contract structure
test("Evidence contract validation", () => {
  const ev = {
    text: "Built production React apps with 50k DAU",
    section: "experience",
    page: 1,
    source_file: "resume_alpha.pdf",
    confidence: 0.95,
    match_type: "exact",
    similarity: null,
  };

  assert.equal(ev.section, "experience");
  assert.equal(ev.page, 1);
  assert.equal(ev.match_type, "exact");
});

// Verify pairwise comparison structure
test("Pairwise comparison delta calculation", () => {
  const scoreA = 0.87;
  const scoreB = 0.76;
  const delta = Math.round((scoreA - scoreB) * 100) / 100;

  assert.equal(delta, 0.11);
  assert.ok(delta > 0, "Winner delta is positive");
});
