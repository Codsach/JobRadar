"""
GreenhouseCollector — public Greenhouse board API.

API docs: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
No authentication required. Returns JSON with a top-level "jobs" list.

Real field names confirmed from live Stripe response saved in
tests/fixtures/greenhouse_stripe.json:
  id               int   — Greenhouse job ID → external_id
  title            str
  company_name     str
  location.name    str   — primary location string
  absolute_url     str   — link to apply
  first_published  str   — ISO 8601 date with TZ offset; present on Stripe board
  updated_at       str   — ISO 8601; used for last_seen_at reference
  departments[]    list  — each has .name
  content          str   — HTML job description (optional, behind ?content=true)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from collectors.base import Collector, Job
from collectors.classifier import classify_category, classify_level

logger = logging.getLogger(__name__)

_BASE = "https://boards-api.greenhouse.io/v1/boards"
_USER_AGENT = "JobRadar/0.1 (personal job tracker; github.com/jobradar)"
_TIMEOUT = 30.0


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO 8601 string with optional TZ offset into a UTC datetime."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        logger.warning("Could not parse date %r", value)
        return None


class GreenhouseCollector(Collector):
    """Fetches jobs from one Greenhouse board (public API, no auth)."""

    def __init__(self, board_token: str) -> None:
        self.board_token = board_token
        self.source_slug = f"greenhouse:{board_token}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def fetch(self) -> dict[str, Any]:
        """GET /v1/boards/{token}/jobs?content=true and return parsed JSON."""
        url = f"{_BASE}/{self.board_token}/jobs?content=true"
        logger.info("Fetching %s", url)
        with httpx.Client(
            headers={"User-Agent": _USER_AGENT},
            timeout=_TIMEOUT,
            follow_redirects=True,
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()

    def normalize(self, raw: dict[str, Any]) -> list[Job]:
        """
        Convert the raw Greenhouse API response into Job records.

        Field mapping (from real Stripe response):
          raw["jobs"]              → list of job objects
          job["id"]                → external_id  (int → str)
          job["title"]             → title
          job["company_name"]      → company_name
          job["location"]["name"]  → location
          job["absolute_url"]      → url
          job["first_published"]   → posted_at (if present and non-null)
          job["departments"][0]["name"] → department (if present)
          job["content"]           → description (if present)
        """
        jobs_raw = raw.get("jobs", [])
        result: list[Job] = []

        for item in jobs_raw:
            # Location: Greenhouse returns {"name": "Dublin"} or null
            loc_obj = item.get("location") or {}
            location = loc_obj.get("name") or ""

            # Posting date: use first_published if it exists and is non-null
            first_published = item.get("first_published")
            posted_at = _parse_dt(first_published)
            posted_at_source = "api" if posted_at is not None else "none"

            # Department: first department name if list is non-empty
            departments = item.get("departments") or []
            department = departments[0]["name"] if departments else None

            # Description: HTML content (may be large; nullable)
            description = item.get("content") or None

            category = classify_category(item["title"], text=description)
            level = classify_level(item["title"], text=description)

            job = Job(
                external_id=str(item["id"]),
                source_slug=self.source_slug,
                title=item["title"],
                company_name=item["company_name"],
                location=location,
                url=item["absolute_url"],
                posted_at=posted_at,
                posted_at_source=posted_at_source,
                department=department,
                description=description,
                category=category,
                level=level,
            )
            result.append(job)

        logger.info("Normalized %d jobs from board %r", len(result), self.board_token)
        return result
