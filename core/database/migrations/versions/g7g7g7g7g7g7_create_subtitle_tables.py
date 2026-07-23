"""Create subtitle tables

Revision ID: g7g7g7g7g7g7
Revises: f6f6f6f6f6f6
Create Date: 2026-07-20 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g7g7g7g7g7g7'
down_revision: Union[str, Sequence[str], None] = 'f6f6f6f6f6f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. caption_style_profiles
    op.create_table(
        "caption_style_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("font_family", sa.String(length=100), nullable=False, server_default="Inter"),
        sa.Column("font_size", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("font_weight", sa.String(length=50), nullable=False, server_default="Bold"),
        sa.Column("text_color", sa.String(length=50), nullable=False, server_default="#FFFFFF"),
        sa.Column("outline_color", sa.String(length=50), nullable=False, server_default="#000000"),
        sa.Column("outline_width", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("shadow", sa.String(length=100), nullable=True),
        sa.Column("background_box", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("background_color", sa.String(length=50), nullable=True),
        sa.Column("alignment", sa.String(length=50), nullable=False, server_default="center"),
        sa.Column("vertical_position", sa.String(length=50), nullable=False, server_default="bottom"),
        sa.Column("margins", sa.JSON(), nullable=True),
        sa.Column("animation", sa.String(length=100), nullable=True),
        sa.Column("safe_region", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. subtitle_jobs
    op.create_table(
        "subtitle_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("voice_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="en"),
        sa.Column("provider", sa.String(length=100), nullable=False, server_default="alignment"),
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
        sa.ForeignKeyConstraint(["voice_package_id"], ["voice_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. subtitle_packages
    op.create_table(
        "subtitle_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voice_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="en"),
        sa.Column("caption_style", sa.String(length=100), nullable=False, server_default="YouTube"),
        sa.Column("subtitle_formats", sa.JSON(), nullable=False),
        sa.Column("scene_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_captions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_words", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_artifacts", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["job_id"], ["subtitle_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voice_package_id"], ["voice_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. scene_subtitles
    op.create_table(
        "scene_subtitles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtitle_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_number", sa.Integer(), nullable=False),
        sa.Column("caption_text", sa.Text(), nullable=False),
        sa.Column("word_timings", sa.JSON(), nullable=False),
        sa.Column("sentence_timings", sa.JSON(), nullable=False),
        sa.Column("caption_position", sa.String(length=100), nullable=False, server_default="bottom"),
        sa.Column("safe_region", sa.String(length=100), nullable=True),
        sa.Column("reading_speed_wpm", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reading_speed_cps", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reading_speed_cpl", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="en"),
        sa.Column("key_phrases", sa.JSON(), nullable=True),
        sa.Column("importance_score", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["subtitle_package_id"], ["subtitle_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. caption_segments
    op.create_table(
        "caption_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_subtitle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("segment_number", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("words", sa.JSON(), nullable=False),
        sa.Column("reading_speed_wpm", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reading_speed_cps", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reading_speed_cpl", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.ForeignKeyConstraint(["scene_subtitle_id"], ["scene_subtitles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 6. subtitle_tracks
    op.create_table(
        "subtitle_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtitle_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("style_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("track_name", sa.String(length=100), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="en"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_original", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_translated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_auto_generated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_human_edited", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("srt_path", sa.String(length=2048), nullable=False),
        sa.Column("webvtt_path", sa.String(length=2048), nullable=False),
        sa.Column("ass_path", sa.String(length=2048), nullable=False),
        sa.Column("json_timeline_path", sa.String(length=2048), nullable=False),
        sa.Column("burned_caption_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["subtitle_package_id"], ["subtitle_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["style_profile_id"], ["caption_style_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 7. subtitle_versions
    op.create_table(
        "subtitle_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtitle_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["subtitle_package_id"], ["subtitle_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("subtitle_versions")
    op.drop_table("subtitle_tracks")
    op.drop_table("caption_segments")
    op.drop_table("scene_subtitles")
    op.drop_table("subtitle_packages")
    op.drop_table("subtitle_jobs")
    op.drop_table("caption_style_profiles")
