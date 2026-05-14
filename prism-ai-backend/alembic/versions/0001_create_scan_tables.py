"""create scans and feedback tables

Revision ID: 0001_create_scan_tables
Revises:
Create Date: 2026-05-10 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_create_scan_tables"
down_revision = None
branch_labels = None
depends_on = None


def _uuid_type():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "scans",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("input_url", sa.Text(), nullable=True),
        sa.Column("fetched_text", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="internship"),
        sa.Column("extracted_title", sa.String(length=255), nullable=True),
        sa.Column("extracted_company", sa.String(length=255), nullable=True),
        sa.Column("extracted_mode", sa.String(length=50), nullable=True),
        sa.Column("extracted_stipend", sa.String(length=255), nullable=True),
        sa.Column("extracted_duration", sa.String(length=100), nullable=True),
        sa.Column("extracted_skills", sa.JSON(), nullable=True),
        sa.Column("trust_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scam_likelihood", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("risk_level", sa.String(length=80), nullable=False, server_default="Needs Manual Verification"),
        sa.Column("confidence", sa.String(length=20), nullable=False, server_default="Low"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("green_flags", sa.JSON(), nullable=True),
        sa.Column("red_flags", sa.JSON(), nullable=True),
        sa.Column("missing_information", sa.JSON(), nullable=True),
        sa.Column("verification_signals", sa.JSON(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("safe_message", sa.Text(), nullable=True),
        sa.Column("agent_trace", sa.JSON(), nullable=True),
        sa.Column("raw_llm_output", sa.JSON(), nullable=True),
        sa.Column("source_results", sa.JSON(), nullable=True),
    )
    op.create_table(
        "feedback",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False),
        sa.Column("scan_id", _uuid_type(), sa.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_rating", sa.String(length=20), nullable=False),
        sa.Column("user_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("scans")
