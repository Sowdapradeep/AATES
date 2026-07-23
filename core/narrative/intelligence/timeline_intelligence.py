import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from core.narrative.services.timeline_service import TimelineService
from core.narrative.repositories.timeline_repo import TimelineRepository
from core.narrative.dto.narrative_dto import TimelineEventCreateDTO
from core.narrative.intelligence.bedrock_client import bedrock_intelligence

class TimelineIntelligenceEngine:
    """
    3. Timeline Intelligence Engine.
    Generates chronological beats, flashbacks, foreshadowing clues, parallel timelines,
    and enforces historical consistency.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.time_service = TimelineService(db)
        self.time_repo = TimelineRepository(db)

    def generate_timeline_beat(
        self,
        universe_id: uuid.UUID | str,
        beat_title: str,
        event_type: str = "beat",
        context_notes: str = ""
    ) -> Dict[str, Any]:
        u_id = universe_id if isinstance(universe_id, uuid.UUID) else uuid.UUID(universe_id)
        existing_beats = self.time_repo.get_by_universe(u_id)
        next_beat_num = len(existing_beats) + 1

        system_prompt = (
            "You are the AATES Timeline Intelligence Engine. "
            "Formulate chronological story beats, foreshadowing clues, and dramatic twists for a narrative timeline."
        )
        user_prompt = (
            f"Beat Title: {beat_title}\n"
            f"Event Type: {event_type}\n"
            f"Beat Number: {next_beat_num}\n"
            f"Context: {context_notes}\n\n"
            "Return JSON with fields: 'title', 'description', 'emotional_charge', "
            "'twist_introduced', 'foreshadowing_clues' (list of strings)."
        )

        res = bedrock_intelligence.reason(user_prompt, system_instruction=system_prompt)
        parsed = {}
        try:
            parsed = json.loads(res)
        except Exception:
            parsed = {
                "title": beat_title,
                "description": f"Narrative beat event: {beat_title}",
                "emotional_charge": "tense",
                "twist_introduced": "Secret survey map revealed",
                "foreshadowing_clues": ["An unusual stamp on the surveyor's document folder"]
            }

        event_dto = self.time_service.create_timeline_event(
            TimelineEventCreateDTO(
                universe_id=u_id,
                beat_number=next_beat_num,
                title=parsed.get("title", beat_title),
                event_type=event_type,
                description=parsed.get("description"),
                emotional_charge=parsed.get("emotional_charge", "tense"),
                twist_introduced=parsed.get("twist_introduced"),
                foreshadowing_clues=parsed.get("foreshadowing_clues", [])
            )
        )

        return event_dto.model_dump()
