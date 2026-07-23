"""
Narrative Core v1 Package.
Provides permanent ORM persistence, repositories, services, DTOs, events, and API endpoints
for the AATES Creative Intelligence Platform.
"""

from core.narrative.models import (
    NarrativeBaseModel, Universe, World, Character, Relationship, Location,
    Organization, StoryArc, TimelineEvent, Season, Episode, Scene
)
from core.narrative.repositories import (
    UniverseRepository, CharacterRepository, RelationshipRepository, LocationRepository,
    OrganizationRepository, StoryArcRepository, TimelineRepository, SeasonRepository,
    EpisodeRepository, SceneRepository
)
from core.narrative.services import (
    UniverseService, CharacterService, RelationshipService, LocationService,
    OrganizationService, StoryArcService, TimelineService, SeasonService,
    EpisodeService, SceneService
)

__all__ = [
    "NarrativeBaseModel", "Universe", "World", "Character", "Relationship", "Location",
    "Organization", "StoryArc", "TimelineEvent", "Season", "Episode", "Scene",
    "UniverseRepository", "CharacterRepository", "RelationshipRepository", "LocationRepository",
    "OrganizationRepository", "StoryArcRepository", "TimelineRepository", "SeasonRepository",
    "EpisodeRepository", "SceneRepository",
    "UniverseService", "CharacterService", "RelationshipService", "LocationService",
    "OrganizationService", "StoryArcService", "TimelineService", "SeasonService",
    "EpisodeService", "SceneService",
]
