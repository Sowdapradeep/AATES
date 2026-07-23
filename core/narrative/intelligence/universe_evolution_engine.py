import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from core.narrative.services.universe_service import UniverseService
from core.narrative.services.organization_service import OrganizationService
from core.narrative.services.location_service import LocationService
from core.narrative.dto.narrative_dto import UniverseUpdateDTO
from core.narrative.intelligence.bedrock_client import bedrock_intelligence

class UniverseEvolutionEngine:
    """
    7. Universe Evolution Engine.
    Drives autonomous macro evolution of cultures, organizations, politics, technology,
    economy, and history over time.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.univ_service = UniverseService(db)
        self.org_service = OrganizationService(db)
        self.loc_service = LocationService(db)

    def evolve_universe(self, universe_id: uuid.UUID | str, episode_count_elapsed: int) -> Dict[str, Any]:
        univ = self.univ_service.get_universe(universe_id)
        if not univ:
            return {"status": "error", "message": "Universe not found."}

        system_prompt = (
            "You are the AATES Universe Evolution Engine. "
            "Formulate long-term world evolution across culture, technology, politics, economy, and organization dynamics."
        )
        user_prompt = (
            f"Universe Name: {univ.name}\n"
            f"Genre: {univ.genre}\n"
            f"Core Themes: {univ.core_themes}\n"
            f"Current World Rules: {univ.world_rules}\n"
            f"Episodes Elapsed: {episode_count_elapsed}\n\n"
            "Return JSON with fields: 'new_world_rules' (list of strings), "
            "'evolved_themes' (list of strings), 'cultural_shift_notes', 'political_shift_notes'."
        )

        res = bedrock_intelligence.reason(user_prompt, system_instruction=system_prompt)
        parsed = {}
        try:
            parsed = json.loads(res)
        except Exception:
            parsed = {
                "new_world_rules": (univ.world_rules or []) + ["Industrial expansion challenges agricultural heritage."],
                "evolved_themes": (univ.core_themes or []) + ["Modernization vs Tradition"],
                "cultural_shift_notes": "Community traditions adapting to urban migration",
                "political_shift_notes": "Local village councils forming united negotiation fronts"
            }

        new_rules = list(set((univ.world_rules or []) + parsed.get("new_world_rules", [])))
        new_themes = list(set((univ.core_themes or []) + parsed.get("evolved_themes", [])))

        meta = univ.metadata_json or {}
        meta["cultural_shift"] = parsed.get("cultural_shift_notes")
        meta["political_shift"] = parsed.get("political_shift_notes")
        meta["last_evolved_at_episode"] = episode_count_elapsed

        updated = self.univ_service.update_universe(
            universe_id,
            UniverseUpdateDTO(
                world_rules=new_rules,
                core_themes=new_themes
            )
        )

        return {
            "universe_id": str(universe_id),
            "universe_name": univ.name,
            "episodes_elapsed": episode_count_elapsed,
            "evolved_rules": new_rules,
            "evolved_themes": new_themes,
            "cultural_shift": meta["cultural_shift"],
            "political_shift": meta["political_shift"]
        }
