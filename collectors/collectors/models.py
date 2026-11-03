"""
SQLAlchemy Table definitions (used by Alembic migrations AND run.py).
Python owns the schema — never edit from web/.
"""

from __future__ import annotations

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

companies = Table(
    "companies",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False, unique=True),
)

sources = Table(
    "sources",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("company_id", Integer, nullable=False),  # FK to companies.id (added in migration)
    Column("slug", String(100), nullable=False, unique=True),
    Column("type", String(50), nullable=False),  # greenhouse | lever | ashby | custom
    Column("config", JSON, nullable=False, server_default="{}"),
    Column("enabled", Boolean, nullable=False, server_default="true"),
    Column("poll_interval_minutes", Integer, nullable=False, server_default="30"),
)

jobs = Table(
    "jobs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("source_id", Integer, nullable=False),  # FK to sources.id
    Column("company_id", Integer, nullable=False),  # FK to companies.id
    Column("external_id", String(255), nullable=False),
    Column("fingerprint", String(64), nullable=False, index=True),
    Column("title", String(500), nullable=False),
    Column("location", Text, nullable=True),
    Column("url", Text, nullable=False),
    Column("department", String(255), nullable=True),
    Column("description", Text, nullable=True),
    Column("category", String(100), nullable=True),
    Column("level", String(50), nullable=True, server_default="unknown"),
    # Dates — all UTC
    Column("posted_at", DateTime(timezone=True), nullable=True),
    Column("posted_at_source", String(10), nullable=False, server_default="none"),
    Column("first_seen_at", DateTime(timezone=True), nullable=False),
    Column("last_seen_at", DateTime(timezone=True), nullable=False),
    # Status
    Column("status", String(20), nullable=False, server_default="active"),
    UniqueConstraint("source_id", "external_id", name="uq_jobs_source_external"),
)

source_runs = Table(
    "source_runs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("source_id", Integer, nullable=False),  # FK to sources.id
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True), nullable=True),
    Column("status", String(20), nullable=False),  # success | failed | running
    Column("jobs_found", Integer, nullable=False, server_default="0"),
    Column("new_count", Integer, nullable=False, server_default="0"),
    Column("error", Text, nullable=True),
)

preferences = Table(
    "preferences",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("include_keywords", ARRAY(Text), nullable=False, server_default="{}"),
    Column("exclude_keywords", ARRAY(Text), nullable=False, server_default="{}"),
    Column("locations", ARRAY(Text), nullable=False, server_default="{}"),
    Column("levels", ARRAY(Text), nullable=False, server_default="{}"),
    Column("companies", ARRAY(Text), nullable=False, server_default="{}"),
    Column("categories", ARRAY(Text), nullable=False, server_default="{}"),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

applications = Table(
    "applications",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, nullable=False),  # FK to jobs.id
    # status: saved/applied/interview/rejected/offer
    Column("status", String(50), nullable=False, server_default="saved"),
    Column("notes", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("job_id", name="uq_applications_job_id"),
)

notifications = Table(
    "notifications",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, nullable=False),  # FK to jobs.id
    Column("channel", String(50), nullable=False, server_default="telegram"),
    Column("sent_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("job_id", name="uq_notifications_job_id"),
)
