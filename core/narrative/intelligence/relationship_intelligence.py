import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from core.narrative.services.relationship_service import RelationshipService
from core.narrative.repositories.relationship_repo import RelationshipRepository
from core.narrative.repositories.character_repo import CharacterRepository
from core.narrative.intelligence.bedrock_client import bedrock_intelligence

class RelationshipIntelligenceEngine:
    """
    2. Relationship Intelligence Engine.
    Tracks and automatically evolves relationships (friendships, love, betrayal, trust,
    respect, fear, rivalry, loyalty) and updates tension scores in the database.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.rel_service = RelationshipService(db)
        self.rel_repo = RelationshipRepository(db)
        self.char_repo = CharacterRepository(db)

    def evolve_relationship(
        self,
        char_a_id: uuid.UUID | str,
        char_b_id: uuid.UUID | str,
        interaction_event: str
    ) -> Dict[str, Any]:
        ca_id = char_a_id if isinstance(char_a_id, uuid.UUID) else uuid.UUID(char_a_id)
        cb_id = char_b_id if isinstance(char_b_id, uuid.UUID) else uuid.UUID(char_b_id)

        char_a = self.char_repo.get_by_id(ca_id)
        char_b = self.char_repo.get_by_id(cb_id)
        if not char_a or not char_b:
            return {"status": "error", "message": "One or both characters not found."}

        rel = self.rel_repo.get_between_characters(ca_id, cb_id)
        curr_type = rel.relationship_type if rel else "rivalry"
        curr_tension = rel.tension_level if rel else 0.5

        system_prompt = (
            "You are the AATES Relationship Intelligence Engine. "
            "Analyze character interactions to evolve relationship types, tension scores, and emotional trust levels."
        )
        user_prompt = (
            f"Character A: {char_a.name} ({char_a.role})\n"
            f"Character B: {char_b.name} ({char_b.role})\n"
            f"Current Relationship Type: {curr_type}\n"
            f"Current Tension Level: {curr_tension}\n"
            f"Interaction Event: {interaction_event}\n\n"
            "Return JSON with fields: 'relationship_type', 'new_tension_level' (float 0.0 to 1.0), "
            "'emotional_shift', 'history_summary'."
        )

        res = bedrock_intelligence.reason(user_prompt, system_instruction=system_prompt)
        parsed = {}
        try:
            parsed = json.loads(res)
        except Exception:
            parsed = {
                "relationship_type": curr_type,
                "new_tension_level": min(1.0, curr_tension + 0.15),
                "emotional_shift": "Increased friction over land rights",
                "history_summary": f"Tension escalated during {interaction_event}"
            }

        new_tension = float(parsed.get("new_tension_level", curr_tension))
        new_type = parsed.get("relationship_type", curr_type)
        history = f"{rel.history_notes if rel and rel.history_notes else ''}\nEvent: {interaction_event} -> {parsed.get('emotional_shift', '')}".strip()

        if rel:
            updated = self.rel_repo.update(
                rel.id,
                relationship_type=new_type,
                tension_level=new_tension,
                history_notes=history
            )
            rel_id = str(updated.id)
        else:
            created = self.rel_repo.create(
                character_a_id=char_a.id,
                character_b_id=char_b.id,
                relationship_type=new_type,
                tension_level=new_tension,
                history_notes=history
            )
            rel_id = str(created.id)

        return {
            "relationship_id": rel_id,
            "character_a": char_a.name,
            "character_b": char_b.name,
            "relationship_type": new_type,
            "tension_level": new_tension,
            "emotional_shift": parsed.get("emotional_shift")
        }
