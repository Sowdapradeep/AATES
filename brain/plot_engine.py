from typing import Any
from sqlalchemy.orm import Session
from contracts.dto.creative import StoryArcDTO, ConflictDTO, PlotPointDTO
from brain.story_bible.bible import story_bible_engine

class PlotEngine:
    """Core Plot and Narrative Arc Engine managing creative structures and timeline plot points."""
    
    async def create_story_arc(self, universe_id: str, arc: StoryArcDTO, db: Session = None) -> StoryArcDTO:
        """Saves a high-level narrative arc definition inside the Story Bible."""
        story_bible_engine.update_bible(
            universe_id=universe_id,
            section="story_arcs",
            key=arc.id,
            new_value=arc.model_dump(),
            author="Creative Director Agent",
            reason=f"Formulate story arc definition: {arc.title}",
            db=db
        )
        return arc

    async def create_conflict(self, universe_id: str, conflict: ConflictDTO, db: Session = None) -> ConflictDTO:
        """Registers a conflict map model tracking tension between parties."""
        story_bible_engine.update_bible(
            universe_id=universe_id,
            section="conflicts",
            key=conflict.id,
            new_value=conflict.model_dump(),
            author="Creative Director Agent",
            reason=f"Map conflict tension score: {conflict.tension_score}",
            db=db
        )
        return conflict

    async def generate_plot_point(self, universe_id: str, plot_point: PlotPointDTO, db: Session = None) -> PlotPointDTO:
        """Registers a chronological beat event inside the Story Bible timeline."""
        story_bible_engine.update_bible(
            universe_id=universe_id,
            section="plot_points",
            key=plot_point.id,
            new_value=plot_point.model_dump(),
            author="Creative Director Agent",
            reason=f"Generate plot point beat {plot_point.beat_number} for arc: {plot_point.arc_id}",
            db=db
        )
        return plot_point

    async def inject_plot_twist(self, universe_id: str, plot_point_id: str, twist_description: str) -> dict[str, Any]:
        """Injects a dramatic plot twist modifier on an existing beat."""
        return {"plot_point_id": plot_point_id, "twist": twist_description, "status": "twist_injected"}

    async def register_foreshadowing(self, universe_id: str, plot_point_id: str, clues: list[str]) -> list[str]:
        """Tracks foreshadowing clues linking setup and payoff events."""
        return clues

    async def map_emotional_arc(self, universe_id: str, scene_number: int, flow: str) -> str:
        """Determines the emotional intensity transition flow of a scene (e.g. rising hope to despair)."""
        return flow

plot_engine = PlotEngine()
