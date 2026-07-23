from typing import List
from sqlalchemy.orm import Session
from core.narrative.services.universe_service import UniverseService
from core.narrative.services.character_service import CharacterService

class NarrativeValidator:
    """
    Validates narrative integrity, character relationships, and canon compliance.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.universe_service = UniverseService(db)
        self.character_service = CharacterService(db)

    def validate_canon_rules(self, universe_id: str, proposed_plot: str) -> dict[str, Any]:
        univ = self.universe_service.get_universe(universe_id)
        if not univ:
            return {"is_valid": False, "warnings": ["Universe not found in persistence layer."], "score": 0.0}
        
        rules = univ.world_rules or []
        warnings = []
        for rule in rules:
            if "realism" in rule.lower() and "magic" in proposed_plot.lower():
                warnings.append("Proposed plot violates world realism rule.")
                
        is_valid = len(warnings) == 0
        return {
            "is_valid": is_valid,
            "warnings": warnings,
            "canon_compliance_score": 100.0 if is_valid else 60.0,
            "rule_count_evaluated": len(rules)
        }
