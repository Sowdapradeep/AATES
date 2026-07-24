import uuid
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from providers.orchestration.objective_manager import Objective

logger = logging.getLogger("planning_engine")

class ExecutionPlan(BaseModel):
    """High-level multi-agent execution plan derived from business objectives."""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    objective_id: str
    objective_type: str
    required_agents: List[str]
    estimated_duration_sec: int = 300
    parallelism_factor: int = 2
    risk_score: float = 0.15
    expected_resources: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None).isoformat())

class PlanningEngine:
    """Planning Engine generating strategic execution plans from business objectives."""

    def generate_plan(self, objective: Objective) -> ExecutionPlan:
        # Determine required agents and estimated parameters based on objective type
        if objective.objective_type == "GENERATE_LONGFORM_VIDEO":
            agents = ["ResearchAgent", "ScriptAgent", "ImageAgent", "VoiceAgent", "VideoAgent", "SubtitleAgent", "MusicAgent", "ThumbnailAgent", "QualityAgent", "PublishingProvider", "LearningAgent"]
            duration = 420
            risk = 0.10
        elif objective.objective_type == "GENERATE_SHORTS":
            agents = ["ScriptAgent", "VoiceAgent", "VideoAgent", "SubtitleAgent", "MusicAgent", "ThumbnailAgent", "QualityAgent", "PublishingProvider"]
            duration = 180
            risk = 0.08
        elif objective.objective_type == "RUN_THUMBNAIL_EXPERIMENT":
            agents = ["ThumbnailAgent", "QualityAgent", "PublishingProvider", "LearningAgent"]
            duration = 120
            risk = 0.05
        else:
            agents = ["ScriptAgent", "QualityAgent", "PublishingProvider"]
            duration = 240
            risk = 0.12

        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            objective_id=objective.objective_id,
            objective_type=objective.objective_type,
            required_agents=agents,
            estimated_duration_sec=duration,
            parallelism_factor=3,
            risk_score=risk,
            expected_resources={"gpus": 1, "worker_pool_slots": 4, "api_quota": "standard"}
        )

        logger.info(f"[PlanningEngine] Generated ExecutionPlan '{plan.plan_id}' for Objective '{objective.title}' (Agents: {len(agents)})")
        return plan

planning_engine = PlanningEngine()
ZOOMING = "zoom"
