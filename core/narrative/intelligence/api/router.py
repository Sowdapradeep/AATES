import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database.session import get_db
from core.narrative.intelligence.character_intelligence import CharacterIntelligenceEngine
from core.narrative.intelligence.relationship_intelligence import RelationshipIntelligenceEngine
from core.narrative.intelligence.timeline_intelligence import TimelineIntelligenceEngine
from core.narrative.intelligence.story_arc_intelligence import StoryArcIntelligenceEngine
from core.narrative.intelligence.continuity_intelligence import ContinuityIntelligenceEngine
from core.narrative.intelligence.narrative_memory_engine import NarrativeMemoryEngine
from core.narrative.intelligence.universe_evolution_engine import UniverseEvolutionEngine
from core.narrative.intelligence.creative_director_ai import CreativeDirectorAI

router = APIRouter(prefix="/v1/intelligence", tags=["Narrative Intelligence v2"])

# ── Input Schemas ─────────────────────────────────────────────────────────────
class CharacterGrowthIn(BaseModel):
    character_id: uuid.UUID
    recent_events: List[str]

class RelationshipEvolveIn(BaseModel):
    character_a_id: uuid.UUID
    character_b_id: uuid.UUID
    interaction_event: str

class TimelineBeatIn(BaseModel):
    universe_id: uuid.UUID
    beat_title: str
    event_type: str = "beat"
    context_notes: str = ""

class ContinuityCheckIn(BaseModel):
    universe_id: uuid.UUID
    proposed_action: str
    participating_character_names: List[str] = []
    target_location_name: Optional[str] = None

class MemorySearchIn(BaseModel):
    universe_id: uuid.UUID
    query: str
    top_k: int = 5

class UniverseEvolveIn(BaseModel):
    universe_id: uuid.UUID
    episodes_elapsed: int

class CreativeDirectorReasonIn(BaseModel):
    universe_id: uuid.UUID
    season: int
    episode: int
    episode_id: str
    objective_prompt: str

# ── API Routes ────────────────────────────────────────────────────────────────

@router.post("/character/growth")
def evaluate_character_growth(payload: CharacterGrowthIn, db: Session = Depends(get_db)):
    engine = CharacterIntelligenceEngine(db)
    return engine.evaluate_character_growth(payload.character_id, payload.recent_events)

@router.post("/relationship/evolve")
def evolve_relationship(payload: RelationshipEvolveIn, db: Session = Depends(get_db)):
    engine = RelationshipIntelligenceEngine(db)
    return engine.evolve_relationship(payload.character_a_id, payload.character_b_id, payload.interaction_event)

@router.post("/timeline/beat")
def generate_timeline_beat(payload: TimelineBeatIn, db: Session = Depends(get_db)):
    engine = TimelineIntelligenceEngine(db)
    return engine.generate_timeline_beat(
        payload.universe_id, payload.beat_title, payload.event_type, payload.context_notes
    )

@router.get("/story-arcs/{universe_id}/unfinished")
def detect_unfinished_arcs(universe_id: uuid.UUID, db: Session = Depends(get_db)):
    engine = StoryArcIntelligenceEngine(db)
    return engine.detect_unfinished_arcs(universe_id)

@router.post("/continuity/validate")
def validate_continuity_reasoning(payload: ContinuityCheckIn, db: Session = Depends(get_db)):
    engine = ContinuityIntelligenceEngine(db)
    return engine.validate_story_action(
        payload.universe_id, payload.proposed_action,
        payload.participating_character_names, payload.target_location_name
    )

@router.post("/memory/search")
def search_semantic_memory(payload: MemorySearchIn, db: Session = Depends(get_db)):
    engine = NarrativeMemoryEngine(db)
    return engine.search_semantic_memory(payload.universe_id, payload.query, payload.top_k)

@router.post("/universe/evolve")
def evolve_universe_macro(payload: UniverseEvolveIn, db: Session = Depends(get_db)):
    engine = UniverseEvolutionEngine(db)
    return engine.evolve_universe(payload.universe_id, payload.episodes_elapsed)

@router.post("/creative-director/reason")
async def creative_director_reason_and_plan(payload: CreativeDirectorReasonIn, db: Session = Depends(get_db)):
    engine = CreativeDirectorAI(db)
    return await engine.execute_reasoning_and_create_blueprint(
        universe_id=payload.universe_id,
        season=payload.season,
        episode=payload.episode,
        episode_id=payload.episode_id,
        objective_prompt=payload.objective_prompt
    )
