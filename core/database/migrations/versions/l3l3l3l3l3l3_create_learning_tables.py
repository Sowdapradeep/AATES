"""Create learning engine tables

Revision ID: l3l3l3l3l3l3
Revises: k2k2k2k2k2k2
Create Date: 2026-07-20 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l3l3l3l3l3l3'
down_revision: Union[str, Sequence[str], None] = 'k2k2k2k2k2k2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. learning_jobs
    op.create_table(
        "learning_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="QUEUED"),
        sa.Column("stage", sa.String(length=50), nullable=False, server_default="COLLECTING"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("worker_id", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_platform", sa.String(length=50), nullable=False, server_default="all"),
        sa.Column("learning_window_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("dataset_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("learning_mode", sa.String(length=50), nullable=False, server_default="batch"),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. learning_datasets
    op.create_table(
        "learning_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_name", sa.String(length=255), nullable=False, server_default="AATES Default Training Set"),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("feature_vectors_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["learning_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. learning_packages
    op.create_table(
        "learning_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_platform", sa.String(length=50), nullable=False, server_default="all"),
        sa.Column("learning_confidence", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("model_version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("feature_importance_snapshot", sa.JSON(), nullable=True),
        sa.Column("package_manifest", sa.JSON(), nullable=True),
        # BasePackageMixin fields
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_agent", sa.String(length=100), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=50), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("telemetry_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dataset_id"], ["learning_datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["learning_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. performance_snapshots
    op.create_table(
        "performance_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learning_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False, server_default="all"),
        sa.Column("window_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("total_publications", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_reach", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_ctr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_engagement_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_watch_time_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["learning_package_id"], ["learning_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. learning_signals
    op.create_table(
        "learning_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learning_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_key", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="Hook"),
        sa.Column("correlation_coefficient", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.80"),
        sa.Column("platform", sa.String(length=50), nullable=False, server_default="all"),
        sa.Column("applicable_agents", sa.JSON(), nullable=False),
        sa.Column("causality_level", sa.String(length=50), nullable=False, server_default="CORRELATED"),
        sa.Column("evidence_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["learning_package_id"], ["learning_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 6. recommendations
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learning_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_agent", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="Content Optimization"),
        sa.Column("priority", sa.String(length=50), nullable=False, server_default="HIGH"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("expected_impact", sa.String(length=255), nullable=False, server_default="+15% Projected CTR Increase"),
        sa.Column("suggested_action", sa.Text(), nullable=False),
        sa.Column("action_payload", sa.JSON(), nullable=True),
        sa.Column("evidence_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["learning_package_id"], ["learning_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 7. recommendation_feedbacks
    op.create_table(
        "recommendation_feedbacks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="MEASURING"),
        sa.Column("initial_metric", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("measured_metric", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("impact_percent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("confidence_update", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 8. experiment_results
    op.create_table(
        "experiment_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learning_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("experiment_id", sa.String(length=255), nullable=False),
        sa.Column("experiment_type", sa.String(length=100), nullable=False, server_default="Thumbnail A/B Test"),
        sa.Column("winning_variant_id", sa.String(length=255), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.92"),
        sa.Column("metric_lift_percent", sa.Float(), nullable=False, server_default="18.5"),
        sa.Column("insights_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["learning_package_id"], ["learning_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 9. learning_versions
    op.create_table(
        "learning_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learning_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["learning_package_id"], ["learning_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 10. learning_model_profiles
    op.create_table(
        "learning_model_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("training_window_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("confidence_threshold", sa.Float(), nullable=False, server_default="0.75"),
        sa.Column("supported_platforms", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 11. feature_definitions
    op.create_table(
        "feature_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("data_type", sa.String(length=50), nullable=False, server_default="float"),
        sa.Column("source_packages", sa.JSON(), nullable=False),
        sa.Column("extraction_method", sa.String(length=100), nullable=False),
        sa.Column("normalization_method", sa.String(length=100), nullable=False, server_default="min_max"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("feature_definitions")
    op.drop_table("learning_model_profiles")
    op.drop_table("learning_versions")
    op.drop_table("experiment_results")
    op.drop_table("recommendation_feedbacks")
    op.drop_table("recommendations")
    op.drop_table("learning_signals")
    op.drop_table("performance_snapshots")
    op.drop_table("learning_packages")
    op.drop_table("learning_datasets")
    op.drop_table("learning_jobs")
