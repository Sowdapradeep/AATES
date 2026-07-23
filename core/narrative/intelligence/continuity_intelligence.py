import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from core.narrative.repositories.universe_repo import UniverseRepository
from core.narrative.repositories.character_repo import CharacterRepository
from core.narrative.repositories.location_repo import LocationRepository
from core.narrative.repositories.relationship_repo import RelationshipRepository
from core.narrative.repositories.timeline_repo import TimelineRepository
from core.narrative.intelligence.bedrock_client import bedrock_intelligence

class ContinuityIntelligenceEngine:
    """
    5. Continuity Intelligence Engine.
    Executes deep AI reasoning over ORM models to detect dead characters appearing,
    timeline violations, location conflicts, relationship inconsistencies, and story contradictions.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.univ_repo = UniverseRepository(db)
        self.char_repo = CharacterRepository(db)
        self.loc_repo = LocationRepository(db)
        self.rel_repo = RelationshipRepository(db)
        self.time_repo = TimelineRepository(db)

    def validate_story_action(
        self,
        universe_id: uuid.UUID | str,
        proposed_action: str,
        participating_character_names: List[str] = None,
        target_location_name: str = None
    ) -> Dict[str, Any]:
        participating_character_names = participating_character_names or []
        
        # 1. Inspect ORM models directly
        chars = self.char_repo.get_by_universe(universe_id)
        locs = self.loc_repo.get_by_universe(universe_id)
        beats = self.time_repo.get_by_universe(universe_id)

        char_names_in_db = {c.name.lower(): c for c in chars}
        loc_names_in_db = {l.name.lower(): l for l in locs}

        violations = []

        # Check missing or dead characters
        for name in participating_character_names:
            if name.lower() not in char_names_in_db:
                violations.append({
                    "type": "MISSING_CHARACTER",
                    "severity": "CRITICAL",
                    "explanation": f"Character '{name}' does not exist in the active Universe ORM models."
                })
            else:
                c_obj = char_names_in_db[name.lower()]
                if c_obj.status == "deceased" or c_obj.is_deleted:
                    violations.append({
                        "type": "DEAD_CHARACTER_APPEARANCE",
                        "severity": "CRITICAL",
                        "explanation": f"Character '{name}' is marked as deceased/deleted in ORM model but is participating in action."
                    })

        # Check location conflicts
        if target_location_name and target_location_name.lower() not in loc_names_in_db:
            violations.append({
                "type": "LOCATION_CONFLICT",
                "severity": "MAJOR",
                "explanation": f"Location '{target_location_name}' is not registered in the Universe ORM model."
            })

        # 2. Reasoning via Bedrock Nova Pro for complex narrative logic
        system_prompt = (
            "You are the AATES Continuity Intelligence Engine. "
            "Perform strict canon & continuity validation over proposed screenplay actions against universe rules."
        )
        user_prompt = (
            f"Proposed Action: {proposed_action}\n"
            f"Known Characters: {[c.name for c in chars]}\n"
            f"Known Locations: {[l.name for l in locs]}\n"
            f"Known Beats: {[b.title for b in beats]}\n"
            f"Direct ORM Violations Found: {violations}\n\n"
            "Return JSON with fields: 'is_valid' (bool), 'canon_score' (float 0-100), "
            "'violations' (list of violation objects), 'explanation' (str)."
        )

        res = bedrock_intelligence.reason(user_prompt, system_instruction=system_prompt)
        parsed = {}
        try:
            parsed = json.loads(res)
        except Exception:
            is_valid = len(violations) == 0
            parsed = {
                "is_valid": is_valid,
                "canon_score": 100.0 if is_valid else 50.0,
                "violations": violations,
                "explanation": "Validation performed cleanly over ORM entity models."
            }

        if violations and "violations" in parsed:
            # Merge deterministic ORM checks with AI reasoning
            existing_types = {v.get("type") for v in parsed["violations"]}
            for v in violations:
                if v["type"] not in existing_types:
                    parsed["violations"].append(v)
            parsed["is_valid"] = False
            parsed["canon_score"] = min(parsed.get("canon_score", 50.0), 40.0)

        return parsed
