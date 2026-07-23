import uuid
import datetime
import logging
from typing import Any
from sqlalchemy.orm import Session
from core.database.session import SessionLocal
from core.database.models import SystemState
from core.narrative.services.universe_service import UniverseService
from core.narrative.services.character_service import CharacterService
from core.narrative.services.location_service import LocationService
from core.narrative.services.organization_service import OrganizationService
from core.narrative.services.timeline_service import TimelineService
from core.narrative.dto.narrative_dto import (
    UniverseCreateDTO, CharacterCreateDTO, LocationCreateDTO, OrganizationCreateDTO, TimelineEventCreateDTO
)

logger = logging.getLogger("story_bible_engine")

class StoryBibleEngine:
    """
    Refactored StoryBibleEngine supporting Narrative Core v1.
    Reads progressively from permanent Narrative ORM models with automatic fallback to SystemState.
    Performs dual-write to sync legacy SystemState JSON state with Narrative ORM models.
    """

    def get_bible(self, universe_id: str, db: Session = None) -> dict[str, Any]:
        """
        Retrieves the active story bible state for a given universe.
        Progressively reads from Narrative ORM tables, falling back to SystemState if not yet populated.
        """
        session = db or SessionLocal()
        try:
            # 1. Attempt reading from Narrative Core ORM entities
            univ_service = UniverseService(session)
            char_service = CharacterService(session)
            loc_service = LocationService(session)
            org_service = OrganizationService(session)
            time_service = TimelineService(session)

            univ_dto = None
            try:
                # Try finding universe by UUID or Name
                if len(universe_id) == 36 and "-" in universe_id:
                    univ_dto = univ_service.get_universe(universe_id)
            except Exception:
                pass

            if univ_dto:
                # Build Bible dictionary dynamically from ORM entities
                chars = char_service.list_by_universe(univ_dto.id)
                locs = loc_service.list_by_universe(univ_dto.id)
                orgs = org_service.list_by_universe(univ_dto.id)
                beats = time_service.list_by_universe(univ_dto.id)

                chars_dict = {c.name: c.model_dump() for c in chars}
                locs_dict = {l.name: l.model_dump() for l in locs}
                orgs_dict = {o.name: o.model_dump() for o in orgs}
                timeline_list = [b.model_dump() for b in beats]

                return {
                    "universe": {
                        "metadata": {
                            "name": univ_dto.name,
                            "genre": univ_dto.genre,
                            "themes": univ_dto.core_themes,
                            "rules": univ_dto.world_rules
                        }
                    },
                    "characters": chars_dict,
                    "locations": locs_dict,
                    "organizations": orgs_dict,
                    "timeline": timeline_list,
                    "rules": univ_dto.world_rules or [],
                    "version": univ_dto.version
                }

            # 2. Fallback to SystemState table
            state = session.query(SystemState).filter(SystemState.state_key == f"bible-{universe_id}").first()
            return state.state_value if state else {
                "characters": {},
                "locations": {},
                "timeline": [],
                "rules": [],
                "version": 1
            }
        except Exception as e:
            logger.warning(f"Error reading from Narrative Core ORM: {str(e)}. Falling back to SystemState.")
            state = session.query(SystemState).filter(SystemState.state_key == f"bible-{universe_id}").first()
            return state.state_value if state else {
                "characters": {},
                "locations": {},
                "timeline": [],
                "rules": [],
                "version": 1
            }
        finally:
            if not db:
                session.close()

    def update_bible(
        self,
        universe_id: str,
        section: str,
        key: str,
        new_value: Any,
        author: str,
        reason: str,
        workflow_id: str | None = None,
        db: Session = None
    ) -> None:
        """
        Applies a versioned change, logs audit trails, and dual-writes to both SystemState and Narrative ORM models.
        """
        session = db or SessionLocal()
        try:
            state_key = f"bible-{universe_id}"
            state = session.query(SystemState).filter(SystemState.state_key == state_key).first()

            bible_data = state.state_value if state else {
                "characters": {},
                "locations": {},
                "timeline": [],
                "rules": [],
                "version": 1
            }

            # Fetch previous value for delta tracking
            if isinstance(bible_data.get(section), dict):
                prev_value = bible_data[section].get(key)
            elif isinstance(bible_data.get(section), list):
                prev_value = f"list-index-{key}"
            else:
                prev_value = None

            # Write new value to SystemState dictionary
            if isinstance(bible_data.get(section), dict):
                bible_data[section][key] = new_value
            elif isinstance(bible_data.get(section), list):
                bible_data[section].append(new_value)
            else:
                bible_data[section] = {key: new_value}

            bible_data["version"] = bible_data.get("version", 1) + 1

            if not state:
                state = SystemState(state_key=state_key, state_value=bible_data)
                session.add(state)
            else:
                state.state_value = {}
                session.flush()
                state.state_value = bible_data
            session.flush()

            # Generate auditable change record in SystemState history
            history_key = f"bible-history-{universe_id}"
            history_state = session.query(SystemState).filter(SystemState.state_key == history_key).first()

            audit_record = {
                "change_id": str(uuid.uuid4()),
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "authoring_agent": author,
                "reason": reason,
                "section": section,
                "key": key,
                "previous_value": prev_value,
                "new_value": new_value,
                "workflow_id": workflow_id
            }

            if not history_state:
                history_state = SystemState(state_key=history_key, state_value=[audit_record])
                session.add(history_state)
            else:
                hist_list = list(history_state.state_value)
                hist_list.append(audit_record)
                history_state.state_value = []
                session.flush()
                history_state.state_value = hist_list

            # ── Dual-write into Narrative Core ORM Tables ─────────────────────
            self._sync_to_narrative_orm(session, universe_id, section, key, new_value, author)

            if not db:
                session.commit()
        except Exception as e:
            if not db:
                session.rollback()
            raise e
        finally:
            if not db:
                session.close()

    def _sync_to_narrative_orm(
        self,
        session: Session,
        universe_id: str,
        section: str,
        key: str,
        value: Any,
        author: str
    ) -> None:
        """Internal helper attempting dual-write into Narrative Core ORM entities."""
        try:
            univ_service = UniverseService(session)
            char_service = CharacterService(session)
            loc_service = LocationService(session)
            org_service = OrganizationService(session)
            time_service = TimelineService(session)

            # Ensure Universe ORM entity exists
            valid_uuid = None
            try:
                if len(universe_id) == 36 and "-" in universe_id:
                    valid_uuid = uuid.UUID(universe_id)
            except Exception:
                pass

            if not valid_uuid:
                u_res = univ_service.create_universe(UniverseCreateDTO(
                    name=f"Universe-{universe_id}",
                    description=f"Auto-synced universe for {universe_id}",
                    created_by=author
                ))
                valid_uuid = u_res.id

            # Sync Section Items
            if section == "characters" and isinstance(value, dict):
                char_service.create_character(CharacterCreateDTO(
                    universe_id=valid_uuid,
                    name=value.get("name", key),
                    role=value.get("role", "protagonist"),
                    archetype=value.get("archetype"),
                    personality_traits=value.get("personality_traits", []),
                    background_lore=value.get("background_lore", ""),
                    motivation=value.get("motivation", ""),
                    slang_preference=value.get("slang_preference", "chennai"),
                    attire_note=value.get("attire_note", "")
                ))
            elif section == "locations" and isinstance(value, dict):
                loc_service.create_location(LocationCreateDTO(
                    universe_id=valid_uuid,
                    name=value.get("name", key),
                    description=value.get("description", ""),
                    key_features=value.get("key_features", []),
                    mood=value.get("mood", "Neutral"),
                    cultural_context=value.get("cultural_context", "")
                ))
            elif section == "organizations" and isinstance(value, dict):
                org_service.create_organization(OrganizationCreateDTO(
                    universe_id=valid_uuid,
                    name=value.get("name", key),
                    faction_type=value.get("faction_type", "Guild"),
                    objectives=value.get("objectives", []),
                    influence_level=value.get("influence_level", 0.5)
                ))
            elif section == "plot_points" and isinstance(value, dict):
                time_service.create_timeline_event(TimelineEventCreateDTO(
                    universe_id=valid_uuid,
                    beat_number=value.get("beat_number", 1),
                    title=value.get("event", key),
                    event_type="beat",
                    emotional_charge=value.get("emotional_charge", "tense"),
                    twist_introduced=value.get("twist_introduced"),
                    foreshadowing_clues=value.get("foreshadowing_clues", [])
                ))
        except Exception as sync_err:
            logger.warning(f"Dual-write to Narrative ORM skipped: {str(sync_err)}")

story_bible_engine = StoryBibleEngine()
