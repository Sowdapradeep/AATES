"""Create Narrative Core v1 Tables

Revision ID: o6o6o6o6o6o6
Revises: n5n5n5n5n5n5
Create Date: 2026-07-22 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'o6o6o6o6o6o6'
down_revision = 'n5n5n5n5n5n5'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Universes
    op.create_table(
        'narrative_universes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('genre', sa.String(length=100), nullable=False, server_default='Drama'),
        sa.Column('core_themes', sa.JSON(), nullable=True),
        sa.Column('world_rules', sa.JSON(), nullable=True),
        sa.Column('long_term_direction', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 2. Worlds
    op.create_table(
        'narrative_worlds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('universe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_universes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('geography_type', sa.String(length=100), nullable=True),
        sa.Column('climate', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('world_rules', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 3. Characters
    op.create_table(
        'narrative_characters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('universe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_universes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False, index=True),
        sa.Column('role', sa.String(length=100), nullable=False, server_default='protagonist'),
        sa.Column('archetype', sa.String(length=100), nullable=True),
        sa.Column('personality_traits', sa.JSON(), nullable=True),
        sa.Column('background_lore', sa.Text(), nullable=True),
        sa.Column('motivation', sa.Text(), nullable=True),
        sa.Column('slang_preference', sa.String(length=100), nullable=True),
        sa.Column('attire_note', sa.Text(), nullable=True),
        sa.Column('antagonistic_goal', sa.Text(), nullable=True),
        sa.Column('methods', sa.JSON(), nullable=True),
        sa.Column('redeeming_qualities', sa.JSON(), nullable=True),
        sa.Column('underlying_weakness', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 4. Relationships
    op.create_table(
        'narrative_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('character_a_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_characters.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('character_b_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_characters.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('relationship_type', sa.String(length=100), nullable=False, server_default='rivalry'),
        sa.Column('tension_level', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('history_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 5. Locations
    op.create_table(
        'narrative_locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('universe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_universes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('key_features', sa.JSON(), nullable=True),
        sa.Column('mood', sa.String(length=100), nullable=True),
        sa.Column('cultural_context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 6. Organizations
    op.create_table(
        'narrative_organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('universe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_universes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False, index=True),
        sa.Column('faction_type', sa.String(length=100), nullable=True),
        sa.Column('objectives', sa.JSON(), nullable=True),
        sa.Column('influence_level', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('allies', sa.JSON(), nullable=True),
        sa.Column('enemies', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 7. StoryArcs
    op.create_table(
        'narrative_story_arcs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('universe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_universes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('major_theme', sa.String(length=255), nullable=True),
        sa.Column('climax_prediction', sa.Text(), nullable=True),
        sa.Column('resolution_path', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 8. Seasons
    op.create_table(
        'narrative_seasons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('universe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_universes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('season_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('total_episodes', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('season_arc', sa.String(length=500), nullable=True),
        sa.Column('major_conflicts', sa.JSON(), nullable=True),
        sa.Column('character_development_milestones', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 9. Episodes
    op.create_table(
        'narrative_episodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('season_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_seasons.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('episode_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('episode_objectives', sa.Text(), nullable=True),
        sa.Column('story_beats', sa.JSON(), nullable=True),
        sa.Column('scene_objectives', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 10. Scenes
    op.create_table(
        'narrative_scenes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_episodes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('scene_number', sa.Integer(), nullable=False),
        sa.Column('location_name', sa.String(length=255), nullable=True),
        sa.Column('time_of_day', sa.String(length=50), nullable=True, server_default='DAY'),
        sa.Column('weather', sa.String(length=50), nullable=True, server_default='SUNNY'),
        sa.Column('lighting_mood', sa.String(length=100), nullable=True),
        sa.Column('characters_present', sa.JSON(), nullable=True),
        sa.Column('emotions', sa.JSON(), nullable=True),
        sa.Column('props', sa.JSON(), nullable=True),
        sa.Column('costumes', sa.JSON(), nullable=True),
        sa.Column('camera_intent', sa.Text(), nullable=True),
        sa.Column('visual_style', sa.String(length=100), nullable=True),
        sa.Column('dialogues', sa.JSON(), nullable=True),
        sa.Column('music_mood', sa.String(length=100), nullable=True),
        sa.Column('sound_effects', sa.JSON(), nullable=True),
        sa.Column('continuity_notes', sa.Text(), nullable=True),
        sa.Column('rendering_hints', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 11. TimelineEvents
    op.create_table(
        'narrative_timeline_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('universe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_universes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('beat_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False, server_default='beat'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('emotional_charge', sa.String(length=100), nullable=True, server_default='tense'),
        sa.Column('twist_introduced', sa.Text(), nullable=True),
        sa.Column('foreshadowing_clues', sa.JSON(), nullable=True),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_characters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_locations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('narrative_episodes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('narrative_timeline_events')
    op.drop_table('narrative_scenes')
    op.drop_table('narrative_episodes')
    op.drop_table('narrative_seasons')
    op.drop_table('narrative_story_arcs')
    op.drop_table('narrative_organizations')
    op.drop_table('narrative_locations')
    op.drop_table('narrative_relationships')
    op.drop_table('narrative_characters')
    op.drop_table('narrative_worlds')
    op.drop_table('narrative_universes')
