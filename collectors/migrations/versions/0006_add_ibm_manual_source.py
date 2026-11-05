"""add ibm manual source config row

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-04
"""

from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("INSERT INTO companies (name) VALUES ('IBM') ON CONFLICT (name) DO NOTHING;")
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO sources (company_id, slug, type, config, enabled, poll_interval_minutes)
            SELECT id, 'manual:ibm', 'manual', :config, false, 0
            FROM companies
            WHERE name = 'IBM'
            ON CONFLICT (slug) DO NOTHING;
            """
        ),
        {"config": json.dumps({"careers_url": "https://www.ibm.com/careers/search"})},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM sources WHERE slug = 'manual:ibm';"))

