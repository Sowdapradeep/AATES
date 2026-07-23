"""Create Finance & Governance Tables

Revision ID: p7p7p7p7p7p7
Revises: o6o6o6o6o6o6
Create Date: 2026-07-22 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'p7p7p7p7p7p7'
down_revision = 'o6o6o6o6o6o6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. BudgetLedger
    op.create_table(
        'finance_budget_ledgers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False, server_default='Master Studio Ledger'),
        sa.Column('allocated_budget_usd', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('current_spent_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('max_daily_limit_usd', sa.Float(), nullable=False, server_default='10.0'),
        sa.Column('max_episode_limit_usd', sa.Float(), nullable=False, server_default='1.50'),
        sa.Column('universe_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

    # 2. CostTransaction
    op.create_table(
        'finance_cost_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ledger_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('finance_budget_ledgers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('job_id', sa.String(length=100), nullable=True, index=True),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='script'),
        sa.Column('provider', sa.String(length=100), nullable=False, server_default='bedrock_nova'),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('units_consumed', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('finance_cost_transactions')
    op.drop_table('finance_budget_ledgers')
