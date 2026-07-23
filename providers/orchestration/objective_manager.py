import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("objective_manager")

class Objective(BaseModel):
    """Business objective representation for multi-agent strategic orchestration."""
    objective_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    objective_type: str  # GENERATE_LONGFORM_VIDEO, GENERATE_SHORTS, REPUBLISH_EXISTING_CONTENT, OPTIMIZE_EXISTING_VIDEO, RUN_THUMBNAIL_EXPERIMENT, GENERATE_PLATFORM_VARIANTS, MULTI_PLATFORM_PUBLISHING, BULK_CAMPAIGN_EXECUTION
    target_platform: str = "all"  # instagram, youtube, all
    priority: int = 5
    target_kpi: Dict[str, Any] = Field(default_factory=dict)  # e.g., {"target_views": 10000, "target_ctr": 0.08}
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = "PENDING"  # PENDING, PLANNING, EXECUTING, COMPLETED, REPLANNING, FAILED
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ObjectiveManager:
    """Objective Manager maintaining active business objectives and targets."""

    def __init__(self) -> None:
        self._objectives: Dict[str, Objective] = {}
        self._initialize_default_objectives()

    def _initialize_default_objectives(self) -> None:
        defaults = [
            Objective(
                objective_id="obj_longform_001",
                title="Automated Longform YouTube & Shorts Campaign",
                objective_type="GENERATE_LONGFORM_VIDEO",
                target_platform="all",
                priority=10,
                target_kpi={"min_quality_score": 0.85, "target_ctr": 0.08},
                parameters={"topic": "AI Automated Content Systems"}
            ),
            Objective(
                objective_id="obj_shorts_001",
                title="Daily Viral Shorts Pipeline",
                objective_type="GENERATE_SHORTS",
                target_platform="instagram",
                priority=8,
                target_kpi={"min_quality_score": 0.90},
                parameters={"aspect_ratio": "9:16"}
            ),
            Objective(
                objective_id="obj_experiment_001",
                title="Thumbnail Contrast A/B Experiment",
                objective_type="RUN_THUMBNAIL_EXPERIMENT",
                target_platform="youtube",
                priority=7,
                target_kpi={"expected_lift_percent": 15.0},
                parameters={"experiment_type": "Thumbnail Contrast"}
            )
        ]
        for obj in defaults:
            self._objectives[obj.objective_id] = obj

    def create_objective(self, title: str, objective_type: str, target_platform: str = "all", priority: int = 5, parameters: Optional[Dict[str, Any]] = None) -> Objective:
        obj = Objective(
            objective_id=str(uuid.uuid4()),
            title=title,
            objective_type=objective_type,
            target_platform=target_platform,
            priority=priority,
            parameters=parameters or {}
        )
        self._objectives[obj.objective_id] = obj
        logger.info(f"[ObjectiveManager] Created Objective '{obj.title}' (ID: {obj.objective_id})")
        return obj

    def get_objective(self, objective_id: str) -> Optional[Objective]:
        return self._objectives.get(objective_id)

    def list_objectives(self) -> List[Objective]:
        return list(self._objectives.values())

objective_manager = ObjectiveManager()
ZOOMING = "zoom"
