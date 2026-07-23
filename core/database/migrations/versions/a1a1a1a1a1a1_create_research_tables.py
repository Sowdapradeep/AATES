"""Create research tables

Revision ID: a1a1a1a1a1a1
Revises: 99e6983a54b3
Create Date: 2026-07-17 11:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1a1a1a1a1a1'
down_revision: Union[str, Sequence[str], None] = '99e6983a54b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. research_jobs
    op.create_table(
        "research_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="QUEUED"),
        sa.Column("stage", sa.String(length=50), nullable=False, server_default="DISCOVERING"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("providers_used", sa.JSON(), nullable=True),
        sa.Column("search_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("summary_time_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 2. research_sources
    op.create_table(
        "research_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["research_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 3. knowledge_packages
    op.create_table(
        "knowledge_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("audience", sa.JSON(), nullable=True),
        sa.Column("pain_points", sa.JSON(), nullable=True),
        sa.Column("faqs", sa.JSON(), nullable=True),
        sa.Column("competitors", sa.JSON(), nullable=True),
        sa.Column("statistics", sa.JSON(), nullable=True),
        sa.Column("story_structure", sa.JSON(), nullable=True),
        sa.Column("visual_ideas", sa.JSON(), nullable=True),
        sa.Column("outline", sa.JSON(), nullable=True),
        sa.Column("hooks", sa.JSON(), nullable=True),
        sa.Column("ctas", sa.JSON(), nullable=True),
        sa.Column("titles", sa.JSON(), nullable=True),
        sa.Column("references", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["research_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # 4. trending_topics
    op.create_table(
        "trending_topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("popularity_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("language", sa.String(length=50), nullable=False, server_default="ta"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )

    # 5. keywords
    op.create_table(
        "keywords",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("keyword", sa.String(length=100), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("difficulty", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["research_jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )

    # 6. competitors
    op.create_table(
        "competitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("weaknesses", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["research_jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("competitors")
    op.drop_table("keywords")
    op.drop_table("trending_topics")
    op.drop_table("knowledge_packages")
    op.drop_table("research_sources")
    op.drop_table("research_jobs")
