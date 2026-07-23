"""
Phase 11 — Autonomous Self-Evolving Studio Tests

Covers all 16 autonomous capabilities:
  1. AutonomousDecisionEngine (centralized commit authority)
  2. StrategicMemory
  3. WorldModel
  4. MissionEngine
  5. AutonomousExecutiveCouncil
  6. ContinuousLearningEngine
  7. AgentEvolutionTracker
  8. PromptEvolutionEngine
  9. ModelEvolutionTracker
  10. UniverseEvolutionEngine
  11. ProductionOptimizer
  12. PublishingIntelligenceEngine
  13. BusinessIntelligenceEngine
  14. LifelongMemoryStore
  15. AutonomousGoalEngine
  16. Autonomy API endpoints
"""
import asyncio
import pytest
from fastapi.testclient import TestClient

from brain.autonomy.decision_engine import (
    AutonomousDecisionEngine, Recommendation,
)
from brain.autonomy.strategic_memory import StrategicMemory
from brain.autonomy.world_model import WorldModel
from brain.autonomy.mission_engine import MissionEngine
from brain.autonomy.executive_council import AutonomousExecutiveCouncil
from brain.autonomy.learning_engine import ContinuousLearningEngine
from brain.autonomy.agent_evolution import AgentEvolutionTracker
from brain.autonomy.prompt_evolution import PromptEvolutionEngine
from brain.autonomy.model_evolution import ModelEvolutionTracker
from brain.autonomy.universe_evolution import UniverseEvolutionEngine
from brain.autonomy.production_optimizer import ProductionOptimizer
from brain.autonomy.publishing_intelligence import PublishingIntelligenceEngine
from brain.autonomy.business_intelligence import BusinessIntelligenceEngine
from brain.autonomy.lifelong_memory import LifelongMemoryStore
from brain.autonomy.goal_engine import AutonomousGoalEngine


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fresh_engine() -> AutonomousDecisionEngine:
    return AutonomousDecisionEngine()


# ── 1. Decision Engine ───────────────────────────────────────────────────────

def test_decision_engine_submit_and_process() -> None:
    """Recommendations are queued, prioritized, and committed in a single cycle."""
    engine = _fresh_engine()

    # Submit two recommendations on different targets
    engine.submit(Recommendation(
        source="TestA", priority="business", action="cut_cost",
        target="budget_engine", payload={"amount": 1.0}, estimated_impact=5.0,
    ))
    engine.submit(Recommendation(
        source="TestB", priority="optimization", action="cache_warm",
        target="asset_library", payload={"n": 20}, estimated_impact=3.0,
    ))

    result = engine.process_cycle()
    assert result["committed"] == 2
    assert result["rejected"] == 0
    assert len(engine.get_decision_log()) == 2


def test_decision_engine_conflict_resolution() -> None:
    """Higher-priority recommendation wins when two target the same action."""
    engine = _fresh_engine()

    engine.submit(Recommendation(
        source="Low", priority="optimization", action="change_model",
        target="model_router", payload={"tier": "economy"}, estimated_impact=2.0,
    ))
    engine.submit(Recommendation(
        source="High", priority="business", action="change_model",
        target="model_router", payload={"tier": "standard"}, estimated_impact=7.0,
    ))

    result = engine.process_cycle()
    assert result["committed"] == 1
    assert result["rejected"] == 1
    # The committed decision should be from the higher-priority source
    assert engine.get_decision_log()[-1]["source"] == "High"


# ── 2. Strategic Memory ──────────────────────────────────────────────────────

def test_strategic_memory_record_and_retrieve() -> None:
    """Records persist and are retrievable by category."""
    mem = StrategicMemory()
    mem.record("cost_optimizations", {"action": "switch_to_haiku", "savings": 0.5})
    mem.record("cost_optimizations", {"action": "enable_reuse", "savings": 0.3})
    entries = mem.retrieve("cost_optimizations")
    assert len(entries) == 2
    assert entries[0]["action"] == "switch_to_haiku"
    assert mem.summary()["cost_optimizations"] == 2


# ── 3. World Model ───────────────────────────────────────────────────────────

def test_world_model_update_and_snapshot() -> None:
    """World model dimensions update correctly and appear in snapshot."""
    wm = WorldModel()
    wm.update("budgets", {"spent_usd": 1.5})
    wm.register_universe("u-1", {"name": "Karnan Chronicles"})
    snap = wm.snapshot()
    assert snap["budgets"]["spent_usd"] == 1.5
    assert "u-1" in snap["universes"]
    assert snap["last_updated"] is not None


# ── 4. Mission Engine ────────────────────────────────────────────────────────

def test_mission_engine_goal_generation() -> None:
    """Goals are generated aligned with the studio mission."""
    me = MissionEngine()
    # Low retention triggers retention goal
    goal = me.generate_mission_aligned_goal({"avg_retention_pct": 40.0})
    assert "retention" in goal["goal_id"]
    assert goal["status"] == "active"
    assert me.get_mission_summary()["total_goals"] == 1


# ── 5. Executive Council ─────────────────────────────────────────────────────

def test_executive_council_review() -> None:
    """Post-episode review generates correct executive action and submits recommendations."""
    engine = _fresh_engine()
    council = AutonomousExecutiveCouncil(engine)

    report = {
        "episode_id": "ep-test",
        "quality_score": 72.0,      # below threshold
        "cost_usd": 0.5,
        "render_time_sec": 25.0,
        "audience_retention_pct": 50.0,  # below threshold
        "revision_count": 0,
    }

    result = asyncio.run(council.review_episode(report))
    assert result["executive_action"] in ("regenerate", "continue_with_adjustments")
    assert len(result["recommendations_submitted"]) >= 1
    assert engine.summary()["pending"] >= 1


# ── 6. Learning Engine ───────────────────────────────────────────────────────

def test_continuous_learning_weight_adjustments() -> None:
    """Successful prompts gain weight, poor prompts lose weight."""
    engine = _fresh_engine()
    learner = ContinuousLearningEngine(engine)

    learner.record_episode_outcome({
        "quality_score": 92.0, "prompt_id": "p-good", "primary_model": "claude-sonnet",
        "universe_id": "u-1",
    })
    learner.record_episode_outcome({
        "quality_score": 55.0, "prompt_id": "p-bad", "primary_model": "titan-tg1",
        "universe_id": "u-1",
    })

    summary = learner.get_learning_summary()
    assert summary["prompt_weights"]["p-good"] > 1.0
    assert summary["prompt_weights"]["p-bad"] < 1.0


# ── 7. Agent Evolution ───────────────────────────────────────────────────────

def test_agent_evolution_tracking() -> None:
    """Agent profiles accumulate runs and compute correct confidence scores."""
    engine = _fresh_engine()
    tracker = AgentEvolutionTracker(engine)

    tracker.record("Dialogue", quality=90.0, cost=0.002, latency_ms=400, success=True)
    tracker.record("Dialogue", quality=85.0, cost=0.002, latency_ms=350, success=True)

    profile = tracker.get_profile("Dialogue")
    assert profile["runs"] == 2
    assert profile["avg_quality_score"] == 87.5
    assert profile["confidence"] > 0.0


# ── 8. Prompt Evolution ──────────────────────────────────────────────────────

def test_prompt_evolution_promotion_and_retirement() -> None:
    """Prompts are promoted when consistently high-scoring, retired when low."""
    engine = _fresh_engine()
    pe = PromptEvolutionEngine(engine)

    pe.register("p1", "v1", "A beautiful Tamil village scene")
    # 3 high-scoring runs -> promote
    pe.record_run("p1", "v1", quality=92.0)
    pe.record_run("p1", "v1", quality=90.0)
    pe.record_run("p1", "v1", quality=89.0)

    best = pe.get_active_best("p1")
    assert best is not None
    assert best["status"] == "promoted"

    pe.register("p2", "v1", "An uninspired generic scene")
    # 3 low-scoring runs -> retire
    pe.record_run("p2", "v1", quality=50.0)
    pe.record_run("p2", "v1", quality=55.0)
    pe.record_run("p2", "v1", quality=60.0)

    registry = pe.get_registry()
    p2_entries = [r for r in registry if r["prompt_id"] == "p2"]
    assert p2_entries[0]["status"] == "retired"


# ── 9. Model Evolution ───────────────────────────────────────────────────────

def test_model_evolution_rankings() -> None:
    """Models are ranked by composite score and underperformers are deprioritized."""
    engine = _fresh_engine()
    tracker = ModelEvolutionTracker(engine)

    # Good model
    for _ in range(5):
        tracker.record_invocation("claude-sonnet", quality=90.0, cost_usd=0.003,
                                  latency_ms=1200, failed=False)
    # Bad model
    for _ in range(5):
        tracker.record_invocation("bad-model", quality=30.0, cost_usd=0.01,
                                  latency_ms=5000, failed=True, hallucination=True)

    rankings = tracker.get_rankings()
    assert rankings[0]["model_id"] == "claude-sonnet"
    assert rankings[-1]["model_id"] == "bad-model"
    # Bad model should have submitted deprioritization recommendation
    assert engine.summary()["pending"] >= 1


# ── 10. Universe Evolution ────────────────────────────────────────────────────

def test_universe_evolution_decisions() -> None:
    """High-quality universes expand; weak characters are retired."""
    engine = _fresh_engine()
    ue = UniverseEvolutionEngine(engine)

    result = ue.evaluate_universe("u-karnan", {
        "avg_quality": 88.0,
        "avg_engagement": 0.8,
        "episode_count": 6,
        "top_characters": ["Karnan"],
        "underperforming_characters": ["VillagerA"],
    })
    assert "expand_universe" in result["decisions_submitted"]
    assert "create_spinoff" in result["decisions_submitted"]
    assert any("retire_character" in d for d in result["decisions_submitted"])
    assert "evolve_lore" in result["decisions_submitted"]


# ── 11. Production Optimizer ──────────────────────────────────────────────────

def test_production_optimizer_cost_efficiency() -> None:
    """High-cost renders trigger economy routing recommendations."""
    engine = _fresh_engine()
    optimizer = ProductionOptimizer(engine)

    optimizer.record_render("ep-1", render_time_sec=120.0, cost_usd=3.0,
                            asset_reuse_hits=1, asset_reuse_misses=9)

    summary = optimizer.get_optimization_summary()
    assert summary["episodes_optimized"] == 1
    # High cost + high render time should queue recommendations
    assert engine.summary()["pending"] >= 1


# ── 12. Publishing Intelligence ───────────────────────────────────────────────

def test_publishing_intelligence_schedule_update() -> None:
    """High-engagement publishes update the recommended schedule."""
    engine = _fresh_engine()
    pi = PublishingIntelligenceEngine(engine)

    pi.record_publish_outcome("ep-1", {
        "engagement_score": 0.9,
        "publish_day": "Saturday",
        "publish_hour_utc": 18,
    })

    schedule = pi.get_recommended_schedule()
    assert schedule["best_day"] == "Saturday"
    assert schedule["best_hour_utc"] == 18


# ── 13. Business Intelligence ────────────────────────────────────────────────

def test_business_intelligence_budget_guard() -> None:
    """Budget consumption over 80% triggers production scale reduction."""
    engine = _fresh_engine()
    bi = BusinessIntelligenceEngine(engine)

    result = bi.ingest_metrics({
        "total_cost_usd": 4.5,
        "budget_usd": 5.0,
        "avg_retention_pct": 70.0,
        "engagement_score": 0.6,
        "audience_growth_pct": 10.0,
    })

    assert result["budget_consumed_pct"] == 90.0
    assert "reduce_production_scale" in result["recommendations_submitted"]


# ── 14. Lifelong Memory ──────────────────────────────────────────────────────

def test_lifelong_memory_never_forgets() -> None:
    """Memories accumulate across categories and are searchable."""
    mem = LifelongMemoryStore()
    mem.remember("successful_prompts", {"prompt": "Karnan battle scene", "score": 92.0})
    mem.remember("failed_prompts", {"prompt": "Generic village", "score": 45.0})
    mem.remember("successful_universes", {"universe": "Karnan", "episodes": 10})

    summary = mem.get_summary()
    assert summary["total_memories"] == 3
    assert summary["categories"]["successful_prompts"] == 1

    results = mem.search("Karnan")
    assert len(results) >= 2  # found in prompts and universes


# ── 15. Goal Engine ──────────────────────────────────────────────────────────

def test_goal_engine_chained_generation() -> None:
    """Goals are generated aligned with mission and chain upon achievement."""
    engine = _fresh_engine()
    mission = MissionEngine()
    goal_engine = AutonomousGoalEngine(engine, mission)

    # Generate first goal
    goal = goal_engine.generate_next_goal({
        "avg_retention_pct": 40.0,
        "avg_quality_score": 85.0,
        "total_cost_usd": 0.5,
    })
    assert goal["status"] == "active"
    assert "retention" in goal["goal_id"]

    # Evaluate and achieve it -> should chain-generate next goal
    result = goal_engine.evaluate_goal(goal["goal_id"], {"avg_retention_pct": 80.0})
    assert result["status"] == "achieved"
    assert "next_goal_id" in result
    assert len(goal_engine.get_goal_chain()) >= 2


# ── 16. Autonomy API Endpoints ───────────────────────────────────────────────

def test_autonomy_council_review_endpoint(client: TestClient) -> None:
    """POST /v1/autonomy/council/review triggers executive review."""
    res = client.post("/v1/autonomy/council/review", json={
        "episode_id": "ep-api-test",
        "quality_score": 90.0,
        "cost_usd": 0.3,
        "render_time_sec": 20.0,
        "audience_retention_pct": 80.0,
        "revision_count": 0,
    })
    assert res.status_code == 200
    assert "executive_action" in res.json()


def test_autonomy_world_snapshot_endpoint(client: TestClient) -> None:
    """GET /v1/autonomy/world/snapshot returns the current world model."""
    res = client.get("/v1/autonomy/world/snapshot")
    assert res.status_code == 200
    assert "budgets" in res.json()
    assert "audience_metrics" in res.json()


def test_autonomy_mission_status_endpoint(client: TestClient) -> None:
    """GET /v1/autonomy/mission/status returns mission progress."""
    res = client.get("/v1/autonomy/mission/status")
    assert res.status_code == 200
    assert "mission" in res.json()


def test_autonomy_decision_submit_endpoint(client: TestClient) -> None:
    """POST /v1/autonomy/decision/submit accepts external recommendations."""
    res = client.post("/v1/autonomy/decision/submit", json={
        "source": "test",
        "priority": "optimization",
        "action": "test_action",
        "target": "asset_library",
        "payload": {"key": "value"},
        "estimated_impact": 1.0,
    })
    assert res.status_code == 200
    assert "submitted" in res.json()
