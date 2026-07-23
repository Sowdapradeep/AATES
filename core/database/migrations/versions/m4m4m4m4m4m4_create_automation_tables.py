"""Create automation engine tables

Revision ID: m4m4m4m4m4m4
Revises: l3l3l3l3l3l3
Create Date: 2026-07-20 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'm4m4m4m4m4m4'
down_revision: Union[str, Sequence[str], None] = 'l3l3l3l3l3l3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. automation_jobs
    op.create_table(
        "automation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="QUEUED"),
        sa.Column("stage", sa.String(length=50), nullable=False, server_default="WAITING"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("worker_id", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trigger_type", sa.String(length=50), nullable=False, server_default="MANUAL_TRIGGER"),
        sa.Column("source_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_platform", sa.String(length=50), nullable=False, server_default="all"),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. automation_policies
    op.create_table(
        "automation_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trigger_types", sa.JSON(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("target_workflow_id", sa.String(length=100), nullable=False, server_default="AUTONOMOUS_PUBLISHING"),
        sa.Column("cooldown_sec", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("retry_rules", sa.JSON(), nullable=False),
        sa.Column("platforms", sa.JSON(), nullable=False),
        sa.Column("applicable_agents", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. automation_triggers
    op.create_table(
        "automation_triggers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trigger_id", sa.String(length=100), nullable=False),
        sa.Column("trigger_type", sa.String(length=100), nullable=False),
        sa.Column("source_component", sa.String(length=100), nullable=False),
        sa.Column("source_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_platform", sa.String(length=50), nullable=False, server_default="all"),
        sa.Column("event_data", sa.JSON(), nullable=False),
        sa.Column("triggered_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. automation_decisions
    op.create_table(
        "automation_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_id", sa.String(length=100), nullable=False),
        sa.Column("workflow_id", sa.String(length=100), nullable=False),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("decision_reason", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("condition_evaluations", sa.JSON(), nullable=False),
        sa.Column("resource_lock_acquired", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. automation_workflow_definitions
    op.create_table(
        "automation_workflow_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("steps_snapshot", sa.JSON(), nullable=False),
        sa.Column("timeout_sec", sa.Integer(), nullable=False, server_default="600"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 6. automation_workflow_instances
    op.create_table(
        "automation_workflow_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instance_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("workflow_id", sa.String(length=100), nullable=False),
        sa.Column("trigger_id", sa.String(length=100), nullable=False),
        sa.Column("policy_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("current_step", sa.String(length=100), nullable=False, server_default="START"),
        sa.Column("execution_owner", sa.String(length=100), nullable=False, server_default="automation-worker-0"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("context_snapshot", sa.JSON(), nullable=False),
        sa.Column("compensation_log", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 7. automation_workflow_step_executions
    op.create_table(
        "automation_workflow_step_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_id", sa.String(length=100), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("target_agent", sa.String(length=100), nullable=False),
        sa.Column("idempotency_key", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("execution_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_data", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("compensation_executed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["instance_id"], ["automation_workflow_instances.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 8. resource_locks
    op.create_table(
        "resource_locks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("owner_workflow_instance_id", sa.String(length=100), nullable=False),
        sa.Column("locked_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )

    # 9. automation_packages
    op.create_table(
        "automation_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", sa.String(length=100), nullable=False),
        sa.Column("policy_id", sa.String(length=100), nullable=False),
        sa.Column("target_platform", sa.String(length=50), nullable=False, server_default="all"),
        sa.Column("execution_confidence", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("executed_actions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("execution_context_snapshot", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["job_id"], ["automation_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 10. automation_versions
    op.create_table(
        "automation_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("automation_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["automation_package_id"], ["automation_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("automation_versions")
    op.drop_table("automation_packages")
    op.drop_table("resource_locks")
    op.drop_table("automation_workflow_step_executions")
    op.drop_table("automation_workflow_instances")
    op.drop_table("automation_workflow_definitions")
    op.drop_table("automation_decisions")
    op.drop_table("automation_triggers")
    op.drop_table("automation_policies")
    op.drop_table("automation_jobs")
