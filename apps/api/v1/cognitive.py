from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any
from sqlalchemy.orm import Session
from core.database.session import get_db
from brain.decision.engine import decision_engine
from brain.story_bible.bible import story_bible_engine
from brain.planner.universe import UniversePlanner
from brain.planner.season import SeasonPlanner
from brain.planner.episode import EpisodePlanner
from brain.planner.scene import ScenePlanner
from runtime.registry.registry import agent_registry

router = APIRouter()

class BibleUpdateIn(BaseModel):
    """Input payload for versioned and auditable Story Bible updates."""
    section: str
    key: str
    new_value: Any
    author: str
    reason: str
    workflow_id: str | None = None

class UniversePlanIn(BaseModel):
    """Input parameters for formulating universe core lore seeds."""
    name: str
    genre: str
    core_themes: list[str]

class SeasonPlanIn(BaseModel):
    """Input parameters for season arcs planners."""
    universe_id: str
    season_number: int
    total_episodes: int

class EpisodePlanIn(BaseModel):
    """Input parameters for episode objective screenplays planner."""
    universe_id: str
    season: int
    episode: int

class ScenePlanIn(BaseModel):
    """Input parameters for scene emotional goals planners."""
    episode_id: str
    scene_number: int

@router.get("/decisions")
def get_decisions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Retrieves list of explainable decisions made by autonomous agents."""
    return decision_engine.get_decisions(skip=skip, limit=limit, db=db)

@router.get("/universes/{universe_id}/bible")
def get_bible(universe_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Retrieves current Story Bible lore properties mapping for a universe."""
    return story_bible_engine.get_bible(universe_id, db=db)

@router.post("/universes/{universe_id}/bible")
def update_bible(universe_id: str, payload: BibleUpdateIn, db: Session = Depends(get_db)) -> dict[str, str]:
    """Applies a versioned change and logs an audit log trail inside the database."""
    try:
        story_bible_engine.update_bible(
            universe_id=universe_id,
            section=payload.section,
            key=payload.key,
            new_value=payload.new_value,
            author=payload.author,
            reason=payload.reason,
            workflow_id=payload.workflow_id,
            db=db
        )
        return {"status": "success", "message": "Story Bible updated and audited successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Story Bible: {str(e)}"
        )

@router.post("/planning/universe")
async def plan_universe(payload: UniversePlanIn) -> dict[str, Any]:
    """Triggers the Universe planner to formulate lore seeds and world rules."""
    planner = UniversePlanner()
    return await planner.create_universe_plan(payload.name, payload.genre, payload.core_themes)

@router.post("/planning/season")
async def plan_season(payload: SeasonPlanIn) -> dict[str, Any]:
    """Triggers the Season planner to map major conflicts and arcs."""
    planner = SeasonPlanner()
    return await planner.create_season_plan(payload.universe_id, payload.season_number, payload.total_episodes)

@router.post("/planning/episode")
async def plan_episode(payload: EpisodePlanIn) -> dict[str, Any]:
    """Triggers the Episode planner to outline scene counts and beat objectives."""
    planner = EpisodePlanner()
    return await planner.create_episode_plan(payload.universe_id, payload.season, payload.episode)

@router.post("/planning/scene")
async def plan_scene(payload: ScenePlanIn) -> dict[str, Any]:
    """Triggers the Scene planner to construct emotional goals and continuity constraints."""
    planner = ScenePlanner()
    return await planner.create_scene_plan(payload.episode_id, payload.scene_number)

@router.get("/agents")
def list_agents() -> list[dict[str, Any]]:
    """Retrieves runtime registration list of active AI agents and metadata."""
    return agent_registry.list_agents()
