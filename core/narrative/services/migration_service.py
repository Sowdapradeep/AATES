import logging
from typing import Any, Dict
from sqlalchemy.orm import Session
from core.database.models import SystemState
from core.narrative.services.universe_service import UniverseService
from core.narrative.services.character_service import CharacterService
from core.narrative.services.location_service import LocationService
from core.narrative.services.organization_service import OrganizationService
from core.narrative.services.timeline_service import TimelineService
from core.narrative.dto.narrative_dto import (
    UniverseCreateDTO, CharacterCreateDTO, LocationCreateDTO, OrganizationCreateDTO, TimelineEventCreateDTO
)

logger = logging.getLogger("narrative_migration")

class NarrativeMigrationService:
    """
    Migrates legacy JSON bibles stored inside SystemState into Narrative Core ORM entities.
    Enables zero-downtime, gradual migration.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.univ_service = UniverseService(db)
        self.char_service = CharacterService(db)
        self.loc_service = LocationService(db)
        self.org_service = OrganizationService(db)
        self.time_service = TimelineService(db)

    def migrate_bible(self, universe_id: str) -> Dict[str, Any]:
        state_key = f"bible-{universe_id}"
        state = self.db.query(SystemState).filter(SystemState.state_key == state_key).first()
        if not state or not state.state_value:
            return {"status": "skipped", "reason": f"No SystemState found for key '{state_key}'."}

        bible_data = state.state_value
        meta = bible_data.get("universe", {}).get("metadata", {})
        univ_name = meta.get("name", f"Universe-{universe_id}")

        # 1. Create or get Universe
        u_dto = self.univ_service.create_universe(UniverseCreateDTO(
            name=univ_name,
            description=f"Migrated from SystemState {state_key}",
            genre=meta.get("genre", "Drama"),
            core_themes=meta.get("themes", []),
            world_rules=meta.get("rules", bible_data.get("rules", []))
        ))
        u_id = u_dto.id

        # 2. Migrate Characters
        chars_migrated = 0
        for name, c_data in bible_data.get("characters", {}).items():
            if isinstance(c_data, dict):
                self.char_service.create_character(CharacterCreateDTO(
                    universe_id=u_id,
                    name=c_data.get("name", name),
                    role=c_data.get("role", "protagonist"),
                    archetype=c_data.get("archetype"),
                    personality_traits=c_data.get("personality_traits", []),
                    background_lore=c_data.get("background_lore"),
                    motivation=c_data.get("motivation"),
                    slang_preference=c_data.get("slang_preference", "chennai"),
                    attire_note=c_data.get("attire_note")
                ))
                chars_migrated += 1

        # 3. Migrate Locations
        locs_migrated = 0
        for name, l_data in bible_data.get("locations", {}).items():
            if isinstance(l_data, dict):
                self.loc_service.create_location(LocationCreateDTO(
                    universe_id=u_id,
                    name=l_data.get("name", name),
                    description=l_data.get("description"),
                    key_features=l_data.get("key_features", []),
                    mood=l_data.get("mood", "Neutral"),
                    cultural_context=l_data.get("cultural_context")
                ))
                locs_migrated += 1

        # 4. Migrate Organizations
        orgs_migrated = 0
        for name, o_data in bible_data.get("organizations", {}).items():
            if isinstance(o_data, dict):
                self.org_service.create_organization(OrganizationCreateDTO(
                    universe_id=u_id,
                    name=o_data.get("name", name),
                    faction_type=o_data.get("faction_type", "Guild"),
                    objectives=o_data.get("objectives", []),
                    influence_level=o_data.get("influence_level", 0.5)
                ))
                orgs_migrated += 1

        # 5. Migrate Plot Points
        beats_migrated = 0
        for idx, beat in enumerate(bible_data.get("plot_points", [])):
            if isinstance(beat, dict):
                self.time_service.create_timeline_event(TimelineEventCreateDTO(
                    universe_id=u_id,
                    beat_number=beat.get("beat_number", idx + 1),
                    title=beat.get("event", f"Beat {idx+1}"),
                    event_type="beat",
                    emotional_charge=beat.get("emotional_charge", "tense"),
                    twist_introduced=beat.get("twist_introduced"),
                    foreshadowing_clues=beat.get("foreshadowing_clues", [])
                ))
                beats_migrated += 1

        return {
            "status": "success",
            "universe_id": str(u_id),
            "characters_migrated": chars_migrated,
            "locations_migrated": locs_migrated,
            "organizations_migrated": orgs_migrated,
            "beats_migrated": beats_migrated
        }
