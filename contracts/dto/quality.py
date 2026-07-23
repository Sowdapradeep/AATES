import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class QualityJobCreateDTO(BaseModel):
    script_package_id: uuid.UUID
    image_package_id: uuid.UUID
    voice_package_id: uuid.UUID
    video_package_id: uuid.UUID
    subtitle_package_id: Optional[uuid.UUID] = None
    music_package_id: Optional[uuid.UUID] = None
    thumbnail_package_id: Optional[uuid.UUID] = None
    quality_policy_id: Optional[uuid.UUID] = None
    provider: Optional[str] = "policy_engine"
    priority: Optional[int] = 0

class QualityRuleDTO(BaseModel):
    id: uuid.UUID
    rule_name: str
    dimension: str
    target_package: str
    metric_name: str
    operator: str
    threshold_value: str
    severity: str
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class QualityPolicyDTO(BaseModel):
    id: uuid.UUID
    name: str
    platform: str
    policy_version: str
    rule_set_version: str
    description: Optional[str] = None
    min_readiness_score: float
    allow_critical_issues: bool
    dimension_weights: Optional[dict[str, Any]] = None
    created_at: datetime
    rules: Optional[list[QualityRuleDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class QualityCheckDTO(BaseModel):
    id: uuid.UUID
    quality_package_id: uuid.UUID
    package_type: str
    dimension: str
    check_name: str
    status: str
    evaluated_value: str
    target_threshold: str
    execution_ms: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class QualityEvidenceDTO(BaseModel):
    id: uuid.UUID
    quality_issue_id: uuid.UUID
    source_package: str
    artifact_path: Optional[str] = None
    timestamp_ms: Optional[int] = None
    metric_name: str
    observed_value: str
    expected_value: str
    snapshot_data: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class QualityRecommendationDTO(BaseModel):
    id: uuid.UUID
    quality_issue_id: uuid.UUID
    recommendation_type: str
    priority: str
    target_agent: str
    auto_fix_available: bool
    estimated_impact: Optional[str] = None
    action_payload: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class QualityIssueDTO(BaseModel):
    id: uuid.UUID
    quality_package_id: uuid.UUID
    quality_check_id: Optional[uuid.UUID] = None
    issue_code: str
    category: str
    severity: str
    description: str
    impacted_component: str
    remediation_suggestion: Optional[str] = None
    is_resolved: bool
    created_at: datetime
    evidence_items: Optional[list[QualityEvidenceDTO]] = None
    recommendations: Optional[list[QualityRecommendationDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class RemediationTaskDTO(BaseModel):
    id: uuid.UUID
    quality_package_id: uuid.UUID
    target_agent: str
    status: str
    action_type: str
    payload: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class QualityVersionDTO(BaseModel):
    id: uuid.UUID
    quality_package_id: uuid.UUID
    version: int
    parent_version: Optional[int] = None
    lineage_action: str
    assets_snapshot: list[dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class QualityPackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    script_package_id: uuid.UUID
    image_package_id: uuid.UUID
    voice_package_id: uuid.UUID
    video_package_id: uuid.UUID
    subtitle_package_id: Optional[uuid.UUID] = None
    music_package_id: Optional[uuid.UUID] = None
    thumbnail_package_id: Optional[uuid.UUID] = None
    quality_policy_id: Optional[uuid.UUID] = None
    
    publishing_lifecycle_state: str
    production_readiness_score: float
    is_approved_for_publishing: bool
    critical_issue_count: int
    major_issue_count: int
    minor_issue_count: int
    dimension_scores: Optional[dict[str, Any]] = None
    aggregated_telemetry: Optional[dict[str, Any]] = None
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
    
    checks: Optional[list[QualityCheckDTO]] = None
    issues: Optional[list[QualityIssueDTO]] = None
    remediation_tasks: Optional[list[RemediationTaskDTO]] = None
    versions: Optional[list[QualityVersionDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class QualityJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    script_package_id: uuid.UUID
    image_package_id: uuid.UUID
    voice_package_id: uuid.UUID
    video_package_id: uuid.UUID
    subtitle_package_id: Optional[uuid.UUID] = None
    music_package_id: Optional[uuid.UUID] = None
    thumbnail_package_id: Optional[uuid.UUID] = None
    quality_policy_id: Optional[uuid.UUID] = None
    provider: str
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
    scheduled_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    policy: Optional[QualityPolicyDTO] = None
    packages: Optional[list[QualityPackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class QualityMetricsDTO(BaseModel):
    jobs_queued: int
    jobs_processing: int
    jobs_succeeded: int
    jobs_failed: int
    jobs_retrying: int
    jobs_cancelled: int
    approval_rate: float
    average_readiness_score: float
    average_duration_sec: float
    current_worker_count: int
    worker_uptime: str
    worker_is_running: bool
    worker_heartbeats: list[dict[str, Any]]
