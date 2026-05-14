"""add agent workflow fields

Revision ID: 0002_add_agent_workflow_fields
Revises: 0001_create_scan_tables
Create Date: 2026-05-10 00:00:00.000001
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_add_agent_workflow_fields"
down_revision = "0001_create_scan_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("scans") as batch_op:
        batch_op.add_column(sa.Column("workflow_status", sa.String(length=40), nullable=False, server_default="pending"))
        batch_op.add_column(sa.Column("requires_human_review", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        batch_op.add_column(sa.Column("human_review_reason", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("human_decision", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("human_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("graph_thread_id", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("checkpoint_id", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("review_requested_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("review_completed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("final_result", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("scans") as batch_op:
        batch_op.drop_column("final_result")
        batch_op.drop_column("review_completed_at")
        batch_op.drop_column("review_requested_at")
        batch_op.drop_column("checkpoint_id")
        batch_op.drop_column("graph_thread_id")
        batch_op.drop_column("human_notes")
        batch_op.drop_column("human_decision")
        batch_op.drop_column("human_review_reason")
        batch_op.drop_column("requires_human_review")
        batch_op.drop_column("workflow_status")