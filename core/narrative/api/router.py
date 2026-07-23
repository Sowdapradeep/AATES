import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database.session import get_db
from core.narrative.dto.narrative_dto import (
    UniverseCreateDTO, UniverseUpdateDTO, UniverseResponseDTO,
    CharacterCreateDTO, CharacterResponseDTO,
    RelationshipCreateDTO, RelationshipResponseDTO,
    LocationCreateDTO, LocationResponseDTO,
    OrganizationCreateDTO, OrganizationResponseDTO,
    StoryArcCreateDTO, StoryArcResponseDTO,
    TimelineEventCreateDTO, TimelineEventResponseDTO,
    SeasonCreateDTO, SeasonResponseDTO,
    EpisodeCreateDTO, EpisodeResponseDTO,
    SceneCreateDTO, SceneResponseDTO
)
from core.narrative.services.universe_service import UniverseService
from core.narrative.services.character_service import CharacterService
from core.narrative.services.relationship_service import RelationshipService
from core.narrative.services.location_service import LocationService
from core.narrative.services.organization_service import OrganizationService
from core.narrative.services.story_arc_service import StoryArcService
from core.narrative.services.timeline_service import TimelineService
from core.narrative.services.season_service import SeasonService
from core.narrative.services.episode_service import EpisodeService
from core.narrative.services.scene_service import SceneService
from core.narrative.graph.narrative_graph import NarrativeGraphEngine

router = APIRouter(prefix="/v1/narrative", tags=["Narrative Core"])

# ── Universes ─────────────────────────────────────────────────────────────────
@router.post("/universes", response_model=UniverseResponseDTO, status_code=status.HTTP_201_CREATED)
def create_universe(dto: UniverseCreateDTO, db: Session = Depends(get_db)):
    service = UniverseService(db)
    return service.create_universe(dto)

@router.get("/universes/{universe_id}", response_model=UniverseResponseDTO)
def get_universe(universe_id: uuid.UUID, db: Session = Depends(get_db)):
    service = UniverseService(db)
    res = service.get_universe(universe_id)
    if not res:
        raise HTTPException(status_code=404, detail="Universe not found.")
    return res

@router.get("/universes", response_model=List[UniverseResponseDTO])
def list_universes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = UniverseService(db)
    return service.list_universes(skip=skip, limit=limit)

# ── Characters ────────────────────────────────────────────────────────────────
@router.post("/characters", response_model=CharacterResponseDTO, status_code=status.HTTP_201_CREATED)
def create_character(dto: CharacterCreateDTO, db: Session = Depends(get_db)):
    service = CharacterService(db)
    return service.create_character(dto)

@router.get("/universes/{universe_id}/characters", response_model=List[CharacterResponseDTO])
def list_characters_by_universe(universe_id: uuid.UUID, db: Session = Depends(get_db)):
    service = CharacterService(db)
    return service.list_by_universe(universe_id)

# ── Relationships ─────────────────────────────────────────────────────────────
@router.post("/relationships", response_model=RelationshipResponseDTO, status_code=status.HTTP_201_CREATED)
def create_relationship(dto: RelationshipCreateDTO, db: Session = Depends(get_db)):
    service = RelationshipService(db)
    return service.create_relationship(dto)

# ── Locations ─────────────────────────────────────────────────────────────────
@router.post("/locations", response_model=LocationResponseDTO, status_code=status.HTTP_201_CREATED)
def create_location(dto: LocationCreateDTO, db: Session = Depends(get_db)):
    service = LocationService(db)
    return service.create_location(dto)

# ── Organizations ─────────────────────────────────────────────────────────────
@router.post("/organizations", response_model=OrganizationResponseDTO, status_code=status.HTTP_201_CREATED)
def create_organization(dto: OrganizationCreateDTO, db: Session = Depends(get_db)):
    service = OrganizationService(db)
    return service.create_organization(dto)

# ── Story Arcs ────────────────────────────────────────────────────────────────
@router.post("/story-arcs", response_model=StoryArcResponseDTO, status_code=status.HTTP_201_CREATED)
def create_story_arc(dto: StoryArcCreateDTO, db: Session = Depends(get_db)):
    service = StoryArcService(db)
    return service.create_story_arc(dto)

# ── Timeline Events ───────────────────────────────────────────────────────────
@router.post("/timeline-events", response_model=TimelineEventResponseDTO, status_code=status.HTTP_201_CREATED)
def create_timeline_event(dto: TimelineEventCreateDTO, db: Session = Depends(get_db)):
    service = TimelineService(db)
    return service.create_timeline_event(dto)

# ── Seasons, Episodes & Scenes ────────────────────────────────────────────────
@router.post("/seasons", response_model=SeasonResponseDTO, status_code=status.HTTP_201_CREATED)
def create_season(dto: SeasonCreateDTO, db: Session = Depends(get_db)):
    service = SeasonService(db)
    return service.create_season(dto)

@router.post("/episodes", response_model=EpisodeResponseDTO, status_code=status.HTTP_201_CREATED)
def create_episode(dto: EpisodeCreateDTO, db: Session = Depends(get_db)):
    service = EpisodeService(db)
    return service.create_episode(dto)

@router.post("/scenes", response_model=SceneResponseDTO, status_code=status.HTTP_201_CREATED)
def create_scene(dto: SceneCreateDTO, db: Session = Depends(get_db)):
    service = SceneService(db)
    return service.create_scene(dto)

# ── Graph ─────────────────────────────────────────────────────────────────────
@router.get("/universes/{universe_id}/graph")
def get_universe_graph(universe_id: uuid.UUID, db: Session = Depends(get_db)):
    graph_engine = NarrativeGraphEngine(db)
    return graph_engine.build_universe_graph(universe_id)
