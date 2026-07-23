import uuid
from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, ConfigDict

class OrchestrationJobCreateDTO(BaseModel):
    objective_type: Optional[str] = "GENERATE_LONGFORM_VIDEO"  # GENERATE_LONGFORM_VIDEO, GENERATE_SHORTS, REPUBLISH_EXISTING_CONTENT, OPTIMIZE_EXISTING_VIDEO, RUN_THUMBNAIL_EXPERIMENT, GENERATE_PLATFORM_VARIANTS, MULTI_PLATFORM_PUBLISHING, BULK_CAMPAIGN_EXECUTION
    target_platform: Optional[str] = "all"
    priority: Optional[int] = 5
    title: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None

class ObjectiveDTO(BaseModel):
    id: uuid.UUID
    objective_id: str
    title: str
    objective_type: str
    target_platform: str
    priority: int
    target_kpi: dict[str, Any]
    parameters: dict[str, Any]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ExecutionPlanDTO(BaseModel):
    id: uuid.UUID
    plan_id: str
    objective_id: str
    objective_type: str
    required_agents: List[str]
    estimated_duration_sec: int
    parallelism_factor: int
    risk_score: float
    expected_resources: dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TaskNodeDTO(BaseModel):
    id: uuid.UUID
    node_id: str
    target_agent: str
    action_type: str
    depends_on: List[str]
    estimated_duration_sec: int
    priority: int
    retry_policy: dict[str, Any]
    resource_requirements: dict[str, Any]
    status: str
    result_data: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrchestrationPackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    objective_type: str
    target_platform: str
    orchestration_confidence: float
    executed_nodes_count: int
    total_nodes_count: int
    plan_snapshot: Optional[dict[str, Any]] = None
    dag_snapshot: Optional[dict[str, Any]] = None
    package_manifest: Optional[dict[str, Any]] = None

    # BasePackageMixin fields
    version: int
    parent_package_id: Optional[uuid.UUID] = None
    source_agent: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt_version: Optional[str] = None
    quality_score: float
    telemetry_metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrchestrationJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    status: str
    stage: str
    progress: float
    attempts: int
    max_attempts: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    duration_sec: float
    worker_id: Optional[str] = None
    priority: int
    objective_type: str
    target_platform: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    packages: Optional[List[OrchestrationPackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class OrchestrationMetricsDTO(BaseModel):
    jobs_queued: int
    jobs_processing: int
    jobs_succeeded: int
    jobs_failed: int
    total_orchestration_packages: int
    total_active_objectives: int
    total_plans_generated: int
    overall_orchestration_confidence: float
    average_duration_sec: float
    current_worker_count: int
    worker_uptime: str
    worker_is_running: bool
    worker_heartbeats: List[dict[str, Any]]
