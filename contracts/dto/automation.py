import uuid
from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, ConfigDict

class AutomationJobCreateDTO(BaseModel):
    trigger_type: Optional[str] = "MANUAL_TRIGGER"  # SCHEDULE, PACKAGE_CREATED, PACKAGE_UPDATED, QUALITY_APPROVED, PUBLISHING_COMPLETED, PUBLISHING_FAILED, LEARNING_RECOMMENDATION, EXPERIMENT_COMPLETED, RETRY_REQUESTED, MANUAL_TRIGGER, WEBHOOK_TRIGGER
    source_package_id: Optional[uuid.UUID] = None
    target_platform: Optional[str] = "all"
    priority: Optional[int] = 0

class AutomationPolicyCreateDTO(BaseModel):
    policy_id: str
    name: str
    enabled: Optional[bool] = True
    priority: Optional[int] = 0
    trigger_types: List[str]
    conditions: dict[str, Any]
    target_workflow_id: Optional[str] = "AUTONOMOUS_PUBLISHING"
    cooldown_sec: Optional[int] = 60

class AutomationPolicyDTO(BaseModel):
    id: uuid.UUID
    policy_id: str
    name: str
    enabled: bool
    priority: int
    trigger_types: List[str]
    conditions: dict[str, Any]
    target_workflow_id: str
    cooldown_sec: int
    platforms: List[str]
    applicable_agents: List[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AutomationTriggerDTO(BaseModel):
    id: uuid.UUID
    trigger_id: str
    trigger_type: str
    source_component: str
    source_package_id: Optional[uuid.UUID] = None
    target_platform: str
    event_data: dict[str, Any]
    triggered_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AutomationDecisionDTO(BaseModel):
    id: uuid.UUID
    policy_id: str
    workflow_id: str
    is_approved: bool
    decision_reason: str
    confidence_score: float
    condition_evaluations: dict[str, Any]
    resource_lock_acquired: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WorkflowStepExecutionDTO(BaseModel):
    id: uuid.UUID
    instance_id: uuid.UUID
    step_id: str
    action_type: str
    target_agent: str
    idempotency_key: str
    status: str
    execution_ms: int
    result_data: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    compensation_executed: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WorkflowInstanceDTO(BaseModel):
    id: uuid.UUID
    instance_id: str
    workflow_id: str
    trigger_id: str
    policy_id: str
    status: str
    current_step: str
    execution_owner: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context_snapshot: dict[str, Any]
    compensation_log: Optional[List[dict[str, Any]]] = None
    created_at: datetime
    step_executions: Optional[List[WorkflowStepExecutionDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class AutomationPackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    workflow_id: str
    policy_id: str
    target_platform: str
    execution_confidence: float
    executed_actions_count: int
    execution_context_snapshot: Optional[dict[str, Any]] = None
    package_manifest: Optional[dict[str, Any]] = None
    
    # Mixin fields
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

class AutomationJobResponseDTO(BaseModel):
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
    trigger_type: str
    source_package_id: Optional[uuid.UUID] = None
    target_platform: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    packages: Optional[List[AutomationPackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class AutomationMetricsDTO(BaseModel):
    jobs_queued: int
    jobs_processing: int
    jobs_succeeded: int
    jobs_failed: int
    total_automation_packages: int
    total_active_policies: int
    total_triggers_received: int
    overall_execution_confidence: float
    average_duration_sec: float
    current_worker_count: int
    worker_uptime: str
    worker_is_running: bool
    worker_heartbeats: List[dict[str, Any]]
