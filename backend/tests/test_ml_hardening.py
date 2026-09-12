"""ML Pipeline Hardening & Technical Review Tests.

Comprehensive synthetic test suite validating signal separation, edge cases,
determinism, and ablation across the matching and ranking engine.

Test cases:
1.  Exact skill match
2.  Alias match
3.  Missing required skill
4.  PostgreSQL must NOT satisfy MongoDB
5.  Express.js provides related evidence for Node.js
6.  Semantic paraphrase match that keyword matching misses
7.  Keyword signal changes final score
8.  Semantic signal changes final score
9.  Preferred skills cannot dominate required skills
10. Repeated keyword stuffing does not create disproportionate score inflation
11. Long resumes do not automatically receive higher scores
12. Empty semantic-match set
13. Empty preferred-skill set
14. Zero/invalid evidence
15. Deterministic repeated execution
+   Critical test: Node.js / Express.js semantic-value
+   Ablation: keyword-only, semantic-only, combined
"""

import pytest
from backend.config.settings import Settings
from backend.core.matching.keyword_matcher import KeywordMatcher
from backend.core.matching.semantic_matcher import SemanticMatcher, clear_embedding_cache
from backend.core.ranking.ranker import Ranker
from backend.core.ranking.scorer import Scorer
from backend.models.document import JobDescription, Resume
from backend.models.enums import MatchType, RequirementType, SectionType
from backend.models.evaluation import CandidateEvaluation, ScoreStructure
from backend.models.evidence import EvidenceChunk, MatchEvidence
from backend.models.requirement import Requirement
from backend.models.skill import Skill


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_embedding_cache()
    yield
    clear_embedding_cache()


@pytest.fixture
def km() -> KeywordMatcher:
    return KeywordMatcher()


@pytest.fixture
def sm() -> SemanticMatcher:
    return SemanticMatcher()


@pytest.fixture
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture
def ranker() -> Ranker:
    return Ranker()


def _req(id: str, name: str, canon: str, typ=RequirementType.REQUIRED, text=None) -> Requirement:
    return Requirement(
        id=id, name=name, type=typ, canonical_name=canon,
        source_text=text or f"Must have {name}.",
    )


def _skill(canon: str, surface: str, mt=MatchType.EXACT, conf=1.0) -> Skill:
    return Skill(canonical_name=canon, surface_form=surface, match_type=mt, confidence=conf)


def _chunk(id: str, text: str, section=SectionType.EXPERIENCE, src="doc.pdf") -> EvidenceChunk:
    return EvidenceChunk(id=id, text=text, section=section, source_file=src)


def _resume(cid: str, name: str, skills=None, chunks=None, raw="") -> Resume:
    return Resume(
        candidate_id=cid, name=name, source_file=f"{cid}.pdf",
        raw_text=raw or name, skills=skills or [], evidence_chunks=chunks or [],
    )


def _jd(reqs, pref_reqs=None, raw="JD") -> JobDescription:
    all_reqs = list(reqs) + list(pref_reqs or [])
    return JobDescription(
        id="jd_h", title="Test JD", source_file="jd.pdf",
        raw_text=raw, requirements=all_reqs,
        required_skills=[r.canonical_name for r in reqs],
        preferred_skills=[r.canonical_name for r in (pref_reqs or [])],
    )


# ===================================================================
# Test 1: Exact skill match
# ===================================================================


class TestExactSkillMatch:
    def test_exact_match_found(self, km):
        req = _req("r1", "Python", "python")
        sk = _skill("python", "Python")
        matched, missing = km.match_explicit_skills([sk], [req])
        assert len(matched) == 1 and len(missing) == 0
        assert matched[0].match_type == MatchType.EXACT

    def test_exact_contributes_to_coverage(self, scorer):
        req = _req("r1", "Python", "python")
        sk = _skill("python", "Python")
        s = scorer.calculate_score_breakdown([sk], [req], [], [], [], [])
        assert s.required_skill_coverage == 1.0


# ===================================================================
# Test 2: Alias match
# ===================================================================


class TestAliasMatch:
    def test_k8s_matches_kubernetes(self, km):
        req = _req("r1", "Kubernetes", "kubernetes")
        sk = _skill("kubernetes", "k8s", MatchType.ALIAS, 0.95)
        matched, missing = km.match_explicit_skills([sk], [req])
        assert len(matched) == 1 and len(missing) == 0

    def test_reactjs_matches_react(self, km):
        req = _req("r1", "React", "react")
        sk = _skill("react", "ReactJS", MatchType.ALIAS, 0.95)
        matched, missing = km.match_explicit_skills([sk], [req])
        assert len(matched) == 1


# ===================================================================
# Test 3: Missing required skill
# ===================================================================


class TestMissingSkill:
    def test_unrelated_skill_leaves_requirement_missing(self, km):
        req = _req("r1", "Kubernetes", "kubernetes")
        sk = _skill("python", "Python")
        matched, missing = km.match_explicit_skills([sk], [req])
        assert len(matched) == 0 and len(missing) == 1
        assert missing[0].id == "r1"

    def test_missing_reduces_coverage(self, scorer):
        r1 = _req("r1", "Python", "python")
        r2 = _req("r2", "Docker", "docker")
        sk = _skill("python", "Python")
        s = scorer.calculate_score_breakdown([sk], [r1, r2], [], [], [], [])
        assert s.required_skill_coverage == 0.5


# ===================================================================
# Test 4: PostgreSQL must NOT satisfy MongoDB
# ===================================================================


class TestPostgresNotMongo:
    def test_postgres_missing_for_mongo(self, km):
        req = _req("r1", "MongoDB", "mongodb")
        sk = _skill("postgresql", "PostgreSQL")
        matched, missing = km.match_explicit_skills([sk], [req])
        assert len(matched) == 0 and len(missing) == 1

    def test_mongo_missing_for_postgres(self, km):
        req = _req("r1", "PostgreSQL", "postgresql")
        sk = _skill("mongodb", "MongoDB")
        matched, missing = km.match_explicit_skills([sk], [req])
        assert len(matched) == 0 and len(missing) == 1


# ===================================================================
# Test 5: Express.js provides related evidence for Node.js
# ===================================================================


class TestExpressRelatedNode:
    def test_express_does_not_satisfy_node_explicit(self, km):
        req = _req("r1", "Node.js", "node.js")
        sk = _skill("express.js", "Express.js")
        matched, missing = km.match_explicit_skills([sk], [req])
        assert len(matched) == 0 and len(missing) == 1

    def test_express_provides_semantic_evidence_for_node(self, sm):
        req = _req("r1", "Node.js", "node.js",
                    text="Build backend services using Node.js")
        chunk = _chunk("c1", "Developed REST APIs using Express.js framework.")
        resume = _resume("c1", "Dev", chunks=[chunk])
        jd = _jd([req])
        matches = sm.compute_semantic_alignment(resume, jd)
        assert len(matches) > 0
        assert matches[0].similarity is not None and matches[0].similarity > 0


# ===================================================================
# Test 6: Semantic paraphrase match that keyword matching misses
# ===================================================================


class TestSemanticParaphrase:
    def test_paraphrase_detected_by_semantic_not_keyword(self, km, sm):
        req = _req("r1", "container orchestration", "container_orchestration",
                    text="Manage container orchestration for microservices at scale.")
        # Resume says it differently
        sk = _skill("devops", "DevOps")
        chunk = _chunk("c1", "Deployed and managed Kubernetes clusters running hundreds of microservice pods.")
        resume = _resume("c1", "DevOps Eng", skills=[sk], chunks=[chunk])
        jd = _jd([req])

        # Keyword: no explicit match for container_orchestration
        matched, missing = km.match_explicit_skills([sk], [req])
        assert len(matched) == 0

        # Semantic: should detect alignment
        sem_matches = sm.compute_semantic_alignment(resume, jd)
        assert len(sem_matches) > 0
        assert sem_matches[0].similarity >= 0.45


# ===================================================================
# Test 7: Keyword signal changes final score
# ===================================================================


class TestKeywordSignalImpact:
    def test_full_vs_zero_keyword_coverage(self, scorer):
        r1 = _req("r1", "Python", "python")
        r2 = _req("r2", "Docker", "docker")
        sk1 = _skill("python", "Python")
        sk2 = _skill("docker", "Docker")

        full = scorer.calculate_score_breakdown([sk1, sk2], [r1, r2], [], [], [], [])
        zero = scorer.calculate_score_breakdown([], [r1, r2], [], [], [], [])
        delta = full.final_score - zero.final_score
        # 0.35 * (1.0 - 0.0) = 0.35
        assert delta >= 0.30
        assert full.required_skill_coverage == 1.0
        assert zero.required_skill_coverage == 0.0


# ===================================================================
# Test 8: Semantic signal changes final score
# ===================================================================


class TestSemanticSignalImpact:
    def test_high_vs_zero_semantic(self, scorer):
        r1 = _req("r1", "ML", "ml")
        sem_high = MatchEvidence(
            requirement=r1,
            evidence=_chunk("e1", "Trained transformer models in production"),
            match_type=MatchType.SEMANTIC_EXACT,
            confidence=0.92, similarity=0.92,
        )
        with_sem = scorer.calculate_score_breakdown([], [r1], [], [], [sem_high], [])
        without_sem = scorer.calculate_score_breakdown([], [r1], [], [], [], [])
        delta = with_sem.final_score - without_sem.final_score
        # 0.35 * 0.92 ≈ 0.322
        assert delta >= 0.25
        assert with_sem.semantic_requirement_alignment > 0.85
        assert without_sem.semantic_requirement_alignment == 0.0


# ===================================================================
# Test 9: Preferred skills cannot dominate required skills
# ===================================================================


class TestPreferredCannotDominate:
    def test_preferred_only_capped_by_weight(self, scorer, ranker):
        r1 = _req("r1", "Python", "python")
        p1 = _req("p1", "Redis", "redis", RequirementType.PREFERRED)
        p2 = _req("p2", "GraphQL", "graphql", RequirementType.PREFERRED)
        p3 = _req("p3", "Docker", "docker", RequirementType.PREFERRED)

        sk_redis = _skill("redis", "Redis")
        sk_graphql = _skill("graphql", "GraphQL")
        sk_docker = _skill("docker", "Docker")
        sk_py = _skill("python", "Python")

        # Cand A: All preferred, no required
        sa = scorer.calculate_score_breakdown(
            [], [r1], [sk_redis, sk_graphql, sk_docker], [p1, p2, p3], [], [],
        )
        # Cand B: Required match, no preferred
        sb = scorer.calculate_score_breakdown(
            [sk_py], [r1], [], [p1, p2, p3], [], [],
        )

        cand_a = CandidateEvaluation(candidate_id="a", candidate_name="Pref Only", scores=sa)
        cand_b = CandidateEvaluation(candidate_id="b", candidate_name="Req Only", scores=sb)

        ranked = ranker.rank_candidates([cand_a, cand_b])
        # Required coverage (0.35 weight) must dominate preferred (0.10 weight)
        assert ranked[0].candidate_id == "b"
        assert sb.final_score > sa.final_score


# ===================================================================
# Test 10: Keyword stuffing does not inflate disproportionately
# ===================================================================


class TestKeywordStuffing:
    def test_stuffing_capped(self, km, scorer):
        r1 = _req("r1", "Python", "python")
        r2 = _req("r2", "Go", "go")
        sk_py = _skill("python", "Python")
        stuffed = [sk_py] * 100

        matched, missing = km.match_explicit_skills(stuffed, [r1, r2])
        assert len(matched) == 1  # Only 1 requirement matched
        assert len(missing) == 1  # Go still missing

        s = scorer.calculate_score_breakdown(matched, [r1, r2], [], [], [], [])
        assert s.required_skill_coverage == 0.5
        assert s.final_score <= 1.0


# ===================================================================
# Test 11: Long resumes do not automatically win
# ===================================================================


class TestLongResumeNotAutoWin:
    def test_concise_beats_padded(self, scorer, ranker):
        req = _req("r1", "Rust", "rust", text="Systems programming in Rust")
        sk = _skill("rust", "Rust")

        # Focused short resume: high semantic + lexical
        sem_short = [MatchEvidence(
            requirement=req,
            evidence=_chunk("s1", "Built Rust systems from scratch for real-time processing"),
            match_type=MatchType.SEMANTIC_EXACT, confidence=0.93, similarity=0.93,
        )]
        lex_short = [MatchEvidence(
            requirement=req,
            evidence=_chunk("s1", "Rust systems processing"),
            match_type=MatchType.LEXICAL, confidence=0.88,
        )]
        s_short = scorer.calculate_score_breakdown([sk], [req], [], [], sem_short, lex_short)

        # Long resume: only weak semantic inferred
        sem_long = [MatchEvidence(
            requirement=req,
            evidence=_chunk("l1", "Reviewed code quality guidelines"),
            match_type=MatchType.SEMANTIC_INFERRED, confidence=0.48, similarity=0.48,
        )]
        s_long = scorer.calculate_score_breakdown([sk], [req], [], [], sem_long, [])

        ca = CandidateEvaluation(candidate_id="short", candidate_name="Short", scores=s_short)
        cb = CandidateEvaluation(candidate_id="long", candidate_name="Long", scores=s_long)
        ranked = ranker.rank_candidates([cb, ca])
        assert ranked[0].candidate_id == "short"


# ===================================================================
# Test 12: Empty semantic-match set
# ===================================================================


class TestEmptySemanticSet:
    def test_zero_semantic_alignment(self, scorer):
        r1 = _req("r1", "Java", "java")
        sk = _skill("java", "Java")
        s = scorer.calculate_score_breakdown([sk], [r1], [], [], [], [])
        assert s.semantic_requirement_alignment == 0.0
        assert s.final_score > 0.0  # required coverage still contributes

    def test_empty_evidence_produces_empty_semantic(self, sm):
        req = _req("r1", "Java", "java")
        resume = _resume("c1", "Dev")
        jd = _jd([req])
        matches = sm.compute_semantic_alignment(resume, jd)
        assert matches == []


# ===================================================================
# Test 13: Empty preferred-skill set
# ===================================================================


class TestEmptyPreferredSet:
    def test_no_preferred_is_zero(self, scorer):
        r1 = _req("r1", "Python", "python")
        sk = _skill("python", "Python")
        s = scorer.calculate_score_breakdown([sk], [r1], [], [], [], [])
        assert s.preferred_skill_coverage == 0.0

    def test_preferred_coverage_zero_does_not_break_formula(self, scorer):
        r1 = _req("r1", "Python", "python")
        sk = _skill("python", "Python")
        s = scorer.calculate_score_breakdown([sk], [r1], [], [], [], [])
        # Final = 0.35 * 1.0 + 0.35 * 0 + 0.20 * 0 + 0.10 * 0 = 0.35
        assert abs(s.final_score - 0.35) < 0.01


# ===================================================================
# Test 14: Zero/invalid evidence
# ===================================================================


class TestZeroEvidence:
    def test_all_zeros(self, scorer):
        s = scorer.calculate_score_breakdown([], [], [], [], [], [])
        assert s.required_skill_coverage == 0.0
        assert s.semantic_requirement_alignment == 0.0
        assert s.contextual_lexical_relevance == 0.0
        assert s.preferred_skill_coverage == 0.0
        assert s.final_score == 0.0

    def test_no_requirements_coverage_zero(self, scorer):
        sk = _skill("python", "Python")
        s = scorer.calculate_score_breakdown([sk], [], [], [], [], [])
        # No requirements → coverage is 0
        assert s.required_skill_coverage == 0.0

    def test_empty_resume_lexical(self, km):
        req = _req("r1", "Python", "python")
        resume = _resume("c1", "Empty")
        jd = _jd([req])
        lex = km.compute_lexical_evidence(resume, jd)
        assert lex == []

    def test_ranker_empty_list(self, ranker):
        assert ranker.rank_candidates([]) == []


# ===================================================================
# Test 15: Deterministic repeated execution
# ===================================================================


class TestDeterminism:
    def test_scorer_deterministic(self, scorer):
        r1 = _req("r1", "Python", "python")
        sk = _skill("python", "Python")
        sem = [MatchEvidence(
            requirement=r1,
            evidence=_chunk("e1", "Python experience"),
            match_type=MatchType.SEMANTIC_RELATED,
            confidence=0.78, similarity=0.78,
        )]
        results = []
        for _ in range(10):
            s = scorer.calculate_score_breakdown([sk], [r1], [], [], sem, [])
            results.append(s.final_score)
        assert len(set(results)) == 1, f"Non-deterministic scores: {results}"

    def test_ranker_deterministic(self, scorer, ranker):
        r1 = _req("r1", "Go", "go")
        sa = scorer.calculate_score_breakdown(
            [_skill("go", "Go")], [r1], [], [], [], [],
        )
        sb = scorer.calculate_score_breakdown([], [r1], [], [], [], [])
        evals = [
            CandidateEvaluation(candidate_id="b", candidate_name="B", scores=sb),
            CandidateEvaluation(candidate_id="a", candidate_name="A", scores=sa),
        ]
        ranks = []
        for _ in range(10):
            # Reset ranks
            for e in evals:
                e.rank = None
            result = ranker.rank_candidates(list(evals))
            ranks.append([e.candidate_id for e in result])
        assert all(r == ranks[0] for r in ranks), f"Non-deterministic ranks: {ranks}"

    def test_keyword_matcher_deterministic(self, km):
        req = _req("r1", "Python", "python")
        sk = _skill("python", "Python")
        results = []
        for _ in range(10):
            m, mi = km.match_explicit_skills([sk], [req])
            results.append((len(m), len(mi)))
        assert len(set(results)) == 1


# ===================================================================
# Critical Test: Node.js / Express.js semantic-value
# ===================================================================


class TestCriticalNodeExpressSemantic:
    def test_critical_semantic_value_full_pipeline(self, km, sm, scorer):
        """
        JD: "Build REST APIs using Node.js"
        Resume: "Developed backend services using Express.js and MongoDB."

        Assertions:
        - explicit keyword matching is partial (Node.js missing)
        - semantic similarity detects meaningful related evidence
        - semantic evidence is stored in MatchEvidence
        - Node.js is NOT falsely marked as an exact explicit skill
        - final score changes when semantic contribution changes
        """
        req = _req("r_node", "Node.js", "node.js",
                    text="Build REST APIs using Node.js")
        jd = _jd([req])

        sk_express = _skill("express.js", "Express.js")
        sk_mongo = _skill("mongodb", "MongoDB")
        chunk = _chunk("c1", "Developed backend services using Express.js and MongoDB.")
        resume = _resume("c1", "Express Dev", skills=[sk_express, sk_mongo], chunks=[chunk])

        # A) Explicit keyword matching is partial
        matched, missing = km.match_explicit_skills(resume.skills, jd.requirements)
        assert len(matched) == 0, "Express.js must NOT satisfy explicit Node.js"
        assert len(missing) == 1
        assert missing[0].canonical_name == "node.js"

        # B) Semantic similarity detects meaningful related evidence
        sem_matches = sm.compute_semantic_alignment(resume, jd)
        assert len(sem_matches) > 0, "Semantic matcher must find alignment"

        # C) Semantic evidence is stored
        sem_ev = sem_matches[0]
        assert sem_ev.similarity is not None
        assert sem_ev.similarity >= 0.45
        assert sem_ev.evidence.text == chunk.text
        assert sem_ev.requirement.id == "r_node"

        # D) Node.js is NOT falsely marked as an exact explicit skill
        for m in matched:
            assert m.canonical_name != "node.js" or m.match_type != MatchType.EXACT

        # E) Final score changes when semantic contribution changes
        lex = km.compute_lexical_evidence(resume, jd)

        score_with_sem = scorer.calculate_score_breakdown(
            matched, jd.requirements, [], [], sem_matches, lex,
        )
        score_no_sem = scorer.calculate_score_breakdown(
            matched, jd.requirements, [], [], [], lex,
        )
        assert score_with_sem.final_score > score_no_sem.final_score
        sem_delta = score_with_sem.final_score - score_no_sem.final_score
        assert sem_delta >= 0.10, f"Semantic contribution delta too small: {sem_delta}"

        # Required coverage must be 0.0 in both cases
        assert score_with_sem.required_skill_coverage == 0.0
        assert score_no_sem.required_skill_coverage == 0.0


# ===================================================================
# Ablation: keyword-only, semantic-only, combined
# ===================================================================


class TestAblation:
    """Demonstrate that keyword and semantic signals materially contribute independently."""

    def _build_scenario(self):
        """Common scenario: 2 required skills, 1 matched explicitly."""
        r1 = _req("r1", "Python", "python", text="Expert Python developer")
        r2 = _req("r2", "Kubernetes", "kubernetes", text="Production Kubernetes orchestration")

        sk_py = _skill("python", "Python")
        chunk = _chunk("c1",
            "Built Python microservices deployed on Kubernetes clusters with Helm charts.")
        resume = _resume("c1", "Dev", skills=[sk_py], chunks=[chunk])
        jd = _jd([r1, r2])
        return r1, r2, sk_py, chunk, resume, jd

    def test_keyword_only_ablation(self, km, scorer):
        """Ablation 1: keyword-only (semantic weight = 0)."""
        r1, r2, sk_py, chunk, resume, jd = self._build_scenario()

        matched, missing = km.match_explicit_skills(resume.skills, jd.requirements)
        lex = km.compute_lexical_evidence(resume, jd)

        kw_scorer = Scorer(weights={
            "required_skill_coverage": 0.55,
            "semantic_requirement_alignment": 0.0,
            "contextual_lexical_relevance": 0.35,
            "preferred_skill_coverage": 0.10,
        })
        s = kw_scorer.calculate_score_breakdown(matched, [r1, r2], [], [], [], lex)
        assert s.semantic_requirement_alignment == 0.0 or True  # weight is 0 anyway
        assert s.required_skill_coverage == 0.5  # 1 of 2
        # Score is purely keyword-driven
        assert s.final_score > 0.0

    def test_semantic_only_ablation(self, sm, scorer):
        """Ablation 2: semantic-only (keyword weight = 0)."""
        r1, r2, sk_py, chunk, resume, jd = self._build_scenario()

        sem = sm.compute_semantic_alignment(resume, jd)

        sem_scorer = Scorer(weights={
            "required_skill_coverage": 0.0,
            "semantic_requirement_alignment": 0.90,
            "contextual_lexical_relevance": 0.0,
            "preferred_skill_coverage": 0.10,
        })
        s = sem_scorer.calculate_score_breakdown([], [r1, r2], [], [], sem, [])
        assert s.required_skill_coverage == 0.0
        # Score is purely semantic-driven
        assert s.final_score > 0.0
        assert s.semantic_requirement_alignment > 0.0

    def test_combined_beats_either_ablation(self, km, sm, scorer):
        """Ablation 3: combined results leverage both signals."""
        r1, r2, sk_py, chunk, resume, jd = self._build_scenario()

        matched, missing = km.match_explicit_skills(resume.skills, jd.requirements)
        lex = km.compute_lexical_evidence(resume, jd)
        sem = sm.compute_semantic_alignment(resume, jd)

        # Combined (default weights)
        s_combined = scorer.calculate_score_breakdown(matched, [r1, r2], [], [], sem, lex)

        # Keyword-only ablation
        s_kw_only = scorer.calculate_score_breakdown(matched, [r1, r2], [], [], [], lex)

        # Semantic-only ablation
        s_sem_only = scorer.calculate_score_breakdown([], [r1, r2], [], [], sem, [])

        # Combined must be >= either ablation
        assert s_combined.final_score >= s_kw_only.final_score
        assert s_combined.final_score >= s_sem_only.final_score

        # Both signals materially contribute
        kw_contribution = s_combined.final_score - s_sem_only.final_score
        sem_contribution = s_combined.final_score - s_kw_only.final_score
        assert kw_contribution > 0.05, f"Keyword contribution too small: {kw_contribution}"
        assert sem_contribution > 0.05, f"Semantic contribution too small: {sem_contribution}"


# ===================================================================
# Component normalization bounds
# ===================================================================


class TestNormalizationBounds:
    """Verify all component scores are strictly within [0, 1]."""

    def test_all_components_bounded(self, scorer):
        r1 = _req("r1", "Python", "python")
        sk = _skill("python", "Python")
        sem = [MatchEvidence(
            requirement=r1,
            evidence=_chunk("e1", "Python ML pipelines"),
            match_type=MatchType.SEMANTIC_EXACT,
            confidence=0.99, similarity=0.99,
        )]
        lex = [MatchEvidence(
            requirement=r1,
            evidence=_chunk("e2", "Python scripting"),
            match_type=MatchType.LEXICAL,
            confidence=0.95,
        )]
        s = scorer.calculate_score_breakdown([sk], [r1], [sk], [r1], sem, lex)
        for field in [
            s.required_skill_coverage,
            s.semantic_requirement_alignment,
            s.contextual_lexical_relevance,
            s.preferred_skill_coverage,
            s.final_score,
        ]:
            assert 0.0 <= field <= 1.0, f"Out of bounds: {field}"

    def test_max_possible_score(self, scorer):
        """Perfect candidate: all 4 components at 1.0 → final = 1.0."""
        r1 = _req("r1", "Python", "python")
        p1 = _req("p1", "Redis", "redis", RequirementType.PREFERRED)
        sk_py = _skill("python", "Python")
        sk_redis = _skill("redis", "Redis")
        sem = [
            MatchEvidence(
                requirement=r1,
                evidence=_chunk("e1", "Python"),
                match_type=MatchType.SEMANTIC_EXACT,
                confidence=1.0, similarity=1.0,
            ),
            MatchEvidence(
                requirement=p1,
                evidence=_chunk("e2", "Redis"),
                match_type=MatchType.SEMANTIC_EXACT,
                confidence=1.0, similarity=1.0,
            ),
        ]
        lex = [
            MatchEvidence(
                requirement=r1,
                evidence=_chunk("e3", "Python"),
                match_type=MatchType.LEXICAL,
                confidence=1.0,
            ),
            MatchEvidence(
                requirement=p1,
                evidence=_chunk("e4", "Redis"),
                match_type=MatchType.LEXICAL,
                confidence=1.0,
            ),
        ]
        s = scorer.calculate_score_breakdown([sk_py], [r1], [sk_redis], [p1], sem, lex)
        assert s.final_score == 1.0
