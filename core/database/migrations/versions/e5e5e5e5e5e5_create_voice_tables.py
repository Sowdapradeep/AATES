"""Create voice tables

Revision ID: e5e5e5e5e5e5
Revises: d4d4d4d4d4d4
Create Date: 2026-07-17 15:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5e5e5e5e5e5'
down_revision: Union[str, Sequence[str], None] = 'd4d4d4d4d4d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. voice_jobs
    op.create_table(
        "voice_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("voice_model", sa.String(length=100), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
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

    # 2. voice_packages
    op.create_table(
        "voice_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("voice_profile", sa.JSON(), nullable=True),
        sa.Column("speaking_style", sa.String(length=100), nullable=True),
        sa.Column("overall_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_words", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_scenes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("audio_format", sa.String(length=50), nullable=False, server_default="mp3"),
        sa.Column("sample_rate", sa.Integer(), nullable=False, server_default="44100"),
        sa.Column("bitrate", sa.Integer(), nullable=False, server_default="192000"),
        sa.Column("pronunciation_dictionary", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["job_id"], ["voice_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_package_id"], ["script_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. scene_voices
    op.create_table(
        "scene_voices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voice_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_number", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("narration", sa.Text(), nullable=False),
        sa.Column("local_path", sa.String(length=2048), nullable=False),
        sa.Column("storage_key", sa.String(length=2048), nullable=False),
        sa.Column("public_url", sa.String(length=2048), nullable=True),
        sa.Column("preview_url", sa.String(length=2048), nullable=True),
        sa.Column("voice_id", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("emotion", sa.String(length=100), nullable=True),
        sa.Column("speaking_style", sa.String(length=100), nullable=True),
        sa.Column("pitch", sa.String(length=50), nullable=True),
        sa.Column("speed", sa.String(length=50), nullable=True),
        sa.Column("volume", sa.String(length=50), nullable=True),
        sa.Column("ssml", sa.Text(), nullable=True),
        sa.Column("pause_map", sa.JSON(), nullable=True),
        sa.Column("word_alignment", sa.JSON(), nullable=True),
        sa.Column("sentence_alignment", sa.JSON(), nullable=True),
        sa.Column("phoneme_alignment", sa.JSON(), nullable=True),
        sa.Column("generation_duration_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["voice_package_id"], ["voice_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. voice_versions
    op.create_table(
        "voice_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voice_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("scene_number", sa.Integer(), nullable=True),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["voice_package_id"], ["voice_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("voice_versions")
    op.drop_table("scene_voices")
    op.drop_table("voice_packages")
    op.drop_table("voice_jobs")
