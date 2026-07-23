import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from core.narrative.repositories.story_arc_repo import StoryArcRepository
from core.narrative.repositories.season_repo import SeasonRepository
from core.narrative.repositories.episode_repo import EpisodeRepository
from core.narrative.services.story_arc_service import StoryArcService
from core.narrative.dto.narrative_dto import StoryArcCreateDTO
from core.narrative.intelligence.bedrock_client import bedrock_intelligence

class StoryArcIntelligenceEngine:
    """
    4. Story Arc Intelligence Engine.
    Generates main conflicts, subplots, episode arcs, season arcs, and automatically
    detects unfinished narrative arcs.
    """
    def __init__(self, db: Session) -> None:
        self.db = db
        self.arc_repo = StoryArcRepository(db)
        self.arc_service = StoryArcService(db)
        self.season_repo = SeasonRepository(db)
        self.episode_repo = EpisodeRepository(db)

    def formulate_story_arc(self, universe_id: uuid.UUID | str, theme: str, target_conflict: str) -> Dict[str, Any]:
        u_id = universe_id if isinstance(universe_id, uuid.UUID) else uuid.UUID(universe_id)
        system_prompt = "You are the AATES Story Arc Intelligence Engine. Formulate macro themes, climax predictions, and resolution paths."
        user_prompt = f"Universe ID: {u_id}\nTheme: {theme}\nTarget Conflict: {target_conflict}\n\nReturn JSON with fields: 'title', 'major_theme', 'climax_prediction', 'resolution_path'."

        res = bedrock_intelligence.reason(user_prompt, system_instruction=system_prompt)
        parsed = {}
        try:
            parsed = json.loads(res)
        except Exception:
            parsed = {
                "title": f"Arc of {theme}",
                "major_theme": theme,
                "climax_prediction": "Climactic community tribunal confrontation",
                "resolution_path": "Re-establishment of ancestral community rights"
            }

        dto = self.arc_service.create_story_arc(
            StoryArcCreateDTO(
                universe_id=u_id,
                title=parsed.get("title", f"Arc of {theme}"),
                major_theme=parsed.get("major_theme", theme),
                climax_prediction=parsed.get("climax_prediction"),
                resolution_path=parsed.get("resolution_path")
            )
        )
        return dto.model_dump()

    def detect_unfinished_arcs(self, universe_id: uuid.UUID | str) -> List[Dict[str, Any]]:
        u_id = universe_id if isinstance(universe_id, uuid.UUID) else uuid.UUID(universe_id)
        arcs = self.arc_repo.get_by_universe(u_id)
        unfinished = []
        for arc in arcs:
            if arc.status != "resolved":
                unfinished.append({
                    "arc_id": str(arc.id),
                    "title": arc.title,
                    "major_theme": arc.major_theme,
                    "climax_prediction": arc.climax_prediction,
                    "status": arc.status
                })
        return unfinished
