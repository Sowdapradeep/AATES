"""Create image tables

Revision ID: d4d4d4d4d4d4
Revises: c3c3c3c3c3c3
Create Date: 2026-07-17 14:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4d4d4d4d4d4'
down_revision: Union[str, Sequence[str], None] = 'c3c3c3c3c3c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. image_jobs
    op.create_table(
        "image_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
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
        sa.PrimaryKeyConstraint("id")
    )

    # 2. image_packages
    op.create_table(
        "image_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("aspect_ratio", sa.String(length=50), nullable=False),
        sa.Column("resolution", sa.String(length=50), nullable=False),
        sa.Column("style_preset", sa.String(length=100), nullable=False),
        sa.Column("overall_theme", sa.Text(), nullable=True),
        sa.Column("image_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generation_settings", sa.JSON(), nullable=True),
        sa.Column("character_profile", sa.JSON(), nullable=True),
        sa.Column("character_reference_images", sa.JSON(), nullable=True),
        sa.Column("character_id", sa.String(length=100), nullable=True),
        # BasePackageMixin columns
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
        sa.ForeignKeyConstraint(["job_id"], ["image_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_package_id"], ["script_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. scene_assets
    op.create_table(
        "scene_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_number", sa.Integer(), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False, server_default="5.0"),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("negative_prompt", sa.Text(), nullable=True),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("prompt_version", sa.String(length=50), nullable=True),
        sa.Column("aspect_ratio", sa.String(length=50), nullable=False),
        sa.Column("resolution", sa.String(length=50), nullable=False),
        sa.Column("style", sa.String(length=100), nullable=True),
        sa.Column("camera_angle", sa.String(length=100), nullable=True),
        sa.Column("character_reference", sa.Text(), nullable=True),
        sa.Column("background", sa.String(length=255), nullable=True),
        sa.Column("emotion", sa.String(length=100), nullable=True),
        sa.Column("lighting", sa.String(length=100), nullable=True),
        sa.Column("color_palette", sa.JSON(), nullable=True),
        sa.Column("local_path", sa.String(length=2048), nullable=False),
        sa.Column("storage_key", sa.String(length=2048), nullable=False),
        sa.Column("public_url", sa.String(length=2048), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("preview_url", sa.String(length=2048), nullable=True),
        sa.Column("previous_scene_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("next_scene_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transition_suggestion", sa.String(length=255), nullable=True),
        sa.Column("generation_duration_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["image_package_id"], ["image_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. image_versions
    op.create_table(
        "image_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("scene_number", sa.Integer(), nullable=True),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["image_package_id"], ["image_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("image_versions")
    op.drop_table("scene_assets")
    op.drop_table("image_packages")
    op.drop_table("image_jobs")
