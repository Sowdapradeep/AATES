import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, ForeignKey, Table, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.compiler import compiles
from core.database.session import Base

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    """Compiles PostgreSQL JSONB to standard JSON string when executing on SQLite dialect (testing)."""
    return "JSON"


@compiles(UUID, "sqlite")
def compile_uuid_sqlite(element, compiler, **kw):
    """Compiles PostgreSQL UUID to VARCHAR(36) when executing on SQLite dialect (testing)."""
    return "VARCHAR(36)"


# Many-to-Many Join Tables
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class Configuration(Base):
    __tablename__ = "configurations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    environment: Mapped[str] = mapped_column(String(50), default="development")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    retry_limit: Mapped[int] = mapped_column(Integer, default=3)


class SystemState(Base):
    __tablename__ = "system_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    state_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flag_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class WorkflowDefinition(Base):
    __tablename__ = "workflow_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    steps: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    outputs: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AIProvider(Base):
    __tablename__ = "ai_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    api_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)

    configs = relationship("ModelConfiguration", back_populates="provider")


class ModelConfiguration(Base):
    __tablename__ = "model_configurations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    provider = relationship("AIProvider", back_populates="configs")


# Model Metrics Tables
class ModelHealth(Base):
    __tablename__ = "model_health"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_config_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_configurations.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="healthy")
    last_checked: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ModelCapability(Base):
    __tablename__ = "model_capabilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_config_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_configurations.id", ondelete="CASCADE"), nullable=False)
    capability_name: Mapped[str] = mapped_column(String(100), nullable=False)
    supports: Mapped[bool] = mapped_column(Boolean, default=True)


class ModelPricing(Base):
    __tablename__ = "model_pricing"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_config_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_configurations.id", ondelete="CASCADE"), nullable=False)
    prompt_token_cost: Mapped[float] = mapped_column(Float, default=0.0)
    completion_token_cost: Mapped[float] = mapped_column(Float, default=0.0)


class ModelLatency(Base):
    __tablename__ = "model_latency"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_config_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_configurations.id", ondelete="CASCADE"), nullable=False)
    p95_latency_ms: Mapped[int] = mapped_column(Integer, default=0)


class ModelAvailability(Base):
    __tablename__ = "model_availability"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_config_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_configurations.id", ondelete="CASCADE"), nullable=False)
    current_rate_limit_remaining: Mapped[int] = mapped_column(Integer, default=100)


# Budget Management Tables
class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    allocated_amount: Mapped[float] = mapped_column(Float, default=0.0)
    spent_amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")


class ProviderCost(Base):
    __tablename__ = "provider_costs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)
    last_call_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EpisodeCost(Base):
    __tablename__ = "episode_costs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)


class DailyCost(Base):
    __tablename__ = "daily_costs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date: Mapped[datetime] = mapped_column(DateTime, unique=True, nullable=False)
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)


class MonthlyCost(Base):
    __tablename__ = "monthly_costs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    month: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # YYYY-MM
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)


# Asset Registry Table
class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # image, video, voice, script
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(20), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    storage_location: Mapped[str] = mapped_column(String(255), nullable=False)
    episode_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    universe_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    scene_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parent_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    blueprint_version: Mapped[int] = mapped_column(Integer, default=1)
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



# Production Queue Tables
class ProductionQueue(Base):
    __tablename__ = "production_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    season: Mapped[int] = mapped_column(Integer, default=1)
    episode: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    assigned_worker: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tasks = relationship("ProductionTask", back_populates="queue")
    history = relationship("ProductionHistory", back_populates="queue")


class ProductionTask(Base):
    __tablename__ = "production_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("production_queue.id", ondelete="CASCADE"), nullable=False)
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)

    queue = relationship("ProductionQueue", back_populates="tasks")


class ProductionHistory(Base):
    __tablename__ = "production_histories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("production_queue.id", ondelete="CASCADE"), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    queue = relationship("ProductionQueue", back_populates="history")


# Decision Explainability Tables
class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_name: Mapped[str] = mapped_column(String(100), nullable=False)  # CEO, Director
    decision_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    reasons = relationship("DecisionReason", back_populates="decision")
    confidence = relationship("DecisionConfidence", back_populates="decision", uselist=False)


class DecisionReason(Base):
    __tablename__ = "decision_reasons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("decision_logs.id", ondelete="CASCADE"), nullable=False)
    reason_text: Mapped[str] = mapped_column(Text, nullable=False)

    decision = relationship("DecisionLog", back_populates="reasons")


class DecisionConfidence(Base):
    __tablename__ = "decision_confidences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("decision_logs.id", ondelete="CASCADE"), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    decision = relationship("DecisionLog", back_populates="confidence")


# Operations Campaign Management
class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    universe_id: Mapped[str] = mapped_column(String(36), nullable=False)
    season: Mapped[int] = mapped_column(Integer, default=1)
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    platforms: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


# Operations Distribution History
class DistributionHistory(Base):
    __tablename__ = "distribution_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    universe_id: Mapped[str] = mapped_column(String(36), nullable=False)
    episode_id: Mapped[str] = mapped_column(String(36), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    publish_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    asset_version: Mapped[int] = mapped_column(Integer, default=1)
    blueprint_version: Mapped[int] = mapped_column(Integer, default=1)
    workflow_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)


# Operations Immutable Analytics Snapshots
class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_id: Mapped[str] = mapped_column(String(36), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    watch_time: Mapped[float] = mapped_column(Float, default=0.0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    follower_growth: Mapped[int] = mapped_column(Integer, default=0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Operations Timeline Audit Trail
class OperationsTimeline(Base):
    __tablename__ = "operations_timeline"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Operations Auditable Learning Recommendations
class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    episode_id: Mapped[str] = mapped_column(String(36), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expected_impact: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    ceo_decision_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Operations Provider Health Monitor
class ProviderHealth(Base):
    __tablename__ = "provider_health"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    error_rate: Mapped[float] = mapped_column(Float, default=0.0)
    success_rate: Mapped[float] = mapped_column(Float, default=1.0)
    last_success_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PublishingJob(Base):
    __tablename__ = "publishing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content_id: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    priority: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    video_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    provider_response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"

    worker_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── AI Research Engine Models ──────────────────────────────────────────────────

class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="DISCOVERING") # DISCOVERING, COLLECTING, EXTRACTING, RANKING, SUMMARIZING, COMPLETED
    priority: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    providers_used: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    summary_time_sec: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sources = relationship("ResearchSource", back_populates="job", cascade="all, delete-orphan")
    packages = relationship("KnowledgePackage", back_populates="job", cascade="all, delete-orphan")
    keywords = relationship("Keyword", back_populates="job", cascade="all, delete-orphan")
    competitors = relationship("Competitor", back_populates="job", cascade="all, delete-orphan")


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("ResearchJob", back_populates="sources")


class BasePackageMixin:
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source_agent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=1.0)
    telemetry_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgePackage(Base, BasePackageMixin):
    __tablename__ = "knowledge_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id", ondelete="CASCADE"), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Text summaries and findings
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    audience: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    pain_points: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    faqs: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    competitors: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    statistics: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    
    # Story structure: hook, problem, story, solution, cta
    story_structure: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    # Visual ideas: scene suggestions, characters, camera angles, backgrounds, color themes, emotion, style references
    visual_ideas: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    # Outline of contents, suggested hooks, titles, ctas, references
    outline: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    hooks: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    ctas: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    titles: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    references: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("ResearchJob", back_populates="packages")


class TrendingTopic(Base):
    __tablename__ = "trending_topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0)
    language: Mapped[str] = mapped_column(String(50), default="ta")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id", ondelete="SET NULL"), nullable=True)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False)
    volume: Mapped[int] = mapped_column(Integer, default=0)
    difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("ResearchJob", back_populates="keywords")


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("ResearchJob", back_populates="competitors")


# ── AI Script Engine Models ──────────────────────────────────────────────────

class ScriptJob(Base):
    __tablename__ = "script_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    knowledge_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_packages.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="ta")
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="VALIDATING")  # VALIDATING, PLANNING, GENERATING, REVIEWING, OPTIMIZING, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    packages = relationship("ScriptPackage", back_populates="job", cascade="all, delete-orphan")


class ScriptPackage(Base, BasePackageMixin):
    __tablename__ = "script_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_jobs.id", ondelete="CASCADE"), nullable=False)
    knowledge_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_packages.id", ondelete="CASCADE"), nullable=False)

    # Script Metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="ta")
    target_audience: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    reading_time_sec: Mapped[float] = mapped_column(Float, default=0.0)

    # Creative Content
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    opening: Mapped[str | None] = mapped_column(Text, nullable=True)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    story: Mapped[str] = mapped_column(Text, nullable=False)
    solution: Mapped[str] = mapped_column(Text, nullable=False)
    cta: Mapped[str] = mapped_column(Text, nullable=False)
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    scene_breakdown: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)  # Structured scene objects
    on_screen_text: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    visual_prompts: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    thumbnail_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    hashtags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    references: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # AI Quality Review Report
    review_report: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("ScriptJob", back_populates="packages")
    versions = relationship("ScriptVersion", back_populates="package", cascade="all, delete-orphan")


class ScriptVersion(Base):
    __tablename__ = "script_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")  # INITIAL, IMPROVED, REGENERATED
    
    # Snapshot of the script content and metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    opening: Mapped[str | None] = mapped_column(Text, nullable=True)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    story: Mapped[str] = mapped_column(Text, nullable=False)
    solution: Mapped[str] = mapped_column(Text, nullable=False)
    cta: Mapped[str] = mapped_column(Text, nullable=False)
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    scene_breakdown: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    thumbnail_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    hashtags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    review_report: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("ScriptPackage", back_populates="versions")


# ── AI Image Engine Models ───────────────────────────────────────────────────

class ImageJob(Base):
    __tablename__ = "image_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="VALIDATING")  # VALIDATING, PLANNING, PROMPTING, GENERATING, QUALITY_CHECK, OPTIMIZING, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    packages = relationship("ImagePackage", back_populates="job", cascade="all, delete-orphan")


class ImagePackage(Base, BasePackageMixin):
    __tablename__ = "image_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("image_jobs.id", ondelete="CASCADE"), nullable=False)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)

    # Package Metadata
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(50), nullable=False)
    resolution: Mapped[str] = mapped_column(String(50), nullable=False)
    style_preset: Mapped[str] = mapped_column(String(100), nullable=False)
    overall_theme: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_count: Mapped[int] = mapped_column(Integer, default=0)
    generation_settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Character Consistency Profiles
    character_profile: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    character_reference_images: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    character_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("ImageJob", back_populates="packages")
    assets = relationship("SceneAsset", back_populates="package", cascade="all, delete-orphan")
    versions = relationship("ImageVersion", back_populates="package", cascade="all, delete-orphan")


class SceneAsset(Base):
    __tablename__ = "scene_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("image_packages.id", ondelete="CASCADE"), nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[float] = mapped_column(Float, default=5.0)

    # Prompt details
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Style profiles & Metadata
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    aspect_ratio: Mapped[str] = mapped_column(String(50), nullable=False)
    resolution: Mapped[str] = mapped_column(String(50), nullable=False)
    style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    camera_angle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    character_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    background: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lighting: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color_palette: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Cloud ready paths
    local_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    public_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    preview_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Relationship linkages
    previous_scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    next_scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    transition_suggestion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    generation_duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("ImagePackage", back_populates="assets")


class ImageVersion(Base):
    __tablename__ = "image_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("image_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")  # INITIAL, IMPROVED, REGENERATED
    scene_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Snapshot of the image package state including all scene assets
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("ImagePackage", back_populates="versions")


# ── AI Voice Engine Models ────────────────────────────────────────────────────

class VoiceJob(Base):
    __tablename__ = "voice_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    voice_model: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="VALIDATING")  # VALIDATING, PLANNING, VOICE_SELECTION, GENERATING, ALIGNING, QUALITY_CHECK, OPTIMIZING, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    packages = relationship("VoicePackage", back_populates="job", cascade="all, delete-orphan")


class VoicePackage(Base, BasePackageMixin):
    __tablename__ = "voice_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_jobs.id", ondelete="CASCADE"), nullable=False)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)

    # Package Metadata
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    voice_profile: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    speaking_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    overall_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    total_words: Mapped[int] = mapped_column(Integer, default=0)
    total_scenes: Mapped[int] = mapped_column(Integer, default=0)
    audio_format: Mapped[str] = mapped_column(String(50), default="mp3")
    sample_rate: Mapped[int] = mapped_column(Integer, default=44100)
    bitrate: Mapped[int] = mapped_column(Integer, default=192000)
    pronunciation_dictionary: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("VoiceJob", back_populates="packages")
    assets = relationship("SceneVoice", back_populates="package", cascade="all, delete-orphan")
    versions = relationship("VoiceVersion", back_populates="package", cascade="all, delete-orphan")


class SceneVoice(Base):
    __tablename__ = "scene_voices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voice_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_packages.id", ondelete="CASCADE"), nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    # Content & Paths
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    local_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    public_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    preview_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Synthesized Parameters
    voice_id: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    emotion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    speaking_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pitch: Mapped[str | None] = mapped_column(String(50), nullable=True)
    speed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    volume: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ssml: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Alignments
    pause_map: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    word_alignment: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    sentence_alignment: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    phoneme_alignment: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    generation_duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("VoicePackage", back_populates="assets")


class VoiceVersion(Base):
    __tablename__ = "voice_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voice_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")  # INITIAL, IMPROVED, REGENERATED
    scene_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Snapshot of the voice package state including all scene voice assets
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("VoicePackage", back_populates="versions")


# ── AI Video Engine Models ────────────────────────────────────────────────────

class RenderProfile(Base):
    __tablename__ = "render_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    resolution: Mapped[str] = mapped_column(String(50), nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(50), nullable=False)
    fps: Mapped[int] = mapped_column(Integer, default=30)
    codec: Mapped[str] = mapped_column(String(50), default="h264")
    bitrate: Mapped[int] = mapped_column(Integer, default=5000000)
    container: Mapped[str] = mapped_column(String(50), default="mp4")
    audio_codec: Mapped[str] = mapped_column(String(50), default="aac")
    audio_sample_rate: Mapped[int] = mapped_column(Integer, default=44100)
    audio_bitrate: Mapped[int] = mapped_column(Integer, default=192000)
    color_space: Mapped[str | None] = mapped_column(String(50), default="srgb")
    hardware_acceleration: Mapped[bool] = mapped_column(Boolean, default=False)
    preset: Mapped[str | None] = mapped_column(String(50), default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    jobs = relationship("VideoJob", back_populates="profile")


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    image_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("image_packages.id", ondelete="CASCADE"), nullable=False)
    voice_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_packages.id", ondelete="CASCADE"), nullable=False)
    render_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("render_profiles.id", ondelete="SET NULL"), nullable=True)
    renderer: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="VALIDATING")  # VALIDATING, TIMELINE_BUILDING, SCENE_COMPOSITION, MOTION_RENDERING, TRANSITION_RENDERING, AUDIO_SYNCHRONIZATION, FINAL_RENDER, QUALITY_CHECK, OPTIMIZING, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("RenderProfile", back_populates="jobs")
    packages = relationship("VideoPackage", back_populates="job", cascade="all, delete-orphan")


class VideoPackage(Base, BasePackageMixin):
    __tablename__ = "video_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_jobs.id", ondelete="CASCADE"), nullable=False)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    image_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("image_packages.id", ondelete="CASCADE"), nullable=False)
    voice_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_packages.id", ondelete="CASCADE"), nullable=False)

    # Package Metadata
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    resolution: Mapped[str] = mapped_column(String(50), nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(50), nullable=False)
    fps: Mapped[int] = mapped_column(Integer, default=30)
    codec: Mapped[str] = mapped_column(String(50), default="h264")
    bitrate: Mapped[int] = mapped_column(Integer, default=5000000)
    container: Mapped[str] = mapped_column(String(50), default="mp4")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    storage_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    preview_video: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    thumbnail_frame: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    scene_count: Mapped[int] = mapped_column(Integer, default=0)
    timeline_version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Downstream Metadata for Subtitle & Thumbnail Agents
    metadata_artifacts: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True) # keyframes, title-safe, representative frame indices
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("VideoJob", back_populates="packages")
    assets = relationship("SceneVideo", back_populates="package", cascade="all, delete-orphan")
    events = relationship("TimelineEvent", back_populates="package", cascade="all, delete-orphan")
    versions = relationship("VideoVersion", back_populates="package", cascade="all, delete-orphan")


class SceneVideo(Base):
    __tablename__ = "scene_videos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    timeline_start_ms: Mapped[int] = mapped_column(Integer, default=0)
    timeline_end_ms: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    
    image_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("scene_assets.id", ondelete="SET NULL"), nullable=True)
    voice_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("scene_voices.id", ondelete="SET NULL"), nullable=True)
    
    motion_preset: Mapped[str | None] = mapped_column(String(100), default="None")
    transition_preset: Mapped[str | None] = mapped_column(String(100), default="Cut")
    rendered_clip: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    preview_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    
    render_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True) # SceneGraph details
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("VideoPackage", back_populates="assets")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    
    voice_offset_ms: Mapped[int] = mapped_column(Integer, default=0)
    transition_start_ms: Mapped[int] = mapped_column(Integer, default=0)
    transition_end_ms: Mapped[int] = mapped_column(Integer, default=0)
    motion_start_ms: Mapped[int] = mapped_column(Integer, default=0)
    motion_end_ms: Mapped[int] = mapped_column(Integer, default=0)
    caption_region: Mapped[str | None] = mapped_column(String(100), default="bottom")
    audio_fade_in_ms: Mapped[int] = mapped_column(Integer, default=0)
    audio_fade_out_ms: Mapped[int] = mapped_column(Integer, default=0)
    video_fade_in_ms: Mapped[int] = mapped_column(Integer, default=0)
    video_fade_out_ms: Mapped[int] = mapped_column(Integer, default=0)

    package = relationship("VideoPackage", back_populates="events")


class VideoVersion(Base):
    __tablename__ = "video_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")  # INITIAL, IMPROVED, RENDERED, REGENERATED
    
    # Snapshot of the video package state including all scene details
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("VideoPackage", back_populates="versions")


# ── AI Subtitle Engine Models ──────────────────────────────────────────────────

class CaptionStyleProfile(Base):
    __tablename__ = "caption_style_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    font_family: Mapped[str] = mapped_column(String(100), default="Inter")
    font_size: Mapped[int] = mapped_column(Integer, default=24)
    font_weight: Mapped[str] = mapped_column(String(50), default="Bold")
    text_color: Mapped[str] = mapped_column(String(50), default="#FFFFFF")
    outline_color: Mapped[str] = mapped_column(String(50), default="#000000")
    outline_width: Mapped[int] = mapped_column(Integer, default=2)
    shadow: Mapped[str | None] = mapped_column(String(100), default="0px 2px 4px rgba(0,0,0,0.8)")
    background_box: Mapped[bool] = mapped_column(Boolean, default=False)
    background_color: Mapped[str | None] = mapped_column(String(50), default="rgba(0,0,0,0.6)")
    alignment: Mapped[str] = mapped_column(String(50), default="center")
    vertical_position: Mapped[str] = mapped_column(String(50), default="bottom")
    margins: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    animation: Mapped[str | None] = mapped_column(String(100), default="fade")
    safe_region: Mapped[str | None] = mapped_column(String(100), default="80% safety window")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tracks = relationship("SubtitleTrack", back_populates="style_profile")


class SubtitleJob(Base):
    __tablename__ = "subtitle_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    voice_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_packages.id", ondelete="CASCADE"), nullable=False)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="en")
    provider: Mapped[str] = mapped_column(String(100), default="alignment")
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="VALIDATING")  # VALIDATING, ALIGNMENT_LOADING, SEGMENTING, LINE_BREAK_OPTIMIZATION, STYLE_APPLICATION, FORMAT_GENERATION, QUALITY_CHECK, OPTIMIZING, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    packages = relationship("SubtitlePackage", back_populates="job", cascade="all, delete-orphan")


class SubtitlePackage(Base, BasePackageMixin):
    __tablename__ = "subtitle_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subtitle_jobs.id", ondelete="CASCADE"), nullable=False)
    voice_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_packages.id", ondelete="CASCADE"), nullable=False)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)

    # Package Metadata
    language: Mapped[str] = mapped_column(String(20), default="en")
    caption_style: Mapped[str] = mapped_column(String(100), default="YouTube")
    subtitle_formats: Mapped[list[str]] = mapped_column(JSON, nullable=False)  # ["srt", "vtt", "ass", "json"]
    scene_count: Mapped[int] = mapped_column(Integer, default=0)
    total_captions: Mapped[int] = mapped_column(Integer, default=0)
    total_words: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata & Shared Manifest
    metadata_artifacts: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    package_manifest: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("SubtitleJob", back_populates="packages")
    scene_subtitles = relationship("SceneSubtitle", back_populates="package", cascade="all, delete-orphan")
    tracks = relationship("SubtitleTrack", back_populates="package", cascade="all, delete-orphan")
    versions = relationship("SubtitleVersion", back_populates="package", cascade="all, delete-orphan")


class SceneSubtitle(Base):
    __tablename__ = "scene_subtitles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subtitle_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subtitle_packages.id", ondelete="CASCADE"), nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    caption_text: Mapped[str] = mapped_column(Text, nullable=False)
    word_timings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    sentence_timings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    caption_position: Mapped[str] = mapped_column(String(100), default="bottom")
    safe_region: Mapped[str | None] = mapped_column(String(100), default="80% safety window")
    reading_speed_wpm: Mapped[float] = mapped_column(Float, default=0.0)
    reading_speed_cps: Mapped[float] = mapped_column(Float, default=0.0)
    reading_speed_cpl: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    language: Mapped[str] = mapped_column(String(20), default="en")
    
    # Thumbnail Agent integration fields
    key_phrases: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    importance_score: Mapped[float] = mapped_column(Float, default=0.85)

    quality_score: Mapped[float] = mapped_column(Float, default=0.95)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("SubtitlePackage", back_populates="scene_subtitles")
    segments = relationship("CaptionSegment", back_populates="scene_subtitle", cascade="all, delete-orphan")


class CaptionSegment(Base):
    __tablename__ = "caption_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scene_subtitle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scene_subtitles.id", ondelete="CASCADE"), nullable=False)
    segment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    words: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    reading_speed_wpm: Mapped[float] = mapped_column(Float, default=0.0)
    reading_speed_cps: Mapped[float] = mapped_column(Float, default=0.0)
    reading_speed_cpl: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    scene_subtitle = relationship("SceneSubtitle", back_populates="segments")


class SubtitleTrack(Base):
    __tablename__ = "subtitle_tracks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subtitle_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subtitle_packages.id", ondelete="CASCADE"), nullable=False)
    style_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("caption_style_profiles.id", ondelete="SET NULL"), nullable=True)
    track_name: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="en")
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)
    is_original: Mapped[bool] = mapped_column(Boolean, default=True)
    is_translated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    is_human_edited: Mapped[bool] = mapped_column(Boolean, default=False)

    srt_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    webvtt_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    ass_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    json_timeline_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    burned_caption_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("SubtitlePackage", back_populates="tracks")
    style_profile = relationship("CaptionStyleProfile", back_populates="tracks")


class SubtitleVersion(Base):
    __tablename__ = "subtitle_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subtitle_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subtitle_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")  # INITIAL, OPTIMIZED, REGENERATED
    
    # Snapshot of the subtitle package state including all scene subtitles & tracks
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("SubtitlePackage", back_populates="versions")


# ── AI Music Engine Models ─────────────────────────────────────────────────────

class AudioMixProfile(Base):
    __tablename__ = "audio_mix_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_platform: Mapped[str] = mapped_column(String(100), nullable=False)
    music_volume_db: Mapped[float] = mapped_column(Float, default=-14.0)
    narration_volume_db: Mapped[float] = mapped_column(Float, default=0.0)
    ducking_level_db: Mapped[float] = mapped_column(Float, default=-12.0)
    fade_duration_ms: Mapped[int] = mapped_column(Integer, default=500)
    crossfade_duration_ms: Mapped[int] = mapped_column(Integer, default=800)
    target_lufs: Mapped[float] = mapped_column(Float, default=-14.0)
    true_peak_db: Mapped[float] = mapped_column(Float, default=-1.0)
    sample_rate: Mapped[int] = mapped_column(Integer, default=44100)
    channels: Mapped[int] = mapped_column(Integer, default=2)
    normalization_mode: Mapped[str] = mapped_column(String(50), default="peak_and_lufs")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    jobs = relationship("MusicJob", back_populates="profile")


class MusicJob(Base):
    __tablename__ = "music_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    voice_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_packages.id", ondelete="CASCADE"), nullable=False)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)
    subtitle_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subtitle_packages.id", ondelete="CASCADE"), nullable=True)
    audio_mix_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("audio_mix_profiles.id", ondelete="SET NULL"), nullable=True)
    provider: Mapped[str] = mapped_column(String(100), default="library")
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="VALIDATING")  # VALIDATING, MUSIC_SELECTION, SCENE_MAPPING, TIMELINE_BUILDING, DUCKING, AUDIO_MIXING, LOUDNESS_NORMALIZATION, QUALITY_CHECK, OPTIMIZING, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("AudioMixProfile", back_populates="jobs")
    packages = relationship("MusicPackage", back_populates="job", cascade="all, delete-orphan")


class MusicPackage(Base, BasePackageMixin):
    __tablename__ = "music_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("music_jobs.id", ondelete="CASCADE"), nullable=False)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    voice_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_packages.id", ondelete="CASCADE"), nullable=False)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)
    subtitle_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subtitle_packages.id", ondelete="CASCADE"), nullable=True)
    audio_mix_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("audio_mix_profiles.id", ondelete="SET NULL"), nullable=True)

    # Storage Keys & Master Outputs
    storage_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    separated_music_track: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    narration_track: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    ambient_stem_track: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    sfx_stem_track: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    scene_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    waveform_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    package_manifest: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("MusicJob", back_populates="packages")
    scene_musics = relationship("SceneMusic", back_populates="package", cascade="all, delete-orphan")
    timeline_events = relationship("AudioTimelineEvent", back_populates="package", cascade="all, delete-orphan")
    analysis = relationship("AudioAnalysis", back_populates="package", uselist=False, cascade="all, delete-orphan")
    versions = relationship("MusicVersion", back_populates="package", cascade="all, delete-orphan")


class MusicAsset(Base):
    __tablename__ = "music_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    license_type: Mapped[str] = mapped_column(String(100), default="Creative Commons")
    copyright_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    isrc: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tracks = relationship("MusicTrack", back_populates="asset")


class MusicTrack(Base):
    __tablename__ = "music_tracks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("music_assets.id", ondelete="SET NULL"), nullable=True)
    track_title: Mapped[str] = mapped_column(String(150), nullable=False)
    artist: Mapped[str | None] = mapped_column(String(150), default="AATES AI Audio")
    genre: Mapped[str] = mapped_column(String(100), default="Cinematic")
    mood: Mapped[str] = mapped_column(String(100), default="Inspiring")
    energy_level: Mapped[str] = mapped_column(String(50), default="Medium")
    tempo_bpm: Mapped[int] = mapped_column(Integer, default=120)
    musical_key: Mapped[str] = mapped_column(String(20), default="C Major")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    sample_rate: Mapped[int] = mapped_column(Integer, default=44100)
    channels: Mapped[int] = mapped_column(Integer, default=2)
    is_loopable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_licensed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asset = relationship("MusicAsset", back_populates="tracks")
    cues = relationship("MusicCue", back_populates="track")


class SceneMusic(Base):
    __tablename__ = "scene_musics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    music_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("music_packages.id", ondelete="CASCADE"), nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    track_name: Mapped[str] = mapped_column(String(150), nullable=False)
    genre: Mapped[str] = mapped_column(String(100), default="Cinematic")
    mood: Mapped[str] = mapped_column(String(100), default="Inspiring")
    energy: Mapped[str] = mapped_column(String(50), default="Medium")
    tempo_bpm: Mapped[int] = mapped_column(Integer, default=120)
    musical_key: Mapped[str] = mapped_column(String(20), default="C Major")
    start_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    end_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    fade_in_ms: Mapped[int] = mapped_column(Integer, default=500)
    fade_out_ms: Mapped[int] = mapped_column(Integer, default=500)
    loop_points: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    music_volume_db: Mapped[float] = mapped_column(Float, default=-14.0)
    narration_ducking_db: Mapped[float] = mapped_column(Float, default=-12.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.95)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("MusicPackage", back_populates="scene_musics")
    cues = relationship("MusicCue", back_populates="scene_music", cascade="all, delete-orphan")


class MusicCue(Base):
    __tablename__ = "music_cues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    music_track_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("music_tracks.id", ondelete="SET NULL"), nullable=True)
    scene_music_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("scene_musics.id", ondelete="CASCADE"), nullable=True)
    cue_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cue_purpose: Mapped[str] = mapped_column(String(50), default="background")  # intro, background, transition, outro
    source_start_ms: Mapped[int] = mapped_column(Integer, default=0)
    source_end_ms: Mapped[int] = mapped_column(Integer, default=0)
    trim_start_ms: Mapped[int] = mapped_column(Integer, default=0)
    trim_end_ms: Mapped[int] = mapped_column(Integer, default=0)
    loop_start_ms: Mapped[int] = mapped_column(Integer, default=0)
    loop_end_ms: Mapped[int] = mapped_column(Integer, default=0)
    fade_in_ms: Mapped[int] = mapped_column(Integer, default=500)
    fade_out_ms: Mapped[int] = mapped_column(Integer, default=500)
    gain_db: Mapped[float] = mapped_column(Float, default=0.0)
    emotion_score: Mapped[float] = mapped_column(Float, default=0.88)
    transition_compatibility: Mapped[float] = mapped_column(Float, default=0.92)
    loop_confidence: Mapped[float] = mapped_column(Float, default=0.95)
    crossfade_recommendation: Mapped[int] = mapped_column(Integer, default=800)
    beat_alignment_offset_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    track = relationship("MusicTrack", back_populates="cues")
    scene_music = relationship("SceneMusic", back_populates="cues")
    timeline_events = relationship("AudioTimelineEvent", back_populates="cue")


class AudioTimelineEvent(Base):
    __tablename__ = "audio_timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    music_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("music_packages.id", ondelete="CASCADE"), nullable=False)
    cue_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("music_cues.id", ondelete="SET NULL"), nullable=True)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    gain_db: Mapped[float] = mapped_column(Float, default=0.0)
    pan: Mapped[float] = mapped_column(Float, default=0.0)
    fade_in_ms: Mapped[int] = mapped_column(Integer, default=500)
    fade_out_ms: Mapped[int] = mapped_column(Integer, default=500)
    ducking_state: Mapped[str] = mapped_column(String(50), default="active")
    automation_points: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)  # [{timestamp_ms, value_db, interpolation}]

    package = relationship("MusicPackage", back_populates="timeline_events")
    cue = relationship("MusicCue", back_populates="timeline_events")


class AudioAnalysis(Base):
    __tablename__ = "audio_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    music_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("music_packages.id", ondelete="CASCADE"), nullable=False)
    peak_db: Mapped[float] = mapped_column(Float, default=-1.0)
    lufs: Mapped[float] = mapped_column(Float, default=-14.0)
    dynamic_range_db: Mapped[float] = mapped_column(Float, default=8.5)
    rms_db: Mapped[float] = mapped_column(Float, default=-16.0)
    tempo_bpm: Mapped[int] = mapped_column(Integer, default=120)
    musical_key: Mapped[str] = mapped_column(String(20), default="C Major")
    silence_regions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    speech_regions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    waveform_data: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    spectrum_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("MusicPackage", back_populates="analysis")


class MusicVersion(Base):
    __tablename__ = "music_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    music_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("music_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")  # INITIAL, OPTIMIZED, REMIXED, REGENERATED
    
    # Snapshot of the music package state
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("MusicPackage", back_populates="versions")


# ── AI Thumbnail Engine Models ──────────────────────────────────────────────────

class ThumbnailStyleProfile(Base):
    __tablename__ = "thumbnail_style_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    font_family: Mapped[str] = mapped_column(String(100), default="Inter Black")
    font_size_pt: Mapped[int] = mapped_column(Integer, default=72)
    font_weight: Mapped[str] = mapped_column(String(50), default="Bold")
    primary_color: Mapped[str] = mapped_column(String(50), default="#FFFFFF")
    accent_color: Mapped[str] = mapped_column(String(50), default="#FFD700")
    outline_color: Mapped[str] = mapped_column(String(50), default="#000000")
    shadow_style: Mapped[str] = mapped_column(String(100), default="Heavy Drop Shadow")
    background_style: Mapped[str] = mapped_column(String(100), default="High Contrast Gradient")
    logo_placement: Mapped[str] = mapped_column(String(50), default="top_right")
    safe_margins: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)  # {top: 40, bottom: 40, left: 40, right: 40}
    emoji_policy: Mapped[str] = mapped_column(String(50), default="allowed")
    aspect_ratio: Mapped[str] = mapped_column(String(20), default="16:9")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    jobs = relationship("ThumbnailJob", back_populates="style_profile")


class CompositionTemplate(Base):
    __tablename__ = "composition_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    layout_type: Mapped[str] = mapped_column(String(50), default="left_focus")  # left_focus, right_focus, centered, split, minimal
    subject_region: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    headline_region: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    secondary_text_region: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    logo_region: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    safe_margins: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    grid_definition: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    aspect_ratio: Mapped[str] = mapped_column(String(20), default="16:9")
    priority_rules: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    variants = relationship("ThumbnailVariant", back_populates="template")


class ThumbnailJob(Base):
    __tablename__ = "thumbnail_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    image_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("image_packages.id", ondelete="CASCADE"), nullable=False)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)
    subtitle_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subtitle_packages.id", ondelete="CASCADE"), nullable=True)
    music_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("music_packages.id", ondelete="CASCADE"), nullable=True)
    thumbnail_style_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_style_profiles.id", ondelete="SET NULL"), nullable=True)
    provider: Mapped[str] = mapped_column(String(100), default="template")
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="VALIDATING")  # VALIDATING, FRAME_SELECTION, FRAME_ANALYSIS, TEXT_SELECTION, LAYOUT_COMPOSITION, STYLE_APPLICATION, VARIANT_GENERATION, QUALITY_SCORING, OPTIMIZING, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    style_profile = relationship("ThumbnailStyleProfile", back_populates="jobs")
    packages = relationship("ThumbnailPackage", back_populates="job", cascade="all, delete-orphan")


class ThumbnailPackage(Base, BasePackageMixin):
    __tablename__ = "thumbnail_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_jobs.id", ondelete="CASCADE"), nullable=False)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    image_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("image_packages.id", ondelete="CASCADE"), nullable=False)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)
    subtitle_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subtitle_packages.id", ondelete="CASCADE"), nullable=True)
    music_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("music_packages.id", ondelete="CASCADE"), nullable=True)
    thumbnail_style_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_style_profiles.id", ondelete="SET NULL"), nullable=True)

    primary_thumbnail_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    selected_variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    variant_count: Mapped[int] = mapped_column(Integer, default=0)
    package_manifest: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("ThumbnailJob", back_populates="packages")
    variants = relationship("ThumbnailVariant", back_populates="package", cascade="all, delete-orphan")
    analysis = relationship("ThumbnailAnalysis", back_populates="package", uselist=False, cascade="all, delete-orphan")
    versions = relationship("ThumbnailVersion", back_populates="package", cascade="all, delete-orphan")
    experiments = relationship("ThumbnailExperiment", back_populates="package", cascade="all, delete-orphan")


class ThumbnailAsset(Base):
    __tablename__ = "thumbnail_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    public_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    preview_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    width: Mapped[int] = mapped_column(Integer, default=1280)
    height: Mapped[int] = mapped_column(Integer, default=720)
    format: Mapped[str] = mapped_column(String(20), default="png")
    compression: Mapped[str] = mapped_column(String(50), default="high_quality")
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    variants = relationship("ThumbnailVariant", back_populates="asset")


class ThumbnailVariant(Base):
    __tablename__ = "thumbnail_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thumbnail_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_packages.id", ondelete="CASCADE"), nullable=False)
    thumbnail_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_assets.id", ondelete="SET NULL"), nullable=True)
    composition_template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("composition_templates.id", ondelete="SET NULL"), nullable=True)
    variant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, default=1)
    source_frame_key: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    
    # Explicit Text Hierarchy
    primary_hook: Mapped[str] = mapped_column(String(100), nullable=False)
    secondary_hook: Mapped[str | None] = mapped_column(String(150), nullable=True)
    badge_text: Mapped[str | None] = mapped_column(String(50), nullable=True)
    brand_label: Mapped[str | None] = mapped_column(String(50), nullable=True)

    layout_type: Mapped[str] = mapped_column(String(50), default="left_focus")
    face_region: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    subject_region: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    background_region: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    # Separate Heuristic and Learned Scores
    contrast_score: Mapped[float] = mapped_column(Float, default=0.9)
    readability_score: Mapped[float] = mapped_column(Float, default=0.92)
    composition_score: Mapped[float] = mapped_column(Float, default=0.88)
    brand_score: Mapped[float] = mapped_column(Float, default=0.95)
    ctr_prediction_score: Mapped[float] = mapped_column(Float, default=0.94)
    quality_score: Mapped[float] = mapped_column(Float, default=0.94)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("ThumbnailPackage", back_populates="variants")
    asset = relationship("ThumbnailAsset", back_populates="variants")
    template = relationship("CompositionTemplate", back_populates="variants")
    score = relationship("ThumbnailScore", back_populates="variant", uselist=False, cascade="all, delete-orphan")


class ThumbnailAnalysis(Base):
    __tablename__ = "thumbnail_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thumbnail_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_packages.id", ondelete="CASCADE"), nullable=False)
    blur_score: Mapped[float] = mapped_column(Float, default=0.05)
    brightness: Mapped[float] = mapped_column(Float, default=0.65)
    contrast_ratio: Mapped[float] = mapped_column(Float, default=6.2)  # WCAG >= 4.5:1
    entropy: Mapped[float] = mapped_column(Float, default=7.4)
    dominant_colors: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    face_count: Mapped[int] = mapped_column(Integer, default=1)
    face_confidence: Mapped[float] = mapped_column(Float, default=0.95)
    object_regions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    saliency_map: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ocr_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    edge_density: Mapped[float] = mapped_column(Float, default=0.45)
    color_histogram: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("ThumbnailPackage", back_populates="analysis")


class ThumbnailScore(Base):
    __tablename__ = "thumbnail_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thumbnail_variant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_variants.id", ondelete="CASCADE"), nullable=False)
    contrast_score: Mapped[float] = mapped_column(Float, default=0.92)
    sharpness_score: Mapped[float] = mapped_column(Float, default=0.95)
    face_visibility_score: Mapped[float] = mapped_column(Float, default=0.90)
    subject_prominence_score: Mapped[float] = mapped_column(Float, default=0.88)
    text_readability_score: Mapped[float] = mapped_column(Float, default=0.94)
    color_harmony_score: Mapped[float] = mapped_column(Float, default=0.91)
    rule_of_thirds_score: Mapped[float] = mapped_column(Float, default=0.89)
    emotion_score: Mapped[float] = mapped_column(Float, default=0.87)
    brand_consistency_score: Mapped[float] = mapped_column(Float, default=0.96)
    
    # Dual Scoring Architecture
    heuristic_score: Mapped[float] = mapped_column(Float, default=0.92)
    learned_score: Mapped[float] = mapped_column(Float, default=0.94)
    overall_score: Mapped[float] = mapped_column(Float, default=0.93)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    variant = relationship("ThumbnailVariant", back_populates="score")


class ThumbnailVersion(Base):
    __tablename__ = "thumbnail_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thumbnail_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")  # INITIAL, OPTIMIZED, REGENERATED
    
    # Snapshot of the thumbnail package state
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("ThumbnailPackage", back_populates="versions")


class ThumbnailExperiment(Base):
    __tablename__ = "thumbnail_experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thumbnail_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_packages.id", ondelete="CASCADE"), nullable=False)
    variant_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    variant_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), default="youtube")
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED")  # SCHEDULED, RUNNING, COMPLETED
    evaluation_window_hours: Mapped[int] = mapped_column(Integer, default=72)
    statistical_significance: Mapped[float] = mapped_column(Float, default=0.95)
    algorithm_version: Mapped[str | None] = mapped_column(String(50), default="v1.0")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    winner_variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    winning_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("ThumbnailPackage", back_populates="experiments")


# ── AI Quality Engine Models ──────────────────────────────────────────────────

class QualityPolicy(Base):
    __tablename__ = "quality_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # Production, YouTube, Instagram, Shorts, Enterprise, Custom
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(50), default="v1.0")
    rule_set_version: Mapped[str] = mapped_column(String(50), default="v1.0")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_readiness_score: Mapped[float] = mapped_column(Float, default=0.85)
    allow_critical_issues: Mapped[bool] = mapped_column(Boolean, default=False)
    dimension_weights: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)  # {Content: 0.15, Media: 0.2, Accessibility: 0.15, Brand: 0.15, Metadata: 0.15, Technical: 0.1, Publishing: 0.1}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    jobs = relationship("QualityJob", back_populates="policy")
    rules = relationship("QualityRule", back_populates="policy", cascade="all, delete-orphan")


class QualityRule(Base):
    __tablename__ = "quality_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quality_policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_policies.id", ondelete="CASCADE"), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(150), nullable=False)
    dimension: Mapped[str] = mapped_column(String(50), default="Technical")  # Content, Media, Accessibility, Brand, Metadata, Technical, Publishing
    target_package: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), default=">=")  # >=, <=, ==, !=, in
    threshold_value: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="MAJOR")  # CRITICAL, MAJOR, MINOR, INFO
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    policy = relationship("QualityPolicy", back_populates="rules")


class QualityJob(Base):
    __tablename__ = "quality_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    image_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("image_packages.id", ondelete="CASCADE"), nullable=False)
    voice_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_packages.id", ondelete="CASCADE"), nullable=False)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)
    subtitle_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subtitle_packages.id", ondelete="CASCADE"), nullable=True)
    music_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("music_packages.id", ondelete="CASCADE"), nullable=True)
    thumbnail_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_packages.id", ondelete="CASCADE"), nullable=True)
    quality_policy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_policies.id", ondelete="SET NULL"), nullable=True)
    provider: Mapped[str] = mapped_column(String(100), default="policy_engine")
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="VALIDATING")  # VALIDATING, GRAPH_CONSTRUCTION, TELEMETRY_AGGREGATION, POLICY_EVALUATION, CROSS_PACKAGE_CHECK, ISSUE_CLASSIFICATION, SCORING, REPORT_GENERATION, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    policy = relationship("QualityPolicy", back_populates="jobs")
    packages = relationship("QualityPackage", back_populates="job", cascade="all, delete-orphan")


class QualityPackage(Base, BasePackageMixin):
    __tablename__ = "quality_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_jobs.id", ondelete="CASCADE"), nullable=False)
    script_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("script_packages.id", ondelete="CASCADE"), nullable=False)
    image_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("image_packages.id", ondelete="CASCADE"), nullable=False)
    voice_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("voice_packages.id", ondelete="CASCADE"), nullable=False)
    video_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("video_packages.id", ondelete="CASCADE"), nullable=False)
    subtitle_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subtitle_packages.id", ondelete="CASCADE"), nullable=True)
    music_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("music_packages.id", ondelete="CASCADE"), nullable=True)
    thumbnail_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_packages.id", ondelete="CASCADE"), nullable=True)
    quality_policy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_policies.id", ondelete="SET NULL"), nullable=True)

    # Governance & Publishing Status Lifecycle
    publishing_lifecycle_state: Mapped[str] = mapped_column(String(50), default="Draft")  # Draft -> Validated -> Approved -> Published -> Archived
    production_readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_approved_for_publishing: Mapped[bool] = mapped_column(Boolean, default=False)
    critical_issue_count: Mapped[int] = mapped_column(Integer, default=0)
    major_issue_count: Mapped[int] = mapped_column(Integer, default=0)
    minor_issue_count: Mapped[int] = mapped_column(Integer, default=0)
    dimension_scores: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    aggregated_telemetry: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    package_manifest: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("QualityJob", back_populates="packages")
    checks = relationship("QualityCheck", back_populates="package", cascade="all, delete-orphan")
    issues = relationship("QualityIssue", back_populates="package", cascade="all, delete-orphan")
    versions = relationship("QualityVersion", back_populates="package", cascade="all, delete-orphan")
    remediation_tasks = relationship("RemediationTask", back_populates="package", cascade="all, delete-orphan")


class QualityCheck(Base):
    __tablename__ = "quality_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quality_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_packages.id", ondelete="CASCADE"), nullable=False)
    package_type: Mapped[str] = mapped_column(String(100), nullable=False)
    dimension: Mapped[str] = mapped_column(String(50), default="Technical")
    check_name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PASSED")  # PASSED, WARNING, FAILED
    evaluated_value: Mapped[str] = mapped_column(String(255), nullable=False)
    target_threshold: Mapped[str] = mapped_column(String(255), nullable=False)
    execution_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("QualityPackage", back_populates="checks")
    issues = relationship("QualityIssue", back_populates="check", cascade="all, delete-orphan")


class QualityIssue(Base):
    __tablename__ = "quality_issues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quality_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_packages.id", ondelete="CASCADE"), nullable=False)
    quality_check_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_checks.id", ondelete="SET NULL"), nullable=True)
    issue_code: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="MAJOR")  # CRITICAL, MAJOR, MINOR, INFO
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impacted_component: Mapped[str] = mapped_column(String(100), nullable=False)
    remediation_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("QualityPackage", back_populates="issues")
    check = relationship("QualityCheck", back_populates="issues")
    evidence_items = relationship("QualityEvidence", back_populates="issue", cascade="all, delete-orphan")
    recommendations = relationship("QualityRecommendation", back_populates="issue", cascade="all, delete-orphan")


class QualityEvidence(Base):
    __tablename__ = "quality_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quality_issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_issues.id", ondelete="CASCADE"), nullable=False)
    source_package: Mapped[str] = mapped_column(String(100), nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    timestamp_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    observed_value: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_value: Mapped[str] = mapped_column(String(255), nullable=False)
    snapshot_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    issue = relationship("QualityIssue", back_populates="evidence_items")


class QualityRecommendation(Base):
    __tablename__ = "quality_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quality_issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_issues.id", ondelete="CASCADE"), nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="HIGH")  # HIGH, MEDIUM, LOW
    target_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    auto_fix_available: Mapped[bool] = mapped_column(Boolean, default=True)
    estimated_impact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    issue = relationship("QualityIssue", back_populates="recommendations")


class RemediationTask(Base):
    __tablename__ = "remediation_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quality_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_packages.id", ondelete="CASCADE"), nullable=False)
    target_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("QualityPackage", back_populates="remediation_tasks")


class QualityVersion(Base):
    __tablename__ = "quality_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quality_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")  # INITIAL, RE_EVALUATED, OVERRIDDEN
    
    # Snapshot of the quality package state
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("QualityPackage", back_populates="versions")


# ── AI Instagram Publishing Engine Models ──────────────────────────────────────

class InstagramPublishJob(Base):
    __tablename__ = "instagram_publish_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quality_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_packages.id", ondelete="CASCADE"), nullable=False)
    platform_media_type: Mapped[str] = mapped_column(String(50), default="Reels")  # Reels, Feed
    provider: Mapped[str] = mapped_column(String(100), default="instagram_provider")
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, RETRYING, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="VALIDATING")  # VALIDATING, QUALITY_GATE, MEDIA_TRANSFORMATION, MEDIA_VALIDATION, UPLOAD, PUBLISH, STATUS_SYNC, INSIGHT_INITIALIZATION, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    packages = relationship("PublicationPackage", back_populates="job", cascade="all, delete-orphan")
    attempts_history = relationship("PublishingAttempt", back_populates="job", cascade="all, delete-orphan")


class PublicationPackage(Base, BasePackageMixin):
    __tablename__ = "publication_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instagram_publish_jobs.id", ondelete="CASCADE"), nullable=False)
    quality_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quality_packages.id", ondelete="CASCADE"), nullable=False)
    
    # Governance & Publishing Status Lifecycle
    publishing_lifecycle_state: Mapped[str] = mapped_column(String(50), default="Draft")  # Draft -> Queued -> Uploading -> Published -> Synchronizing -> Completed -> Archived
    platform_name: Mapped[str] = mapped_column(String(50), default="instagram")
    platform_profile_id: Mapped[str] = mapped_column(String(100), default="instagram_reels")
    publication_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    package_manifest: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("InstagramPublishJob", back_populates="packages")
    publications = relationship("InstagramPublication", back_populates="package", cascade="all, delete-orphan")
    versions = relationship("InstagramVersion", back_populates="package", cascade="all, delete-orphan")


class InstagramPublication(Base):
    __tablename__ = "instagram_publications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publication_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publication_packages.id", ondelete="CASCADE"), nullable=False)
    instagram_media_id: Mapped[str] = mapped_column(String(255), nullable=False)
    container_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    permalink: Mapped[str] = mapped_column(String(2048), nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    alt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    visibility: Mapped[str] = mapped_column(String(50), default="PUBLIC")
    publishing_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("PublicationPackage", back_populates="publications")
    media_assets = relationship("InstagramMediaAsset", back_populates="publication", cascade="all, delete-orphan")
    insights = relationship("InstagramInsightSnapshot", back_populates="publication", cascade="all, delete-orphan")


class InstagramMediaAsset(Base):
    __tablename__ = "instagram_media_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instagram_publications.id", ondelete="CASCADE"), nullable=False)
    video_asset_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    cover_image_key: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    aspect_ratio: Mapped[str] = mapped_column(String(20), default="9:16")
    resolution: Mapped[str] = mapped_column(String(50), default="1080x1920")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    codec: Mapped[str] = mapped_column(String(50), default="h264")
    bitrate: Mapped[int] = mapped_column(Integer, default=5000000)
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    publication = relationship("InstagramPublication", back_populates="media_assets")


class PublishingAttempt(Base):
    __tablename__ = "publishing_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instagram_publish_jobs.id", ondelete="CASCADE"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    api_endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    http_status_code: Mapped[int] = mapped_column(Integer, default=200)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    api_response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("InstagramPublishJob", back_populates="attempts_history")


class InstagramInsightSnapshot(Base):
    __tablename__ = "instagram_insight_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instagram_publications.id", ondelete="CASCADE"), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    views: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    profile_visits: Mapped[int] = mapped_column(Integer, default=0)
    follows_attributed: Mapped[int] = mapped_column(Integer, default=0)
    watch_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    publication = relationship("InstagramPublication", back_populates="insights")


class InstagramVersion(Base):
    __tablename__ = "instagram_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publication_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publication_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")  # INITIAL, REPUBLISHED, UPDATED
    
    # Snapshot of the publication package state
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("PublicationPackage", back_populates="versions")


# ── AI Analytics & Learning Engine Models ──────────────────────────────────────

class LearningJob(Base):
    __tablename__ = "learning_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, PROCESSING, SUCCESS, FAILED, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="COLLECTING")  # COLLECTING, NORMALIZING, CORRELATING, PATTERN_DISCOVERY, EXPERIMENT_ANALYSIS, RECOMMENDATION_GENERATION, LEARNING_UPDATE, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    target_platform: Mapped[str] = mapped_column(String(50), default="all")  # instagram, youtube, all
    learning_window_days: Mapped[int] = mapped_column(Integer, default=30)
    dataset_size: Mapped[int] = mapped_column(Integer, default=0)
    learning_mode: Mapped[str] = mapped_column(String(50), default="batch")  # batch, incremental
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    datasets = relationship("LearningDataset", back_populates="job", cascade="all, delete-orphan")
    packages = relationship("LearningPackage", back_populates="job", cascade="all, delete-orphan")


class LearningDataset(Base):
    __tablename__ = "learning_datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_jobs.id", ondelete="CASCADE"), nullable=False)
    dataset_name: Mapped[str] = mapped_column(String(255), default="AATES Default Training Set")
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    feature_vectors_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("LearningJob", back_populates="datasets")
    packages = relationship("LearningPackage", back_populates="dataset", cascade="all, delete-orphan")


class LearningPackage(Base, BasePackageMixin):
    __tablename__ = "learning_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_jobs.id", ondelete="CASCADE"), nullable=False)
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_datasets.id", ondelete="CASCADE"), nullable=False)
    
    target_platform: Mapped[str] = mapped_column(String(50), default="all")
    learning_confidence: Mapped[float] = mapped_column(Float, default=0.85)
    model_version: Mapped[str] = mapped_column(String(50), default="v1.0")
    
    feature_importance_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    package_manifest: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("LearningJob", back_populates="packages")
    dataset = relationship("LearningDataset", back_populates="packages")
    performance_snapshots = relationship("PerformanceSnapshot", back_populates="package", cascade="all, delete-orphan")
    signals = relationship("LearningSignal", back_populates="package", cascade="all, delete-orphan")
    recommendations = relationship("LearningRecommendation", back_populates="package", cascade="all, delete-orphan")
    experiments = relationship("ExperimentResult", back_populates="package", cascade="all, delete-orphan")
    versions = relationship("LearningVersion", back_populates="package", cascade="all, delete-orphan")


class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_packages.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), default="all")
    window_days: Mapped[int] = mapped_column(Integer, default=30)
    total_publications: Mapped[int] = mapped_column(Integer, default=0)
    total_views: Mapped[int] = mapped_column(Integer, default=0)
    total_reach: Mapped[int] = mapped_column(Integer, default=0)
    avg_ctr: Mapped[float] = mapped_column(Float, default=0.0)
    avg_engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_watch_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("LearningPackage", back_populates="performance_snapshots")


class LearningSignal(Base):
    __tablename__ = "learning_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_packages.id", ondelete="CASCADE"), nullable=False)
    signal_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="Hook")  # Hook, Thumbnail, Pacing, Schedule, Music, Caption
    correlation_coefficient: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.80)
    platform: Mapped[str] = mapped_column(String(50), default="all")
    applicable_agents: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    causality_level: Mapped[str] = mapped_column(String(50), default="CORRELATED")  # CORRELATED, EXPERIMENT_SUPPORTED
    evidence_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("LearningPackage", back_populates="signals")


class LearningRecommendation(Base):
    __tablename__ = "learning_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_packages.id", ondelete="CASCADE"), nullable=False)
    target_agent: Mapped[str] = mapped_column(String(100), nullable=False)  # Research, Script, Image, Voice, Video, Subtitle, Music, Thumbnail, Publishing
    category: Mapped[str] = mapped_column(String(100), default="Content Optimization")
    priority: Mapped[str] = mapped_column(String(50), default="HIGH")  # CRITICAL, HIGH, MEDIUM, LOW
    confidence_score: Mapped[float] = mapped_column(Float, default=0.85)
    expected_impact: Mapped[str] = mapped_column(String(255), default="+15% Projected CTR Increase")
    suggested_action: Mapped[str] = mapped_column(Text, nullable=False)
    action_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    evidence_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("LearningPackage", back_populates="recommendations")
    feedbacks = relationship("RecommendationFeedback", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationFeedback(Base):
    __tablename__ = "learning_recommendation_feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_recommendations.id", ondelete="CASCADE"), nullable=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="MEASURING")  # APPLIED, SKIPPED, MEASURING, SUCCESSFUL, FAILED
    initial_metric: Mapped[float] = mapped_column(Float, default=0.0)
    measured_metric: Mapped[float] = mapped_column(Float, default=0.0)
    impact_percent: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_update: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recommendation = relationship("LearningRecommendation", back_populates="feedbacks")


class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_packages.id", ondelete="CASCADE"), nullable=False)
    experiment_id: Mapped[str] = mapped_column(String(255), nullable=False)
    experiment_type: Mapped[str] = mapped_column(String(100), default="Thumbnail A/B Test")  # Thumbnail A/B Test, Publishing Time, Caption Variant
    winning_variant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.92)
    metric_lift_percent: Mapped[float] = mapped_column(Float, default=18.5)
    insights_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("LearningPackage", back_populates="experiments")


class LearningVersion(Base):
    __tablename__ = "learning_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")  # INITIAL, RE_EVALUATED, UPDATED
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("LearningPackage", back_populates="versions")


class LearningModelProfile(Base):
    __tablename__ = "learning_model_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="v1.0")
    training_window_days: Mapped[int] = mapped_column(Integer, default=30)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.75)
    supported_platforms: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FeatureDefinitionModel(Base):
    __tablename__ = "feature_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    data_type: Mapped[str] = mapped_column(String(50), default="float")
    source_packages: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(100), nullable=False)
    normalization_method: Mapped[str] = mapped_column(String(100), default="min_max")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── AI Automation Engine Models ──────────────────────────────────────────────────

class AutomationJob(Base):
    __tablename__ = "automation_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, WAITING, PROCESSING, SUCCESS, FAILED, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="WAITING")  # WAITING, TRIGGER_EVALUATION, POLICY_MATCHING, DECISION_GENERATION, ACTION_EXECUTION, OUTCOME_VALIDATION, AUDIT_LOGGING, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    trigger_type: Mapped[str] = mapped_column(String(50), default="MANUAL_TRIGGER")
    source_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_platform: Mapped[str] = mapped_column(String(50), default="all")
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    packages = relationship("AutomationPackage", back_populates="job", cascade="all, delete-orphan")


class AutomationPolicyModel(Base):
    __tablename__ = "automation_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    trigger_types: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    target_workflow_id: Mapped[str] = mapped_column(String(100), default="AUTONOMOUS_PUBLISHING")
    cooldown_sec: Mapped[int] = mapped_column(Integer, default=60)
    retry_rules: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    platforms: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    applicable_agents: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AutomationTrigger(Base):
    __tablename__ = "automation_triggers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger_id: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_component: Mapped[str] = mapped_column(String(100), nullable=False)
    source_package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_platform: Mapped[str] = mapped_column(String(50), default="all")
    event_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AutomationDecision(Base):
    __tablename__ = "automation_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[str] = mapped_column(String(100), nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(100), nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.95)
    condition_evaluations: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    resource_lock_acquired: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AutomationWorkflowDefinition(Base):
    __tablename__ = "automation_workflow_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    steps_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    timeout_sec: Mapped[int] = mapped_column(Integer, default=600)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AutomationWorkflowInstance(Base):
    __tablename__ = "automation_workflow_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    workflow_id: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_id: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    current_step: Mapped[str] = mapped_column(String(100), default="START")
    execution_owner: Mapped[str] = mapped_column(String(100), default="automation-worker-0")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    context_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    compensation_log: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    step_executions = relationship("AutomationWorkflowStepExecution", back_populates="instance", cascade="all, delete-orphan")


class AutomationWorkflowStepExecution(Base):
    __tablename__ = "automation_workflow_step_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("automation_workflow_instances.id", ondelete="CASCADE"), nullable=False)
    step_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    execution_ms: Mapped[int] = mapped_column(Integer, default=0)
    result_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    compensation_executed: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    instance = relationship("AutomationWorkflowInstance", back_populates="step_executions")


class ResourceLockModel(Base):
    __tablename__ = "resource_locks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    owner_workflow_instance_id: Mapped[str] = mapped_column(String(100), nullable=False)
    locked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AutomationPackage(Base, BasePackageMixin):
    __tablename__ = "automation_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("automation_jobs.id", ondelete="CASCADE"), nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_id: Mapped[str] = mapped_column(String(100), nullable=False)
    target_platform: Mapped[str] = mapped_column(String(50), default="all")
    execution_confidence: Mapped[float] = mapped_column(Float, default=0.95)
    executed_actions_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_context_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    package_manifest: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("AutomationJob", back_populates="packages")
    versions = relationship("AutomationVersion", back_populates="package", cascade="all, delete-orphan")


class AutomationVersion(Base):
    __tablename__ = "automation_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    automation_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("automation_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("AutomationPackage", back_populates="versions")


# ── AI Multi-Agent Orchestrator Models ──────────────────────────────────────────

class OrchestrationJob(Base):
    __tablename__ = "orchestration_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED")  # QUEUED, OBJECTIVE_ANALYSIS, PROCESSING, SUCCESS, FAILED, CANCELLED
    stage: Mapped[str] = mapped_column(String(50), default="OBJECTIVE_ANALYSIS")  # OBJECTIVE_ANALYSIS, PLAN_GENERATION, TASK_GRAPH_BUILDING, RESOURCE_ALLOCATION, WORKFLOW_DISPATCH, EXECUTION_MONITORING, ADAPTIVE_REPLANNING, FINALIZATION, COMPLETED
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    objective_type: Mapped[str] = mapped_column(String(100), default="GENERATE_LONGFORM_VIDEO")
    target_platform: Mapped[str] = mapped_column(String(50), default="all")
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    packages = relationship("OrchestrationPackage", back_populates="job", cascade="all, delete-orphan")


class ObjectiveModel(Base):
    __tablename__ = "orchestrator_objectives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objective_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_platform: Mapped[str] = mapped_column(String(50), default="all")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    target_kpi: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExecutionPlanModel(Base):
    __tablename__ = "execution_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    objective_id: Mapped[str] = mapped_column(String(100), nullable=False)
    objective_type: Mapped[str] = mapped_column(String(100), nullable=False)
    required_agents: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    estimated_duration_sec: Mapped[int] = mapped_column(Integer, default=300)
    parallelism_factor: Mapped[int] = mapped_column(Integer, default=2)
    risk_score: Mapped[float] = mapped_column(Float, default=0.15)
    expected_resources: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExecutionGraphModel(Base):
    __tablename__ = "execution_graphs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    plan_id: Mapped[str] = mapped_column(String(100), nullable=False)
    critical_path: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    nodes = relationship("TaskNodeModel", back_populates="graph", cascade="all, delete-orphan")


class TaskNodeModel(Base):
    __tablename__ = "task_nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("execution_graphs.id", ondelete="CASCADE"), nullable=False)
    node_id: Mapped[str] = mapped_column(String(100), nullable=False)
    target_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    depends_on: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    estimated_duration_sec: Mapped[int] = mapped_column(Integer, default=30)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    retry_policy: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    resource_requirements: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    result_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    graph = relationship("ExecutionGraphModel", back_populates="nodes")


class TaskDependencyModel(Base):
    __tablename__ = "task_dependencies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_node_id: Mapped[str] = mapped_column(String(100), nullable=False)
    child_node_id: Mapped[str] = mapped_column(String(100), nullable=False)
    dependency_type: Mapped[str] = mapped_column(String(50), default="STRONG")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AgentAssignmentModel(Base):
    __tablename__ = "agent_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id: Mapped[str] = mapped_column(String(100), nullable=False)
    target_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_worker_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ASSIGNED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ResourceReservationModel(Base):
    __tablename__ = "resource_reservations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reservation_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    allocated_to_node: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExecutionCheckpointModel(Base):
    __tablename__ = "execution_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orchestration_jobs.id", ondelete="CASCADE"), nullable=False)
    checkpoint_name: Mapped[str] = mapped_column(String(100), nullable=False)
    completed_nodes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    state_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OrchestrationDecisionModel(Base):
    __tablename__ = "orchestration_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objective_id: Mapped[str] = mapped_column(String(100), nullable=False)
    decision_type: Mapped[str] = mapped_column(String(100), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.96)
    action_taken: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OrchestrationPackage(Base, BasePackageMixin):
    __tablename__ = "orchestration_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orchestration_jobs.id", ondelete="CASCADE"), nullable=False)
    objective_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_platform: Mapped[str] = mapped_column(String(50), default="all")
    orchestration_confidence: Mapped[float] = mapped_column(Float, default=0.96)
    executed_nodes_count: Mapped[int] = mapped_column(Integer, default=0)
    total_nodes_count: Mapped[int] = mapped_column(Integer, default=0)
    plan_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    dag_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    package_manifest: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("OrchestrationJob", back_populates="packages")
    versions = relationship("OrchestrationVersion", back_populates="package", cascade="all, delete-orphan")


class OrchestrationVersion(Base):
    __tablename__ = "orchestration_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchestration_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orchestration_packages.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lineage_action: Mapped[str] = mapped_column(String(50), default="INITIAL")
    assets_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    package = relationship("OrchestrationPackage", back_populates="versions")













