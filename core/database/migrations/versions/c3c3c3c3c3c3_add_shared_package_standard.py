"""Add shared package standard columns

Revision ID: c3c3c3c3c3c3
Revises: b2b2b2b2b2b2
Create Date: 2026-07-17 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3c3c3c3c3c3'
down_revision: Union[str, Sequence[str], None] = 'b2b2b2b2b2b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update knowledge_packages
    op.add_column("knowledge_packages", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("knowledge_packages", sa.Column("parent_package_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("knowledge_packages", sa.Column("source_agent", sa.String(length=100), nullable=True))
    op.add_column("knowledge_packages", sa.Column("provider", sa.String(length=100), nullable=True))
    op.add_column("knowledge_packages", sa.Column("model", sa.String(length=100), nullable=True))
    op.add_column("knowledge_packages", sa.Column("prompt_version", sa.String(length=50), nullable=True))
    op.add_column("knowledge_packages", sa.Column("quality_score", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("knowledge_packages", sa.Column("telemetry_metadata", sa.JSON(), nullable=True))
    op.add_column("knowledge_packages", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))

    # 2. Update script_packages
    op.add_column("script_packages", sa.Column("parent_package_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("script_packages", sa.Column("source_agent", sa.String(length=100), nullable=True))
    op.add_column("script_packages", sa.Column("provider", sa.String(length=100), nullable=True))
    op.add_column("script_packages", sa.Column("model", sa.String(length=100), nullable=True))
    op.add_column("script_packages", sa.Column("prompt_version", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("script_packages", "prompt_version")
    op.drop_column("script_packages", "model")
    op.drop_column("script_packages", "provider")
    op.drop_column("script_packages", "source_agent")
    op.drop_column("script_packages", "parent_package_id")

    op.drop_column("knowledge_packages", "updated_at")
    op.drop_column("knowledge_packages", "telemetry_metadata")
    op.drop_column("knowledge_packages", "quality_score")
    op.drop_column("knowledge_packages", "prompt_version")
    op.drop_column("knowledge_packages", "model")
    op.drop_column("knowledge_packages", "provider")
    op.drop_column("knowledge_packages", "source_agent")
    op.drop_column("knowledge_packages", "parent_package_id")
    op.drop_column("knowledge_packages", "version")
