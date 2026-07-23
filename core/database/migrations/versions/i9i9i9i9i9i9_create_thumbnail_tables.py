"""Create thumbnail tables

Revision ID: i9i9i9i9i9i9
Revises: h8h8h8h8h8h8
Create Date: 2026-07-20 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'i9i9i9i9i9i9'
down_revision: Union[str, Sequence[str], None] = 'h8h8h8h8h8h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. thumbnail_style_profiles
    op.create_table(
        "thumbnail_style_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("font_family", sa.String(length=100), nullable=False, server_default="Inter Black"),
        sa.Column("font_size_pt", sa.Integer(), nullable=False, server_default="72"),
        sa.Column("font_weight", sa.String(length=50), nullable=False, server_default="Bold"),
        sa.Column("primary_color", sa.String(length=50), nullable=False, server_default="#FFFFFF"),
        sa.Column("accent_color", sa.String(length=50), nullable=False, server_default="#FFD700"),
        sa.Column("outline_color", sa.String(length=50), nullable=False, server_default="#000000"),
        sa.Column("shadow_style", sa.String(length=100), nullable=False, server_default="Heavy Drop Shadow"),
        sa.Column("background_style", sa.String(length=100), nullable=False, server_default="High Contrast Gradient"),
        sa.Column("logo_placement", sa.String(length=50), nullable=False, server_default="top_right"),
        sa.Column("safe_margins", sa.JSON(), nullable=True),
        sa.Column("emoji_policy", sa.String(length=50), nullable=False, server_default="allowed"),
        sa.Column("aspect_ratio", sa.String(length=20), nullable=False, server_default="16:9"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. composition_templates
    op.create_table(
        "composition_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("layout_type", sa.String(length=50), nullable=False, server_default="left_focus"),
        sa.Column("subject_region", sa.JSON(), nullable=True),
        sa.Column("headline_region", sa.JSON(), nullable=True),
        sa.Column("secondary_text_region", sa.JSON(), nullable=True),
        sa.Column("logo_region", sa.JSON(), nullable=True),
        sa.Column("safe_margins", sa.JSON(), nullable=True),
        sa.Column("grid_definition", sa.JSON(), nullable=True),
        sa.Column("aspect_ratio", sa.String(length=20), nullable=False, server_default="16:9"),
        sa.Column("priority_rules", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. thumbnail_jobs
    op.create_table(
        "thumbnail_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtitle_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("music_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("thumbnail_style_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=False, server_default="template"),
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
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subtitle_package_id"], ["subtitle_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["music_package_id"], ["music_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thumbnail_style_profile_id"], ["thumbnail_style_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. thumbnail_packages
    op.create_table(
        "thumbnail_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtitle_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("music_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("thumbnail_style_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("primary_thumbnail_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("selected_variant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("variant_count", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(["job_id"], ["thumbnail_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_package_id"], ["script_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["image_package_id"], ["image_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subtitle_package_id"], ["subtitle_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["music_package_id"], ["music_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thumbnail_style_profile_id"], ["thumbnail_style_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. thumbnail_assets
    op.create_table(
        "thumbnail_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(length=2048), nullable=False),
        sa.Column("public_url", sa.String(length=2048), nullable=True),
        sa.Column("preview_url", sa.String(length=2048), nullable=True),
        sa.Column("width", sa.Integer(), nullable=False, server_default="1280"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="720"),
        sa.Column("format", sa.String(length=20), nullable=False, server_default="png"),
        sa.Column("compression", sa.String(length=50), nullable=False, server_default="high_quality"),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 6. thumbnail_variants
    op.create_table(
        "thumbnail_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thumbnail_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thumbnail_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("composition_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("variant_name", sa.String(length=100), nullable=False),
        sa.Column("scene_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_frame_key", sa.String(length=2048), nullable=True),
        sa.Column("primary_hook", sa.String(length=100), nullable=False),
        sa.Column("secondary_hook", sa.String(length=150), nullable=True),
        sa.Column("badge_text", sa.String(length=50), nullable=True),
        sa.Column("brand_label", sa.String(length=50), nullable=True),
        sa.Column("layout_type", sa.String(length=50), nullable=False, server_default="left_focus"),
        sa.Column("face_region", sa.JSON(), nullable=True),
        sa.Column("subject_region", sa.JSON(), nullable=True),
        sa.Column("background_region", sa.JSON(), nullable=True),
        sa.Column("contrast_score", sa.Float(), nullable=False, server_default="0.9"),
        sa.Column("readability_score", sa.Float(), nullable=False, server_default="0.92"),
        sa.Column("composition_score", sa.Float(), nullable=False, server_default="0.88"),
        sa.Column("brand_score", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("ctr_prediction_score", sa.Float(), nullable=False, server_default="0.94"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.94"),
        sa.Column("is_selected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["thumbnail_package_id"], ["thumbnail_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thumbnail_asset_id"], ["thumbnail_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["composition_template_id"], ["composition_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 7. thumbnail_analyses
    op.create_table(
        "thumbnail_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thumbnail_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("blur_score", sa.Float(), nullable=False, server_default="0.05"),
        sa.Column("brightness", sa.Float(), nullable=False, server_default="0.65"),
        sa.Column("contrast_ratio", sa.Float(), nullable=False, server_default="6.2"),
        sa.Column("entropy", sa.Float(), nullable=False, server_default="7.4"),
        sa.Column("dominant_colors", sa.JSON(), nullable=True),
        sa.Column("face_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("face_confidence", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("object_regions", sa.JSON(), nullable=True),
        sa.Column("saliency_map", sa.JSON(), nullable=True),
        sa.Column("ocr_result", sa.JSON(), nullable=True),
        sa.Column("edge_density", sa.Float(), nullable=False, server_default="0.45"),
        sa.Column("color_histogram", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["thumbnail_package_id"], ["thumbnail_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 8. thumbnail_scores
    op.create_table(
        "thumbnail_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thumbnail_variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contrast_score", sa.Float(), nullable=False, server_default="0.92"),
        sa.Column("sharpness_score", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("face_visibility_score", sa.Float(), nullable=False, server_default="0.90"),
        sa.Column("subject_prominence_score", sa.Float(), nullable=False, server_default="0.88"),
        sa.Column("text_readability_score", sa.Float(), nullable=False, server_default="0.94"),
        sa.Column("color_harmony_score", sa.Float(), nullable=False, server_default="0.91"),
        sa.Column("rule_of_thirds_score", sa.Float(), nullable=False, server_default="0.89"),
        sa.Column("emotion_score", sa.Float(), nullable=False, server_default="0.87"),
        sa.Column("brand_consistency_score", sa.Float(), nullable=False, server_default="0.96"),
        sa.Column("heuristic_score", sa.Float(), nullable=False, server_default="0.92"),
        sa.Column("learned_score", sa.Float(), nullable=False, server_default="0.94"),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0.93"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["thumbnail_variant_id"], ["thumbnail_variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 9. thumbnail_versions
    op.create_table(
        "thumbnail_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thumbnail_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["thumbnail_package_id"], ["thumbnail_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 10. thumbnail_experiments
    op.create_table(
        "thumbnail_experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thumbnail_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_a_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_b_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False, server_default="youtube"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="SCHEDULED"),
        sa.Column("evaluation_window_hours", sa.Integer(), nullable=False, server_default="72"),
        sa.Column("statistical_significance", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("algorithm_version", sa.String(length=50), nullable=True, server_default="v1.0"),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ctr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("winner_variant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("winning_confidence", sa.Float(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["thumbnail_package_id"], ["thumbnail_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("thumbnail_experiments")
    op.drop_table("thumbnail_versions")
    op.drop_table("thumbnail_scores")
    op.drop_table("thumbnail_analyses")
    op.drop_table("thumbnail_variants")
    op.drop_table("thumbnail_assets")
    op.drop_table("thumbnail_packages")
    op.drop_table("thumbnail_jobs")
    op.drop_table("composition_templates")
    op.drop_table("thumbnail_style_profiles")
