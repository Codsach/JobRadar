"""add unique constraint and index to applications table

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-03
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Add unique constraint on job_id so that each job has at most one application entry (allowing ON CONFLICT (job_id))
    op.create_unique_constraint("uq_applications_job_id", "applications", ["job_id"])
    op.create_index("ix_applications_status", "applications", ["status"])


def downgrade() -> None:
    op.drop_index("ix_applications_status", table_name="applications")
    op.drop_constraint("uq_applications_job_id", "applications", type_="unique")

