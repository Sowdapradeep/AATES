"""Create instagram publishing tables

Revision ID: k2k2k2k2k2k2
Revises: j1j1j1j1j1j1
Create Date: 2026-07-20 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'k2k2k2k2k2k2'
down_revision: Union[str, Sequence[str], None] = 'j1j1j1j1j1j1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. instagram_publish_jobs
    op.create_table(
        "instagram_publish_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("quality_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_media_type", sa.String(length=50), nullable=False, server_default="Reels"),
        sa.Column("provider", sa.String(length=100), nullable=False, server_default="instagram_provider"),
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
        sa.ForeignKeyConstraint(["quality_package_id"], ["quality_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. publication_packages
    op.create_table(
        "publication_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quality_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publishing_lifecycle_state", sa.String(length=50), nullable=False, server_default="Draft"),
        sa.Column("platform_name", sa.String(length=50), nullable=False, server_default="instagram"),
        sa.Column("platform_profile_id", sa.String(length=100), nullable=False, server_default="instagram_reels"),
        sa.Column("publication_result", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["job_id"], ["instagram_publish_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quality_package_id"], ["quality_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. instagram_publications
    op.create_table(
        "instagram_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instagram_media_id", sa.String(length=255), nullable=False),
        sa.Column("container_id", sa.String(length=255), nullable=True),
        sa.Column("permalink", sa.String(length=2048), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("hashtags", sa.JSON(), nullable=True),
        sa.Column("alt_text", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("visibility", sa.String(length=50), nullable=False, server_default="PUBLIC"),
        sa.Column("publishing_result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["publication_package_id"], ["publication_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. instagram_media_assets
    op.create_table(
        "instagram_media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_asset_key", sa.String(length=2048), nullable=False),
        sa.Column("cover_image_key", sa.String(length=2048), nullable=True),
        sa.Column("aspect_ratio", sa.String(length=20), nullable=False, server_default="9:16"),
        sa.Column("resolution", sa.String(length=50), nullable=False, server_default="1080x1920"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("codec", sa.String(length=50), nullable=False, server_default="h264"),
        sa.Column("bitrate", sa.Integer(), nullable=False, server_default="5000000"),
        sa.Column("thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["publication_id"], ["instagram_publications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. publishing_attempts
    op.create_table(
        "publishing_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("api_endpoint", sa.String(length=255), nullable=False),
        sa.Column("http_status_code", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("api_response", sa.JSON(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["instagram_publish_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 6. instagram_insight_snapshots
    op.create_table(
        "instagram_insight_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reach", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shares", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("profile_visits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("follows_attributed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("watch_time_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engagement_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["publication_id"], ["instagram_publications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 7. instagram_versions
    op.create_table(
        "instagram_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["publication_package_id"], ["publication_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("instagram_versions")
    op.drop_table("instagram_insight_snapshots")
    op.drop_table("publishing_attempts")
    op.drop_table("instagram_media_assets")
    op.drop_table("instagram_publications")
    op.drop_table("publication_packages")
    op.drop_table("instagram_publish_jobs")
