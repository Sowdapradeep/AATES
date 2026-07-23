"""
Autonomy API Router — Phase 11 autonomous self-evolving studio endpoints.

Prefix: /v1/autonomy

All routes expose the autonomous studio intelligence layer to the dashboard.
No human approval is required at any step — all decisions are autonomous.
"""
from fastapi import APIRouter
from typing import Any

from brain.autonomy.decision_engine import autonomous_decision_engine, Recommendation
from brain.autonomy.strategic_memory import strategic_memory
from brain.autonomy.world_model import world_model
from brain.autonomy.mission_engine import mission_engine
from brain.autonomy.lifelong_memory import lifelong_memory
from brain.autonomy.executive_council import AutonomousExecutiveCouncil
from brain.autonomy.learning_engine import ContinuousLearningEngine
from brain.autonomy.agent_evolution import AgentEvolutionTracker
from brain.autonomy.prompt_evolution import PromptEvolutionEngine
from brain.autonomy.model_evolution import ModelEvolutionTracker
from brain.autonomy.universe_evolution import UniverseEvolutionEngine
from brain.autonomy.production_optimizer import ProductionOptimizer
from brain.autonomy.publishing_intelligence import PublishingIntelligenceEngine
from brain.autonomy.business_intelligence import BusinessIntelligenceEngine
from brain.autonomy.goal_engine import AutonomousGoalEngine

router = APIRouter(prefix="/v1/autonomy", tags=["autonomy"])

# ── Shared engine instances (request-scoped for API simplicity) ───────────────
# In production, these would be application-lifetime singletons injected via DI.

def _make_council() -> AutonomousExecutiveCouncil:
    return AutonomousExecutiveCouncil(autonomous_decision_engine)

def _make_learning() -> ContinuousLearningEngine:
    return ContinuousLearningEngine(autonomous_decision_engine)

def _make_agent_tracker() -> AgentEvolutionTracker:
    return AgentEvolutionTracker(autonomous_decision_engine)

def _make_prompt_evolution() -> PromptEvolutionEngine:
    return PromptEvolutionEngine(autonomous_decision_engine)

def _make_model_evolution() -> ModelEvolutionTracker:
    return ModelEvolutionTracker(autonomous_decision_engine)

def _make_universe_evolution() -> UniverseEvolutionEngine:
    return UniverseEvolutionEngine(autonomous_decision_engine)

def _make_optimizer() -> ProductionOptimizer:
    return ProductionOptimizer(autonomous_decision_engine)

def _make_publishing() -> PublishingIntelligenceEngine:
    return PublishingIntelligenceEngine(autonomous_decision_engine)

def _make_business() -> BusinessIntelligenceEngine:
    return BusinessIntelligenceEngine(autonomous_decision_engine)

def _make_goal_engine() -> AutonomousGoalEngine:
    return AutonomousGoalEngine(autonomous_decision_engine, mission_engine)


# ── Executive Council ─────────────────────────────────────────────────────────

@router.post("/council/review")
async def executive_council_review(payload: dict) -> dict[str, Any]:
    """Trigger a post-episode autonomous executive council review."""
    council = _make_council()
    result = await council.review_episode(payload)
    return result


@router.get("/council/decisions")
def get_council_decisions() -> dict[str, Any]:
    """Return the autonomous decision engine committed decisions log."""
    return {
        "summary": autonomous_decision_engine.summary(),
        "recent_decisions": autonomous_decision_engine.get_decision_log(limit=20),
        "recent_rejections": autonomous_decision_engine.get_rejected_log(limit=10),
    }


# ── Learning Engine ───────────────────────────────────────────────────────────

@router.get("/learning/summary")
def get_learning_summary() -> dict[str, Any]:
    """Return learning engine statistics and prompt/model weight distributions."""
    engine = _make_learning()
    return engine.get_learning_summary()


# ── Agent Evolution ───────────────────────────────────────────────────────────

@router.get("/agents/evolution")
def get_agent_evolution() -> list[dict[str, Any]]:
    """Return per-agent performance profiles with confidence and success rates."""
    tracker = _make_agent_tracker()
    return tracker.get_all_profiles()


# ── Prompt Evolution ──────────────────────────────────────────────────────────

@router.get("/prompts/registry")
def get_prompt_registry() -> dict[str, Any]:
    """Return the full prompt version registry with promotion/retirement status."""
    engine = _make_prompt_evolution()
    return {"prompts": engine.get_registry()}


# ── Model Evolution ───────────────────────────────────────────────────────────

@router.get("/models/rankings")
def get_model_rankings() -> dict[str, Any]:
    """Return dynamic model rankings by composite performance score."""
    tracker = _make_model_evolution()
    return {"rankings": tracker.get_rankings()}


# ── Universe Evolution ────────────────────────────────────────────────────────

@router.post("/universe/evolve")
async def evolve_universe(payload: dict) -> dict[str, Any]:
    """Trigger a universe evolution decision for the specified universe."""
    universe_id = payload.get("universe_id", "default")
    engine = _make_universe_evolution()
    return engine.evaluate_universe(universe_id, payload)


# ── Publishing Intelligence ───────────────────────────────────────────────────

@router.get("/publishing/schedule")
def get_publishing_schedule() -> dict[str, Any]:
    """Return the currently recommended autonomous publishing schedule."""
    engine = _make_publishing()
    return engine.get_recommended_schedule()


# ── Business Intelligence ─────────────────────────────────────────────────────

@router.get("/business/dashboard")
def get_business_dashboard() -> dict[str, Any]:
    """Return the CEO business intelligence dashboard."""
    engine = _make_business()
    return engine.get_business_dashboard()


# ── Lifelong Memory ───────────────────────────────────────────────────────────

@router.get("/memory/summary")
def get_memory_summary() -> dict[str, Any]:
    """Return lifelong memory statistics across all categories."""
    return lifelong_memory.get_summary()


# ── Goal Engine ───────────────────────────────────────────────────────────────

@router.post("/goals/generate")
def generate_next_goal(payload: dict | None = None) -> dict[str, Any]:
    """Generate the next autonomous mission-aligned goal."""
    engine = _make_goal_engine()
    return engine.generate_next_goal(payload or {})


@router.get("/goals/chain")
def get_goal_chain() -> dict[str, Any]:
    """Return the current autonomous goal chain."""
    engine = _make_goal_engine()
    return {
        "mission_summary": mission_engine.get_mission_summary(),
        "goal_chain": engine.get_goal_chain(),
    }


# ── World Model ───────────────────────────────────────────────────────────────

@router.get("/world/snapshot")
def get_world_snapshot() -> dict[str, Any]:
    """Return the current World Model snapshot."""
    return world_model.snapshot()


# ── Mission ───────────────────────────────────────────────────────────────────

@router.get("/mission/status")
def get_mission_status() -> dict[str, Any]:
    """Return current mission progress and active objectives."""
    return {
        **mission_engine.get_mission_summary(),
        "active_goals": mission_engine.get_active_goals(),
    }


# ── Decision Engine ───────────────────────────────────────────────────────────

@router.post("/decision/submit")
def submit_recommendation(payload: dict) -> dict[str, Any]:
    """Submit a recommendation to the Autonomous Decision Engine for evaluation."""
    rec = Recommendation(
        source=payload.get("source", "external"),
        priority=payload.get("priority", "optimization"),
        action=payload.get("action", ""),
        target=payload.get("target", ""),
        payload=payload.get("payload", {}),
        estimated_impact=payload.get("estimated_impact", 1.0),
    )
    result = autonomous_decision_engine.submit(rec)
    return {"submitted": result, "summary": autonomous_decision_engine.summary()}
