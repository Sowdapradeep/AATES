"""Create quality tables

Revision ID: j1j1j1j1j1j1
Revises: i9i9i9i9i9i9
Create Date: 2026-07-20 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'j1j1j1j1j1j1'
down_revision: Union[str, Sequence[str], None] = 'i9i9i9i9i9i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. quality_policies
    op.create_table(
        "quality_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("policy_version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("rule_set_version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("min_readiness_score", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("allow_critical_issues", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("dimension_weights", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. quality_rules
    op.create_table(
        "quality_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_policy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_name", sa.String(length=150), nullable=False),
        sa.Column("dimension", sa.String(length=50), nullable=False, server_default="Technical"),
        sa.Column("target_package", sa.String(length=100), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("operator", sa.String(length=20), nullable=False, server_default=">="),
        sa.Column("threshold_value", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="MAJOR"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["quality_policy_id"], ["quality_policies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. quality_jobs
    op.create_table(
        "quality_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voice_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtitle_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("music_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("thumbnail_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quality_policy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=False, server_default="policy_engine"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="QUEUED"),
        sa.Column("stage", sa.String(length=50), nullable=False, server_default="VALIDATING"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("worker_id", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["script_package_id"], ["script_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["image_package_id"], ["image_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voice_package_id"], ["voice_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subtitle_package_id"], ["subtitle_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["music_package_id"], ["music_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thumbnail_package_id"], ["thumbnail_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quality_policy_id"], ["quality_policies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. quality_packages
    op.create_table(
        "quality_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voice_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtitle_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("music_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("thumbnail_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quality_policy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("publishing_lifecycle_state", sa.String(length=50), nullable=False, server_default="Draft"),
        sa.Column("production_readiness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_approved_for_publishing", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("critical_issue_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("major_issue_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("minor_issue_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dimension_scores", sa.JSON(), nullable=True),
        sa.Column("aggregated_telemetry", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["job_id"], ["quality_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_package_id"], ["script_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["image_package_id"], ["image_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voice_package_id"], ["voice_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subtitle_package_id"], ["subtitle_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["music_package_id"], ["music_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thumbnail_package_id"], ["thumbnail_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quality_policy_id"], ["quality_policies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. quality_checks
    op.create_table(
        "quality_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("package_type", sa.String(length=100), nullable=False),
        sa.Column("dimension", sa.String(length=50), nullable=False, server_default="Technical"),
        sa.Column("check_name", sa.String(length=150), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PASSED"),
        sa.Column("evaluated_value", sa.String(length=255), nullable=False),
        sa.Column("target_threshold", sa.String(length=255), nullable=False),
        sa.Column("execution_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["quality_package_id"], ["quality_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 6. quality_issues
    op.create_table(
        "quality_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_check_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("issue_code", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="MAJOR"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("impacted_component", sa.String(length=100), nullable=False),
        sa.Column("remediation_suggestion", sa.Text(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["quality_package_id"], ["quality_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quality_check_id"], ["quality_checks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 7. quality_evidence
    op.create_table(
        "quality_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_issue_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_package", sa.String(length=100), nullable=False),
        sa.Column("artifact_path", sa.String(length=2048), nullable=True),
        sa.Column("timestamp_ms", sa.Integer(), nullable=True),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("observed_value", sa.String(length=255), nullable=False),
        sa.Column("expected_value", sa.String(length=255), nullable=False),
        sa.Column("snapshot_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["quality_issue_id"], ["quality_issues.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 8. quality_recommendations
    op.create_table(
        "quality_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_issue_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_type", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="HIGH"),
        sa.Column("target_agent", sa.String(length=100), nullable=False),
        sa.Column("auto_fix_available", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("estimated_impact", sa.String(length=255), nullable=True),
        sa.Column("action_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["quality_issue_id"], ["quality_issues.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 9. remediation_tasks
    op.create_table(
        "remediation_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_agent", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["quality_package_id"], ["quality_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 10. quality_versions
    op.create_table(
        "quality_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["quality_package_id"], ["quality_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("quality_versions")
    op.drop_table("remediation_tasks")
    op.drop_table("quality_recommendations")
    op.drop_table("quality_evidence")
    op.drop_table("quality_issues")
    op.drop_table("quality_checks")
    op.drop_table("quality_packages")
    op.drop_table("quality_jobs")
    op.drop_table("quality_rules")
    op.drop_table("quality_policies")
