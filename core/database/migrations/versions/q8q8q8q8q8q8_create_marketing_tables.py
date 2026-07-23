"""Create Marketing & Audience Tables

Revision ID: q8q8q8q8q8q8
Revises: p7p7p7p7p7p7
Create Date: 2026-07-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'q8q8q8q8q8q8'
down_revision = 'p7p7p7p7p7p7'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. AudienceSegment
    op.create_table(
        'marketing_audience_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False, index=True),
        sa.Column('region', sa.String(length=100), nullable=False, server_default='Tamil Nadu'),
        sa.Column('demographics', sa.String(length=100), nullable=False, server_default='18-35 Youth'),
        sa.Column('preferred_genre', sa.String(length=100), nullable=False, server_default='Drama'),
        sa.Column('engagement_rate', sa.Float(), nullable=False, server_default='0.05'),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 2. MarketingCampaign
    op.create_table(
        'marketing_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('segment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('marketing_audience_segments.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('target_platform', sa.String(length=100), nullable=False, server_default='youtube_reels'),
        sa.Column('viral_hook', sa.Text(), nullable=True),
        sa.Column('hashtags', sa.JSON(), nullable=True),
        sa.Column('budget_allocation_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('performance_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('marketing_campaigns')
    op.drop_table('marketing_audience_segments')
