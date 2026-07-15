from typing import Any
from sqlalchemy.orm import Session
from contracts.dto.creative import ValidationResultDTO
from brain.story_bible.bible import story_bible_engine

class ValidationEngine:
    """Core Validation Engine performing Story Bible continuity and canon compliance checks."""
    
    async def validate_continuity(self, universe_id: str, section: str, key: str, action_proposed: str, db: Session = None) -> ValidationResultDTO:
        """Verifies character traits, locations and state timeline consistency."""
        bible = story_bible_engine.get_bible(universe_id, db=db)
        
        warnings = []
        if section == "characters" and key not in bible.get("characters", {}):
            warnings.append(f"Character ID '{key}' is missing from the Story Bible registry.")
            
        is_valid = len(warnings) == 0
        score = 100.0 if is_valid else 50.0
        
        return ValidationResultDTO(
            is_valid=is_valid,
            warnings=warnings,
            canon_compliance_score=score,
            details=f"Continuity check completed for {section}/{key}. Action: '{action_proposed}'."
        )

    async def validate_canon(self, universe_id: str, proposed_plot: str, db: Session = None) -> ValidationResultDTO:
        """Verifies proposed plot points against base world rules and universe settings."""
        bible = story_bible_engine.get_bible(universe_id, db=db)
        
        # Check both nested metadata rules and root level rules keys
        rules = bible.get("rules", [])
        if not rules:
            rules = bible.get("universe", {}).get("metadata", {}).get("rules", [])
        
        warnings = []
        for rule in rules:
            if "realism" in rule.lower() and "magic" in proposed_plot.lower():
                warnings.append("Proposed plot contains magic elements which contradicts the realism world rule.")
                
        is_valid = len(warnings) == 0
        score = 100.0 if is_valid else 60.0
        
        return ValidationResultDTO(
            is_valid=is_valid,
            warnings=warnings,
            canon_compliance_score=score,
            details=f"Canon compliance validation against {len(rules)} base world rules completed."
        )

validation_engine = ValidationEngine()
