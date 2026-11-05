"""
python -m collectors.run
Fetch → normalize → upsert jobs for configured sources.
Handles:
- Deduplication and upsert
- Baseline run detection (first run suppresses notifications)
- Preference matching
- Batched digest (>5 matching jobs) vs individual alerts (<=5)
- Telegram rate limit compliance
- Health alerts on source failure, 0 jobs, or sudden drop
- Records source_runs and notifications
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

# Load .env from repo root before anything else
_here = os.path.dirname(__file__)
_env_path = os.path.join(_here, "..", "..", ".env")
load_dotenv(dotenv_path=os.path.normpath(_env_path), override=False)

from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402

from collectors.adapters.greenhouse import GreenhouseCollector  # noqa: E402
from collectors.adapters.lever import LeverCollector  # noqa: E402
from collectors.db import get_engine  # noqa: E402
from collectors.models import (  # noqa: E402
    companies,
    jobs,
    notifications,
    source_runs,
    sources,
)
from collectors.preferences import load_preferences, matches_preferences  # noqa: E402
from collectors.telegram import TelegramSender  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BOARD_TOKEN = os.environ.get("GREENHOUSE_BOARD_TOKEN", "stripe")


def _ensure_company(conn, name: str) -> int:
    """Insert company if not exists; return id."""
    stmt = pg_insert(companies).values(name=name)
    stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
    conn.execute(stmt)
    row = conn.execute(select(companies.c.id).where(companies.c.name == name)).one()
    return row.id


def _ensure_source(conn, company_id: int, slug: str, board_token: str) -> int:
    """Insert source row if not exists; return id."""
    stmt = pg_insert(sources).values(
        company_id=company_id,
        slug=slug,
        type="greenhouse",
        config={"board_token": board_token},
        enabled=True,
        poll_interval_minutes=30,
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=["slug"])
    conn.execute(stmt)
    row = conn.execute(select(sources.c.id).where(sources.c.slug == slug)).one()
    return row.id


def _get_baseline_finished_at(conn, source_id: int) -> datetime | None:
    """
    Get the finished_at of the earliest successful run for this source.
    If None, this run is the baseline run.
    """
    row = conn.execute(
        select(source_runs.c.finished_at)
        .where(
            source_runs.c.source_id == source_id,
            source_runs.c.status == "success",
        )
        .order_by(source_runs.c.started_at.asc())
        .limit(1)
    ).first()
    return row[0] if row else None


def _get_previous_run_job_count(conn, source_id: int) -> int | None:
    """Get jobs_found from the most recent successful run."""
    row = conn.execute(
        select(source_runs.c.jobs_found)
        .where(
            source_runs.c.source_id == source_id,
            source_runs.c.status == "success",
        )
        .order_by(source_runs.c.started_at.desc())
        .limit(1)
    ).first()
    return row[0] if row else None


def run_source(
    engine,
    collector,
    telegram: TelegramSender,
    board_token: str,
    source_slug: str | None = None,
    company_name: str | None = None,
    source_id: int | None = None,
    source_type: str = "greenhouse",
    enabled: bool = True,
) -> None:
    """Run collection, persistence, health checking, and alerts for one source."""
    slug = source_slug or f"{source_type}:{board_token}"
    if source_type == "manual" or not enabled or collector is None:
        logger.info("Skipping manual/disabled source %s without collection.", slug)
        return

    run_started_at = datetime.now(timezone.utc)
    source_slug = slug
    company_name = company_name or board_token.title()

    # Pre-ensure company and source to obtain source_id
    with engine.begin() as conn:
        company_id = _ensure_company(conn, company_name)
        if source_id is None:
            source_id = _ensure_source(conn, company_id, source_slug, board_token)
        baseline_finished_at = _get_baseline_finished_at(conn, source_id)
        prev_jobs_found = _get_previous_run_job_count(conn, source_id)
        prefs = load_preferences(conn)

    is_baseline_run = baseline_finished_at is None

    # Step 1: Fetch and normalize
    try:
        logger.info("Fetching jobs from Greenhouse board %r …", board_token)
        raw = collector.fetch()
        job_list = collector.normalize(raw)
        logger.info("Fetched %d jobs", len(job_list))
    except Exception as exc:
        error_msg = f"Failed to fetch or normalize jobs: {exc}"
        logger.exception(error_msg)
        with engine.begin() as conn:
            conn.execute(
                pg_insert(source_runs).values(
                    source_id=source_id,
                    started_at=run_started_at,
                    finished_at=datetime.now(timezone.utc),
                    status="failed",
                    jobs_found=0,
                    new_count=0,
                    error=str(exc),
                )
            )
        telegram.send_health_alert(source_slug, "failure", str(exc))
        return

    # Health check: 0 jobs returned
    if len(job_list) == 0:
        logger.warning("Source %s returned 0 jobs.", source_slug)
        with engine.begin() as conn:
            conn.execute(
                pg_insert(source_runs).values(
                    source_id=source_id,
                    started_at=run_started_at,
                    finished_at=datetime.now(timezone.utc),
                    status="success",
                    jobs_found=0,
                    new_count=0,
                    error=None,
                )
            )
        telegram.send_health_alert(source_slug, "zero_jobs", "0 jobs returned")
        return

    # Health check: far fewer jobs than previous run (drop >= 50% when prev had >= 10)
    if prev_jobs_found and prev_jobs_found >= 10 and len(job_list) <= (prev_jobs_found * 0.5):
        drop_pct = round(((prev_jobs_found - len(job_list)) / prev_jobs_found) * 100)
        warning_msg = (
            f"Returned {len(job_list)} jobs vs {prev_jobs_found} in previous run "
            f"({drop_pct}% decrease)"
        )
        logger.warning("Job drop warning for %s: %s", source_slug, warning_msg)
        telegram.send_health_alert(source_slug, "drop", warning_msg)

    # Step 2: Upsert jobs
    now = datetime.now(timezone.utc)
    inserted = 0
    updated = 0

    with engine.begin() as conn:
        for job in job_list:
            stmt = (
                pg_insert(jobs)
                .values(
                    source_id=source_id,
                    company_id=company_id,
                    external_id=job.external_id,
                    fingerprint=job.fingerprint,
                    title=job.title,
                    location=job.location,
                    url=job.url,
                    department=job.department,
                    description=job.description,
                    category=job.category,
                    level=job.level,
                    posted_at=job.posted_at,
                    posted_at_source=job.posted_at_source,
                    first_seen_at=now,
                    last_seen_at=now,
                    status="active",
                )
                .on_conflict_do_update(
                    index_elements=["source_id", "external_id"],
                    set_={
                        "last_seen_at": now,
                        "status": "active",
                        "category": text("EXCLUDED.category"),
                        "level": text("EXCLUDED.level"),
                        "posted_at": text(
                            "CASE WHEN jobs.posted_at IS NULL THEN EXCLUDED.posted_at "
                            "ELSE jobs.posted_at END"
                        ),
                        "posted_at_source": text(
                            "CASE WHEN jobs.posted_at IS NULL THEN EXCLUDED.posted_at_source "
                            "ELSE jobs.posted_at_source END"
                        ),
                    },
                )
                .returning(text("xmax::text::int"))
            )
            row = conn.execute(stmt).scalar()
            if row == 0:
                inserted += 1
            else:
                updated += 1

        # Record successful source run
        conn.execute(
            pg_insert(source_runs).values(
                source_id=source_id,
                started_at=run_started_at,
                finished_at=datetime.now(timezone.utc),
                status="success",
                jobs_found=len(job_list),
                new_count=inserted,
                error=None,
            )
        )

    logger.info(
        "Source %s complete. inserted=%d updated=%d total=%d",
        source_slug,
        inserted,
        updated,
        len(job_list),
    )

    # Step 3: Alerting
    if is_baseline_run:
        logger.info(
            "Baseline run completed for source %s (%d jobs found). "
            "Notifications suppressed per PRD §8.",
            source_slug,
            len(job_list),
        )
        return

    # Find candidate jobs first seen after baseline that haven't been notified yet
    with engine.begin() as conn:
        stmt = (
            select(
                jobs.c.id,
                jobs.c.title,
                companies.c.name.label("company_name"),
                jobs.c.location,
                jobs.c.url,
                jobs.c.category,
                jobs.c.level,
                jobs.c.description,
                jobs.c.posted_at,
                jobs.c.first_seen_at,
            )
            .select_from(
                jobs.join(companies, companies.c.id == jobs.c.company_id).outerjoin(
                    notifications, notifications.c.job_id == jobs.c.id
                )
            )
            .where(
                jobs.c.source_id == source_id,
                jobs.c.status == "active",
                notifications.c.id.is_(None),
                jobs.c.first_seen_at > baseline_finished_at,
            )
            .order_by(jobs.c.first_seen_at.desc())
        )
        unnotified_rows = conn.execute(stmt).mappings().all()

    # Filter matching preferences
    matching_jobs: list[dict[str, Any]] = [
        dict(row) for row in unnotified_rows if matches_preferences(row, prefs)
    ]

    logger.info(
        "Found %d unnotified jobs after baseline (%d match preferences).",
        len(unnotified_rows),
        len(matching_jobs),
    )

    if not matching_jobs:
        return

    # Dispatch alerts
    sent_job_ids: list[int] = []

    if len(matching_jobs) > 5:
        # Batched digest when > 5 matches arrive in one run
        logger.info("Sending batched digest for %d matching jobs...", len(matching_jobs))
        digest_text = telegram.format_digest(matching_jobs)
        sent = telegram.send_raw_message(digest_text)
        if sent or not telegram.enabled:
            sent_job_ids = [j["id"] for j in matching_jobs]
    else:
        # Individual alerts for <= 5 matches, respecting rate limits
        logger.info("Sending %d individual job alerts...", len(matching_jobs))
        for idx, job in enumerate(matching_jobs):
            if idx > 0:
                time.sleep(1.0)  # Telegram rate limit (~1 msg/sec to chat)
            job_text = telegram.format_single_job(job)
            sent = telegram.send_raw_message(job_text)
            if sent or not telegram.enabled:
                sent_job_ids.append(job["id"])

    # Record sent notifications in database (each job notified at most once)
    if sent_job_ids:
        with engine.begin() as conn:
            for job_id in sent_job_ids:
                stmt = (
                    pg_insert(notifications)
                    .values(
                        job_id=job_id,
                        channel="telegram",
                        sent_at=datetime.now(timezone.utc),
                    )
                    .on_conflict_do_nothing(index_elements=["job_id"])
                )
                conn.execute(stmt)
        logger.info("Recorded %d jobs in notifications table.", len(sent_job_ids))


def main() -> None:
    engine = get_engine()
    telegram = TelegramSender()

    with engine.begin() as conn:
        stmt = select(
            sources.c.id,
            sources.c.slug,
            sources.c.type,
            sources.c.config,
            sources.c.enabled,
            companies.c.name.label("company_name"),
        ).select_from(sources.join(companies, companies.c.id == sources.c.company_id))
        all_sources = conn.execute(stmt).mappings().all()

    if not all_sources:
        collector = GreenhouseCollector(board_token=BOARD_TOKEN)
        run_source(
            engine=engine,
            collector=collector,
            telegram=telegram,
            board_token=BOARD_TOKEN,
        )
        return

    for src in all_sources:
        if src["type"] == "manual" or not src["enabled"]:
            logger.info(
                "Skipping %s source %s (enabled=%s)",
                src["type"],
                src["slug"],
                src["enabled"],
            )
            continue

        collector = None
        token = ""
        cfg = src["config"] or {}
        if src["type"] == "greenhouse":
            token = cfg.get("board_token") or src["slug"].split(":")[-1]
            collector = GreenhouseCollector(board_token=token)
        elif src["type"] == "lever":
            token = cfg.get("site") or src["slug"].split(":")[-1]
            collector = LeverCollector(site=token, company_name=src["company_name"])
        else:
            logger.warning("Unknown collector type %r for source %s", src["type"], src["slug"])
            continue

        run_source(
            engine=engine,
            collector=collector,
            telegram=telegram,
            board_token=token,
            source_slug=src["slug"],
            company_name=src["company_name"],
            source_id=src["id"],
            source_type=src["type"],
            enabled=src["enabled"],
        )


if __name__ == "__main__":
    main()
