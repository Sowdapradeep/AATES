import uuid
from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, ConfigDict

class LearningJobCreateDTO(BaseModel):
    target_platform: Optional[str] = "all"  # instagram, youtube, all
    learning_window_days: Optional[int] = 30
    learning_mode: Optional[str] = "batch"  # batch, incremental
    priority: Optional[int] = 0

class RecommendationFeedbackCreateDTO(BaseModel):
    recommendation_id: uuid.UUID
    status: str  # APPLIED, SKIPPED, MEASURING, SUCCESSFUL, FAILED
    initial_metric: Optional[float] = 0.0
    measured_metric: Optional[float] = 0.0
    impact_percent: Optional[float] = 0.0

class RecommendationFeedbackDTO(BaseModel):
    id: uuid.UUID
    recommendation_id: uuid.UUID
    applied_at: Optional[datetime] = None
    status: str
    initial_metric: float
    measured_metric: float
    impact_percent: float
    confidence_update: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RecommendationDTO(BaseModel):
    id: uuid.UUID
    learning_package_id: uuid.UUID
    target_agent: str
    category: str
    priority: str
    confidence_score: float
    expected_impact: str
    suggested_action: str
    action_payload: Optional[dict[str, Any]] = None
    evidence_data: Optional[dict[str, Any]] = None
    created_at: datetime
    feedbacks: Optional[List[RecommendationFeedbackDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class LearningSignalDTO(BaseModel):
    id: uuid.UUID
    learning_package_id: uuid.UUID
    signal_key: str
    title: str
    category: str
    correlation_coefficient: float
    confidence_score: float
    platform: str
    applicable_agents: List[str]
    causality_level: str
    evidence_data: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ExperimentResultDTO(BaseModel):
    id: uuid.UUID
    learning_package_id: uuid.UUID
    experiment_id: str
    experiment_type: str
    winning_variant_id: str
    confidence_score: float
    metric_lift_percent: float
    insights_snapshot: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PerformanceSnapshotDTO(BaseModel):
    id: uuid.UUID
    learning_package_id: uuid.UUID
    platform: str
    window_days: int
    total_publications: int
    total_views: int
    total_reach: int
    avg_ctr: float
    avg_engagement_rate: float
    avg_watch_time_ms: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LearningPackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    dataset_id: uuid.UUID
    target_platform: str
    learning_confidence: float
    model_version: str
    feature_importance_snapshot: Optional[dict[str, Any]] = None
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
    
    performance_snapshots: Optional[List[PerformanceSnapshotDTO]] = None
    signals: Optional[List[LearningSignalDTO]] = None
    recommendations: Optional[List[RecommendationDTO]] = None
    experiments: Optional[List[ExperimentResultDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class LearningJobResponseDTO(BaseModel):
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
    target_platform: str
    learning_window_days: int
    dataset_size: int
    learning_mode: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    packages: Optional[List[LearningPackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class LearningMetricsDTO(BaseModel):
    jobs_queued: int
    jobs_processing: int
    jobs_succeeded: int
    jobs_failed: int
    total_learning_packages: int
    total_signals_discovered: int
    total_recommendations_generated: int
    overall_learning_confidence: float
    average_duration_sec: float
    current_worker_count: int
    worker_uptime: str
    worker_is_running: bool
    worker_heartbeats: List[dict[str, Any]]
