"""Create music tables

Revision ID: h8h8h8h8h8h8
Revises: g7g7g7g7g7g7
Create Date: 2026-07-20 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'h8h8h8h8h8h8'
down_revision: Union[str, Sequence[str], None] = 'g7g7g7g7g7g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. audio_mix_profiles
    op.create_table(
        "audio_mix_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("target_platform", sa.String(length=100), nullable=False),
        sa.Column("music_volume_db", sa.Float(), nullable=False, server_default="-14.0"),
        sa.Column("narration_volume_db", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("ducking_level_db", sa.Float(), nullable=False, server_default="-12.0"),
        sa.Column("fade_duration_ms", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("crossfade_duration_ms", sa.Integer(), nullable=False, server_default="800"),
        sa.Column("target_lufs", sa.Float(), nullable=False, server_default="-14.0"),
        sa.Column("true_peak_db", sa.Float(), nullable=False, server_default="-1.0"),
        sa.Column("sample_rate", sa.Integer(), nullable=False, server_default="44100"),
        sa.Column("channels", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("normalization_mode", sa.String(length=50), nullable=False, server_default="peak_and_lufs"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. music_jobs
    op.create_table(
        "music_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voice_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtitle_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("audio_mix_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=False, server_default="library"),
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
        sa.ForeignKeyConstraint(["voice_package_id"], ["voice_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subtitle_package_id"], ["subtitle_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["audio_mix_profile_id"], ["audio_mix_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. music_packages
    op.create_table(
        "music_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("script_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voice_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtitle_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("audio_mix_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("storage_key", sa.String(length=2048), nullable=False),
        sa.Column("separated_music_track", sa.String(length=2048), nullable=True),
        sa.Column("narration_track", sa.String(length=2048), nullable=True),
        sa.Column("ambient_stem_track", sa.String(length=2048), nullable=True),
        sa.Column("sfx_stem_track", sa.String(length=2048), nullable=True),
        sa.Column("scene_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("waveform_metadata", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["job_id"], ["music_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_package_id"], ["script_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voice_package_id"], ["voice_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_package_id"], ["video_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subtitle_package_id"], ["subtitle_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["audio_mix_profile_id"], ["audio_mix_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. music_assets
    op.create_table(
        "music_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("license_type", sa.String(length=100), nullable=False, server_default="Creative Commons"),
        sa.Column("copyright_info", sa.String(length=255), nullable=True),
        sa.Column("storage_key", sa.String(length=2048), nullable=False),
        sa.Column("fingerprint", sa.String(length=255), nullable=True),
        sa.Column("isrc", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. music_tracks
    op.create_table(
        "music_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("track_title", sa.String(length=150), nullable=False),
        sa.Column("artist", sa.String(length=150), nullable=True, server_default="AATES AI Audio"),
        sa.Column("genre", sa.String(length=100), nullable=False, server_default="Cinematic"),
        sa.Column("mood", sa.String(length=100), nullable=False, server_default="Inspiring"),
        sa.Column("energy_level", sa.String(length=50), nullable=False, server_default="Medium"),
        sa.Column("tempo_bpm", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("musical_key", sa.String(length=20), nullable=False, server_default="C Major"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sample_rate", sa.Integer(), nullable=False, server_default="44100"),
        sa.Column("channels", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("is_loopable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_generated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_licensed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["asset_id"], ["music_assets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 6. scene_musics
    op.create_table(
        "scene_musics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("music_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scene_number", sa.Integer(), nullable=False),
        sa.Column("track_name", sa.String(length=150), nullable=False),
        sa.Column("genre", sa.String(length=100), nullable=False, server_default="Cinematic"),
        sa.Column("mood", sa.String(length=100), nullable=False, server_default="Inspiring"),
        sa.Column("energy", sa.String(length=50), nullable=False, server_default="Medium"),
        sa.Column("tempo_bpm", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("musical_key", sa.String(length=20), nullable=False, server_default="C Major"),
        sa.Column("start_time_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("end_time_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fade_in_ms", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("fade_out_ms", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("loop_points", sa.JSON(), nullable=True),
        sa.Column("music_volume_db", sa.Float(), nullable=False, server_default="-14.0"),
        sa.Column("narration_ducking_db", sa.Float(), nullable=False, server_default="-12.0"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["music_package_id"], ["music_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 7. music_cues
    op.create_table(
        "music_cues",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("music_track_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scene_music_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cue_name", sa.String(length=100), nullable=False),
        sa.Column("cue_purpose", sa.String(length=50), nullable=False, server_default="background"),
        sa.Column("source_start_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_end_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trim_start_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trim_end_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("loop_start_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("loop_end_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fade_in_ms", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("fade_out_ms", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("gain_db", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("emotion_score", sa.Float(), nullable=False, server_default="0.88"),
        sa.Column("transition_compatibility", sa.Float(), nullable=False, server_default="0.92"),
        sa.Column("loop_confidence", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("crossfade_recommendation", sa.Integer(), nullable=False, server_default="800"),
        sa.Column("beat_alignment_offset_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["music_track_id"], ["music_tracks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["scene_music_id"], ["scene_musics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 8. audio_timeline_events
    op.create_table(
        "audio_timeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("music_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cue_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scene_number", sa.Integer(), nullable=False),
        sa.Column("start_time_ms", sa.Integer(), nullable=False),
        sa.Column("end_time_ms", sa.Integer(), nullable=False),
        sa.Column("gain_db", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("pan", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("fade_in_ms", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("fade_out_ms", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("ducking_state", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("automation_points", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["music_package_id"], ["music_packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cue_id"], ["music_cues.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 9. audio_analyses
    op.create_table(
        "audio_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("music_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("peak_db", sa.Float(), nullable=False, server_default="-1.0"),
        sa.Column("lufs", sa.Float(), nullable=False, server_default="-14.0"),
        sa.Column("dynamic_range_db", sa.Float(), nullable=False, server_default="8.5"),
        sa.Column("rms_db", sa.Float(), nullable=False, server_default="-16.0"),
        sa.Column("tempo_bpm", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("musical_key", sa.String(length=20), nullable=False, server_default="C Major"),
        sa.Column("silence_regions", sa.JSON(), nullable=True),
        sa.Column("speech_regions", sa.JSON(), nullable=True),
        sa.Column("waveform_data", sa.JSON(), nullable=True),
        sa.Column("spectrum_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["music_package_id"], ["music_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 10. music_versions
    op.create_table(
        "music_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("music_package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_version", sa.Integer(), nullable=True),
        sa.Column("lineage_action", sa.String(length=50), nullable=False, server_default="INITIAL"),
        sa.Column("assets_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["music_package_id"], ["music_packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("music_versions")
    op.drop_table("audio_analyses")
    op.drop_table("audio_timeline_events")
    op.drop_table("music_cues")
    op.drop_table("scene_musics")
    op.drop_table("music_tracks")
    op.drop_table("music_assets")
    op.drop_table("music_packages")
    op.drop_table("music_jobs")
    op.drop_table("audio_mix_profiles")
