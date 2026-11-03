"""add lever spotify source config row

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-03
"""

from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("INSERT INTO companies (name) VALUES ('Spotify') ON CONFLICT (name) DO NOTHING;")
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO sources (company_id, slug, type, config, enabled, poll_interval_minutes)
            SELECT id, 'lever:spotify', 'lever', :config, true, 30
            FROM companies
            WHERE name = 'Spotify'
            ON CONFLICT (slug) DO NOTHING;
            """
        ),
        {"config": json.dumps({"site": "spotify"})},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM sources WHERE slug = 'lever:spotify';"))
