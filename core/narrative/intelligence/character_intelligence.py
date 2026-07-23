import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from core.narrative.services.character_service import CharacterService
from core.narrative.repositories.character_repo import CharacterRepository
from core.narrative.intelligence.bedrock_client import bedrock_intelligence

class CharacterIntelligenceEngine:
    """
    1. Character Intelligence Engine.
    Executes autonomous AI reasoning over Character ORM entities.
    Tracks goals, fears, motivations, emotional states, and updates Character state in DB.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.char_service = CharacterService(db)
        self.char_repo = CharacterRepository(db)

    def evaluate_character_growth(self, character_id: uuid.UUID | str, recent_events: List[str]) -> Dict[str, Any]:
        """
        Reasons over a character's recent experiences and updates their personality traits and state.
        """
        c_id = character_id if isinstance(character_id, uuid.UUID) else uuid.UUID(character_id)
        char = self.char_repo.get_by_id(c_id)
        if not char:
            return {"status": "error", "message": "Character not found."}

        system_prompt = (
            "You are the AATES Character Intelligence Engine. "
            "Analyze character backstory, personality, and recent story events to determine character evolution."
        )
        user_prompt = (
            f"Character Name: {char.name}\n"
            f"Role: {char.role}\n"
            f"Archetype: {char.archetype}\n"
            f"Current Personality: {char.personality_traits}\n"
            f"Motivation: {char.motivation}\n"
            f"Recent Events: {recent_events}\n\n"
            "Return a JSON object with fields: 'emotional_state', 'updated_motivation', "
            "'new_personality_traits' (list of strings), 'decision_choice', 'growth_notes'."
        )

        reasoning_res = bedrock_intelligence.reason(user_prompt, system_instruction=system_prompt)
        
        parsed_data = {}
        try:
            parsed_data = json.loads(reasoning_res)
        except Exception:
            parsed_data = {}

        emotional_state = parsed_data.get("emotional_state") or "determined"
        updated_motivation = parsed_data.get("updated_motivation") or char.motivation or "Protect community interests"
        incoming_traits = parsed_data.get("new_personality_traits") or ["Resolute"]
        decision_choice = parsed_data.get("decision_choice") or "Stand firm against survey demands"
        growth_notes = parsed_data.get("growth_notes") or "Character embraced leadership responsibility."

        new_traits = list(set((char.personality_traits or []) + incoming_traits))

        # Update DB State
        meta = char.metadata_json or {}
        meta["emotional_state"] = emotional_state
        meta["latest_decision"] = decision_choice
        meta["growth_notes"] = growth_notes

        self.char_repo.update(
            char.id,
            motivation=updated_motivation,
            personality_traits=new_traits,
            metadata_json=meta
        )

        return {
            "character_id": str(char.id),
            "character_name": char.name,
            "emotional_state": emotional_state,
            "updated_motivation": updated_motivation,
            "personality_traits": new_traits,
            "decision": decision_choice
        }
