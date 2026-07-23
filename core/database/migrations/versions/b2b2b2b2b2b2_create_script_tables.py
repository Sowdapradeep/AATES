"""Create script tables

Revision ID: b2b2b2b2b2b2
Revises: a1a1a1a1a1a1
Create Date: 2026-07-17 13:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2b2b2b2b2b2'
down_revision: Union[str, Sequence[str], None] = 'a1a1a1a1a1a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. script_jobs
    op.create_table(
        "script_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("knowledge_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False, server_default="ta"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="QUEUED"),
        sa.Column("stage", sa.String(length=50), nullable=False, server_default="VALIDATING"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("worker_id", sa.String(length=100), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["knowledge_package_id"], ["knowledge_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. script_packages
    op.create_table(
        "script_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("knowledge_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False, server_default="ta"),
        sa.Column("target_audience", sa.JSON(), nullable=True),
        sa.Column("tone", sa.String(length=100), nullable=True),
        sa.Column("style", sa.String(length=100), nullable=True),
        sa.Column("estimated_duration_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reading_time_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("hook", sa.Text(), nullable=False),
        sa.Column("opening", sa.Text(), nullable=True),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("story", sa.Text(), nullable=False),
        sa.Column("solution", sa.Text(), nullable=False),
        sa.Column("cta", sa.Text(), nullable=False),
        sa.Column("narration", sa.Text(), nullable=False),
        sa.Column("scene_breakdown", sa.JSON(), nullable=False),
        sa.Column("on_screen_text", sa.JSON(), nullable=True),
        sa.Column("visual_prompts", sa.JSON(), nullable=True),
        sa.Column("thumbnail_prompt", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("hashtags", sa.JSON(), nullable=True),
        sa.Column("references", sa.JSON(), nullable=True),
        sa.Column("telemetry_metadata", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("review_report", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["script_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["knowledge_package_id"], ["knowledge_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. script_versions
    op.create_table(
        "script_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("hook", sa.Text(), nullable=False),
        sa.Column("opening", sa.Text(), nullable=True),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("story", sa.Text(), nullable=False),
        sa.Column("solution", sa.Text(), nullable=False),
        sa.Column("cta", sa.Text(), nullable=False),
        sa.Column("narration", sa.Text(), nullable=False),
        sa.Column("scene_breakdown", sa.JSON(), nullable=False),
        sa.Column("thumbnail_prompt", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("hashtags", sa.JSON(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("review_report", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["script_package_id"], ["script_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("script_versions")
    op.drop_table("script_packages")
    op.drop_table("script_jobs")
