from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CompensationAction(BaseModel):
    """Action executed on failure to compensate or rollback previous changes."""
    action_type: str  # e.g., ARCHIVE_PACKAGE, NOTIFY_USER, RESET_JOB_STATUS
    target_agent: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class WorkflowStep(BaseModel):
    """Individual step within a WorkflowDefinition."""
    step_id: str
    name: str
    action_type: str  # RUN_RESEARCH, RUN_SCRIPT, RUN_IMAGE, RUN_VOICE, RUN_VIDEO, RUN_SUBTITLE, RUN_MUSIC, RUN_THUMBNAIL, RUN_QUALITY, PUBLISH_CONTENT, LAUNCH_EXPERIMENT, RETRY_PUBLISHING, REFRESH_LEARNING, ARCHIVE_PACKAGE, NOTIFY_USER
    target_agent: str
    depends_on: List[str] = Field(default_factory=list)
    is_parallel: bool = False
    timeout_sec: int = 120
    payload_template: Dict[str, Any] = Field(default_factory=dict)
    compensation_action: Optional[CompensationAction] = None

class WorkflowDefinition(BaseModel):
    """Immutable workflow blueprint defining execution steps, dependencies, parallel groups, and rollbacks."""
    workflow_id: str
    name: str
    description: str
    version: int = 1
    steps: List[WorkflowStep]
    timeout_sec: int = 600
    rollback_rules: Dict[str, Any] = Field(default_factory=dict)
    success_criteria: Dict[str, Any] = Field(default_factory=dict)

class WorkflowRegistry:
    """Registry managing reusable WorkflowDefinitions across AATES."""

    def __init__(self) -> None:
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._initialize_default_workflows()

    def _initialize_default_workflows(self) -> None:
        # 1. E2E Content Generation Workflow
        e2e = WorkflowDefinition(
            workflow_id="E2E_CONTENT_GENERATION",
            name="End-to-End Content Generation Pipeline",
            description="Full automated generation from Research -> Script -> (Image + Voice) -> Video -> Subtitle -> Music -> Thumbnail -> Quality Gate.",
            steps=[
                WorkflowStep(step_id="step_research", name="Research Generation", action_type="RUN_RESEARCH", target_agent="ResearchAgent"),
                WorkflowStep(step_id="step_script", name="Script Generation", action_type="RUN_SCRIPT", target_agent="ScriptAgent", depends_on=["step_research"]),
                WorkflowStep(step_id="step_image", name="Image Generation", action_type="RUN_IMAGE", target_agent="ImageAgent", depends_on=["step_script"], is_parallel=True),
                WorkflowStep(step_id="step_voice", name="Voice Synthesis", action_type="RUN_VOICE", target_agent="VoiceAgent", depends_on=["step_script"], is_parallel=True),
                WorkflowStep(step_id="step_video", name="Video Rendering", action_type="RUN_VIDEO", target_agent="VideoAgent", depends_on=["step_image", "step_voice"]),
                WorkflowStep(step_id="step_subtitle", name="Subtitle Alignment", action_type="RUN_SUBTITLE", target_agent="SubtitleAgent", depends_on=["step_video"]),
                WorkflowStep(step_id="step_music", name="Music Selection", action_type="RUN_MUSIC", target_agent="MusicAgent", depends_on=["step_video"]),
                WorkflowStep(step_id="step_thumbnail", name="Thumbnail Generation", action_type="RUN_THUMBNAIL", target_agent="ThumbnailAgent", depends_on=["step_script"]),
                WorkflowStep(step_id="step_quality", name="Quality Gate Validation", action_type="RUN_QUALITY", target_agent="QualityAgent", depends_on=["step_video", "step_music", "step_thumbnail"])
            ]
        )

        # 2. Autonomous Publishing Workflow
        pub = WorkflowDefinition(
            workflow_id="AUTONOMOUS_PUBLISHING",
            name="Autonomous Multi-Platform Publishing Workflow",
            description="Quality Gate Approval -> Media Transformation -> Upload -> Publish Content.",
            steps=[
                WorkflowStep(step_id="step_pub_quality", name="Validate Quality Approval", action_type="RUN_QUALITY", target_agent="QualityAgent"),
                WorkflowStep(step_id="step_publish", name="Publish to Platform", action_type="PUBLISH_CONTENT", target_agent="PublishingProvider", depends_on=["step_pub_quality"], compensation_action=CompensationAction(action_type="NOTIFY_USER", target_agent="NotificationAgent", payload={"message": "Publishing failed"}))
            ]
        )

        # 3. Quality Remediation Workflow
        rem = WorkflowDefinition(
            workflow_id="QUALITY_REMEDIATION",
            name="Quality Remediation Workflow",
            description="Re-run failed component agent and re-evaluate quality gate.",
            steps=[
                WorkflowStep(step_id="step_rem_agent", name="Re-run Failed Agent", action_type="RUN_SCRIPT", target_agent="ScriptAgent"),
                WorkflowStep(step_id="step_rem_quality", name="Re-evaluate Quality", action_type="RUN_QUALITY", target_agent="QualityAgent", depends_on=["step_rem_agent"])
            ]
        )

        # 4. Feedback Driven Optimization Workflow
        fdo = WorkflowDefinition(
            workflow_id="FEEDBACK_DRIVEN_OPTIMIZATION",
            name="Feedback Driven Optimization Workflow",
            description="Execute Learning Recommendation parameter updates and refresh learning engine.",
            steps=[
                WorkflowStep(step_id="step_refresh_learning", name="Refresh Analytics Engine", action_type="REFRESH_LEARNING", target_agent="LearningAgent"),
                WorkflowStep(step_id="step_notify_opt", name="Notify System Optimization", action_type="NOTIFY_USER", target_agent="NotificationAgent", depends_on=["step_refresh_learning"])
            ]
        )

        for w in [e2e, pub, rem, fdo]:
            self._workflows[w.workflow_id] = w

    def register(self, workflow: WorkflowDefinition) -> None:
        self._workflows[workflow.workflow_id] = workflow

    def get(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def list_all(self) -> List[WorkflowDefinition]:
        return list(self._workflows.values())

workflow_registry = WorkflowRegistry()
ZOOMING = "zoom"
