"""Create orchestration engine tables

Revision ID: n5n5n5n5n5n5
Revises: m4m4m4m4m4m4
Create Date: 2026-07-20 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'n5n5n5n5n5n5'
down_revision: Union[str, Sequence[str], None] = 'm4m4m4m4m4m4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. orchestration_jobs
    op.create_table(
        "orchestration_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="QUEUED"),
        sa.Column("stage", sa.String(length=50), nullable=False, server_default="OBJECTIVE_ANALYSIS"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("worker_id", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("objective_type", sa.String(length=100), nullable=False, server_default="GENERATE_LONGFORM_VIDEO"),
        sa.Column("target_platform", sa.String(length=50), nullable=False, server_default="all"),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. orchestrator_objectives
    op.create_table(
        "orchestrator_objectives",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("objective_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("objective_type", sa.String(length=100), nullable=False),
        sa.Column("target_platform", sa.String(length=50), nullable=False, server_default="all"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("target_kpi", sa.JSON(), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. execution_plans
    op.create_table(
        "execution_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("objective_id", sa.String(length=100), nullable=False),
        sa.Column("objective_type", sa.String(length=100), nullable=False),
        sa.Column("required_agents", sa.JSON(), nullable=False),
        sa.Column("estimated_duration_sec", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("parallelism_factor", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.15"),
        sa.Column("expected_resources", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. execution_graphs
    op.create_table(
        "execution_graphs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("graph_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("plan_id", sa.String(length=100), nullable=False),
        sa.Column("critical_path", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. task_nodes
    op.create_table(
        "task_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("graph_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", sa.String(length=100), nullable=False),
        sa.Column("target_agent", sa.String(length=100), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("depends_on", sa.JSON(), nullable=False),
        sa.Column("estimated_duration_sec", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("retry_policy", sa.JSON(), nullable=False),
        sa.Column("resource_requirements", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("result_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["graph_id"], ["execution_graphs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 6. task_dependencies
    op.create_table(
        "task_dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_node_id", sa.String(length=100), nullable=False),
        sa.Column("child_node_id", sa.String(length=100), nullable=False),
        sa.Column("dependency_type", sa.String(length=50), nullable=False, server_default="STRONG"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 7. agent_assignments
    op.create_table(
        "agent_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", sa.String(length=100), nullable=False),
        sa.Column("target_agent", sa.String(length=100), nullable=False),
        sa.Column("assigned_worker_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ASSIGNED"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 8. resource_reservations
    op.create_table(
        "resource_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reservation_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("allocated_to_node", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("granted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 9. execution_checkpoints
    op.create_table(
        "execution_checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checkpoint_name", sa.String(length=100), nullable=False),
        sa.Column("completed_nodes", sa.JSON(), nullable=False),
        sa.Column("state_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["orchestration_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 10. orchestration_decisions
    op.create_table(
        "orchestration_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("objective_id", sa.String(length=100), nullable=False),
        sa.Column("decision_type", sa.String(length=100), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.96"),
        sa.Column("action_taken", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 11. orchestration_packages
    op.create_table(
        "orchestration_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("objective_type", sa.String(length=100), nullable=False),
        sa.Column("target_platform", sa.String(length=50), nullable=False, server_default="all"),
        sa.Column("orchestration_confidence", sa.Float(), nullable=False, server_default="0.96"),
        sa.Column("executed_nodes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_nodes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("plan_snapshot", sa.JSON(), nullable=True),
        sa.Column("dag_snapshot", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["job_id"], ["orchestration_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 12. orchestration_versions
    op.create_table(
        "orchestration_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("orchestration_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["orchestration_package_id"], ["orchestration_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("orchestration_versions")
    op.drop_table("orchestration_packages")
    op.drop_table("orchestration_decisions")
    op.drop_table("execution_checkpoints")
    op.drop_table("resource_reservations")
    op.drop_table("agent_assignments")
    op.drop_table("task_dependencies")
    op.drop_table("task_nodes")
    op.drop_table("execution_graphs")
    op.drop_table("execution_plans")
    op.drop_table("orchestrator_objectives")
    op.drop_table("orchestration_jobs")
