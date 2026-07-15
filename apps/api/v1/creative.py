from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any
from sqlalchemy.orm import Session
from core.database.session import get_db
from contracts.dto.creative import (
    CharacterProfile, VillainProfile, RelationshipDTO, LocationDTO, OrganizationDTO,
    StoryArcDTO, ConflictDTO, PlotPointDTO, DialoguePlanDTO, ValidationResultDTO
)
from brain.creative_generator import creative_generator
from brain.plot_engine import plot_engine
from brain.narrative_engine import dialogue_planning_engine, tamil_narrative_engine
from brain.validation_engine import validation_engine
from brain.blueprint_generator import blueprint_generator

router = APIRouter()


class UniverseIn(BaseModel):
    """Input parameters for universe metadata initialization."""
    universe_id: str
    name: str
    genre: str
    themes: list[str]

class SlangTranslateIn(BaseModel):
    """Input dialogue text and slang tag category (e.g. Chennai)."""
    text: str
    slang_type: str

class ContinuityValIn(BaseModel):
    """Input action parameters for Story Bible continuity checks."""
    universe_id: str
    section: str
    key: str
    action_proposed: str

class CanonValIn(BaseModel):
    """Input plot parameters for Story Bible base world rules checks."""
    universe_id: str
    proposed_plot: str

@router.post("/creative/universe")
async def generate_universe(payload: UniverseIn, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Triggers the Universe Generator to register a new universe configuration."""
    return await creative_generator.generate_universe(payload.universe_id, payload.name, payload.genre, payload.themes, db=db)

@router.post("/creative/character")
async def generate_character(universe_id: str, payload: CharacterProfile, db: Session = Depends(get_db)) -> CharacterProfile:
    """Triggers the Character Generator to register a new character profile."""
    return await creative_generator.generate_character(universe_id, payload, db=db)

@router.post("/creative/villain")
async def generate_villain(universe_id: str, payload: VillainProfile, db: Session = Depends(get_db)) -> VillainProfile:
    """Triggers the Villain Generator to append villain traits to a character profile."""
    return await creative_generator.generate_villain(universe_id, payload, db=db)

@router.post("/creative/location")
async def generate_location(universe_id: str, payload: LocationDTO, db: Session = Depends(get_db)) -> LocationDTO:
    """Triggers the Location Generator to register set locations settings."""
    return await creative_generator.generate_location(universe_id, payload, db=db)

@router.post("/creative/organization")
async def generate_organization(universe_id: str, payload: OrganizationDTO, db: Session = Depends(get_db)) -> OrganizationDTO:
    """Triggers the Organization Generator to register structural factions settings."""
    return await creative_generator.generate_organization(universe_id, payload, db=db)

@router.post("/creative/relationship")
async def establish_relationship(universe_id: str, payload: RelationshipDTO, db: Session = Depends(get_db)) -> RelationshipDTO:
    """Triggers the Relationship Engine to link structural ties between characters."""
    return await creative_generator.establish_relationship(universe_id, payload, db=db)

@router.post("/creative/story-arc")
async def create_story_arc(universe_id: str, payload: StoryArcDTO, db: Session = Depends(get_db)) -> StoryArcDTO:
    """Triggers the Story Arc Engine to document creative season conflicts directions."""
    return await plot_engine.create_story_arc(universe_id, payload, db=db)

@router.post("/creative/conflict")
async def create_conflict(universe_id: str, payload: ConflictDTO, db: Session = Depends(get_db)) -> ConflictDTO:
    """Triggers the Conflict Engine to register community disagreement models."""
    return await plot_engine.create_conflict(universe_id, payload, db=db)

@router.post("/creative/plot-point")
async def generate_plot_point(universe_id: str, payload: PlotPointDTO, db: Session = Depends(get_db)) -> PlotPointDTO:
    """Triggers the Plot Engine to append a chronological beat to the timeline."""
    return await plot_engine.generate_plot_point(universe_id, payload, db=db)

@router.post("/creative/dialogue/translate")
async def translate_dialogue(payload: SlangTranslateIn) -> dict[str, str]:
    """Applies regional Tamil dialogue slang vocabularies to input dialogue parameters."""
    translated = await tamil_narrative_engine.adapt_dialogue_to_slang(payload.text, payload.slang_type)
    return {"original": payload.text, "translated": translated}

@router.post("/creative/validate/continuity")
async def validate_continuity(payload: ContinuityValIn, db: Session = Depends(get_db)) -> ValidationResultDTO:
    """Performs a timeline state and character profile continuity audit."""
    return await validation_engine.validate_continuity(payload.universe_id, payload.section, payload.key, payload.action_proposed, db=db)

@router.post("/creative/validate/canon")
async def validate_canon(payload: CanonValIn, db: Session = Depends(get_db)) -> ValidationResultDTO:
    """Performs compliance checking against base Story Bible rules."""
    return await validation_engine.validate_canon(payload.universe_id, payload.proposed_plot, db=db)

class BlueprintIn(BaseModel):
    """Input parameters for assembly of Production Blueprints."""
    universe_id: str
    season: int
    episode: int
    episode_id: str

@router.post("/creative/blueprint")
async def generate_blueprint(payload: BlueprintIn, db: Session = Depends(get_db)) -> Any:
    """Compiles characters, lore, and dialogue states into a standard media-independent Production Blueprint."""
    return await blueprint_generator.generate_blueprint(
        universe_id=payload.universe_id,
        season=payload.season,
        episode=payload.episode,
        episode_id=payload.episode_id,
        db=db
    )

@router.get("/creative/blueprint/{episode_id}")
def get_blueprint(episode_id: str, db: Session = Depends(get_db)) -> Any:
    """Retrieves compiled Production Blueprint JSON specifications for downstream consumption."""
    from core.database.models import SystemState
    state = db.query(SystemState).filter(SystemState.state_key == f"blueprint-{episode_id}").first()
    if not state:
        raise HTTPException(status_code=404, detail="Production blueprint not found.")
    return state.state_value

