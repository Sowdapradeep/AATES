"""Create video tables

Revision ID: f6f6f6f6f6f6
Revises: e5e5e5e5e5e5
Create Date: 2026-07-17 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6f6f6f6f6f6'
down_revision: Union[str, Sequence[str], None] = 'e5e5e5e5e5e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. render_profiles
    op.create_table(
        "render_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("resolution", sa.String(length=50), nullable=False),
        sa.Column("aspect_ratio", sa.String(length=50), nullable=False),
        sa.Column("fps", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("codec", sa.String(length=50), nullable=False, server_default="h264"),
        sa.Column("bitrate", sa.Integer(), nullable=False, server_default="5000000"),
        sa.Column("container", sa.String(length=50), nullable=False, server_default="mp4"),
        sa.Column("audio_codec", sa.String(length=50), nullable=False, server_default="aac"),
        sa.Column("audio_sample_rate", sa.Integer(), nullable=False, server_default="44100"),
        sa.Column("audio_bitrate", sa.Integer(), nullable=False, server_default="192000"),
        sa.Column("color_space", sa.String(length=50), nullable=True, server_default="srgb"),
        sa.Column("hardware_acceleration", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("preset", sa.String(length=50), nullable=True, server_default="medium"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. video_jobs
    op.create_table(
        "video_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voice_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("render_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("renderer", sa.String(length=100), nullable=False),
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
        sa.ForeignKeyConstraint(["render_profile_id"], ["render_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. video_packages
    op.create_table(
        "video_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voice_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("resolution", sa.String(length=50), nullable=False),
        sa.Column("aspect_ratio", sa.String(length=50), nullable=False),
        sa.Column("fps", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("codec", sa.String(length=50), nullable=False, server_default="h264"),
        sa.Column("bitrate", sa.Integer(), nullable=False, server_default="5000000"),
        sa.Column("container", sa.String(length=50), nullable=False, server_default="mp4"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_key", sa.String(length=2048), nullable=False),
        sa.Column("preview_video", sa.String(length=2048), nullable=True),
        sa.Column("thumbnail_frame", sa.String(length=2048), nullable=True),
        sa.Column("scene_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("timeline_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_artifacts", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["job_id"], ["video_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_package_id"], ["script_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["image_package_id"], ["image_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voice_package_id"], ["voice_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. scene_videos
    op.create_table(
        "scene_videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_number", sa.Integer(), nullable=False),
        sa.Column("timeline_start_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("timeline_end_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("voice_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("motion_preset", sa.String(length=100), nullable=True, server_default="None"),
        sa.Column("transition_preset", sa.String(length=100), nullable=True, server_default="Cut"),
        sa.Column("rendered_clip", sa.String(length=2048), nullable=True),
        sa.Column("storage_key", sa.String(length=2048), nullable=False),
        sa.Column("preview_url", sa.String(length=2048), nullable=True),
        sa.Column("render_metadata", sa.JSON(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["image_asset_id"], ["scene_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["voice_asset_id"], ["scene_voices.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. timeline_events
    op.create_table(
        "timeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_number", sa.Integer(), nullable=False),
        sa.Column("start_time_ms", sa.Integer(), nullable=False),
        sa.Column("end_time_ms", sa.Integer(), nullable=False),
        sa.Column("voice_offset_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("transition_start_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("transition_end_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("motion_start_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("motion_end_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("caption_region", sa.String(length=100), nullable=True, server_default="bottom"),
        sa.Column("audio_fade_in_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("audio_fade_out_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("video_fade_in_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("video_fade_out_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 6. video_versions
    op.create_table(
        "video_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("video_versions")
    op.drop_table("timeline_events")
    op.drop_table("scene_videos")
    op.drop_table("video_packages")
    op.drop_table("video_jobs")
    op.drop_table("render_profiles")
