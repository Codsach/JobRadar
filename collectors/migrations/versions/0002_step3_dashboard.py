"""add category and level to jobs, create source_runs, preferences, and applications tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-03
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # 1. Add category and level to jobs table
    op.add_column("jobs", sa.Column("category", sa.String(100), nullable=True))
    op.add_column("jobs", sa.Column("level", sa.String(50), nullable=True, server_default="unknown"))

    # 2. Create source_runs table
    op.create_table(
        "source_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("jobs_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. Create preferences table
    op.create_table(
        "preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("include_keywords", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("exclude_keywords", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("locations", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("levels", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("companies", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("categories", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Seed default preferences row (id=1)
    op.execute(
        "INSERT INTO preferences (id, include_keywords, exclude_keywords, locations, levels, companies, categories, updated_at) "
        "VALUES (1, '{}', '{}', '{}', '{}', '{}', '{}', NOW()) ON CONFLICT (id) DO NOTHING"
    )

    # 4. Create applications table
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="saved"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("applications")
    op.drop_table("preferences")
    op.drop_table("source_runs")
    op.drop_column("jobs", "level")
    op.drop_column("jobs", "category")

