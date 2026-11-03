"""
LeverCollector — public Lever Postings API.

API docs: https://github.com/lever/postings-api
No authentication required. Returns JSON array of job postings.

Real field names confirmed from live Spotify response saved in
tests/fixtures/lever_spotify.json:
  id                      str   — Lever posting ID (UUID) → external_id
  text                    str   — Job title
  categories.location     str   — Primary location string
  categories.allLocations list  — List of all location strings
  categories.team         str   — Team / sub-department
  categories.department   str   — Department name
  hostedUrl               str   — Link to apply / job page
  createdAt               int   — Unix epoch timestamp in ms → posted_at
  descriptionPlain        str   — Plaintext description
  description             str   — HTML description
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

_BASE = "https://api.lever.co/v0/postings"
_USER_AGENT = "JobRadar/0.1 (personal job tracker; github.com/jobradar)"
_TIMEOUT = 30.0


def _parse_epoch_ms(value: int | float | None) -> datetime | None:
    """Parse a Unix timestamp in milliseconds into a UTC datetime."""
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        logger.warning("Could not parse epoch milliseconds %r", value)
        return None


class LeverCollector(Collector):
    """Fetches jobs from one Lever board (public API, no auth)."""

    def __init__(self, site: str, company_name: str | None = None) -> None:
        self.site = site
        self.company_name = company_name or site.title()
        self.source_slug = f"lever:{site}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def fetch(self) -> dict[str, Any]:
        """GET /v0/postings/{site}?mode=json and return parsed JSON."""
        url = f"{_BASE}/{self.site}?mode=json"
        logger.info("Fetching %s", url)
        with httpx.Client(
            headers={"User-Agent": _USER_AGENT},
            timeout=_TIMEOUT,
            follow_redirects=True,
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return {"postings": data}
            return data

    def normalize(self, raw: dict[str, Any] | list[dict[str, Any]]) -> list[Job]:
        """
        Convert the raw Lever API response into Job records.

        Field mapping (from real Spotify response):
          posting["id"]                           → external_id
          posting["text"]                         → title
          posting["hostedUrl"]                    → url
          posting["createdAt"]                    → posted_at (if present)
          posting["categories"]["allLocations"]   → location (or categories.location)
          posting["categories"]["team"]           → department (or categories.department)
          posting["descriptionPlain"]            → description
        """
        if isinstance(raw, list):
            postings_raw = raw
        elif isinstance(raw, dict):
            postings_raw = raw.get("postings", raw.get("jobs", []))
        else:
            postings_raw = []

        result: list[Job] = []

        for item in postings_raw:
            cat_obj = item.get("categories") or {}

            # Location: prefer allLocations joined if multiple, else location string
            all_locs = cat_obj.get("allLocations")
            if all_locs and isinstance(all_locs, list) and len(all_locs) > 0:
                location = ", ".join(loc for loc in all_locs if loc)
            else:
                location = cat_obj.get("location") or ""

            # Posting date: Lever provides createdAt in epoch ms
            created_at = item.get("createdAt")
            posted_at = _parse_epoch_ms(created_at)
            posted_at_source = "api" if posted_at is not None else "none"

            # Department: team or department
            department = cat_obj.get("team") or cat_obj.get("department") or None

            # Description: plain text preferred, fallback to HTML
            description = item.get("descriptionPlain") or item.get("description") or None

            title = item.get("text") or ""
            category = classify_category(title, text=description)
            level = classify_level(title, text=description)

            job = Job(
                external_id=str(item["id"]),
                source_slug=self.source_slug,
                title=title,
                company_name=self.company_name,
                location=location,
                url=item.get("hostedUrl") or "",
                posted_at=posted_at,
                posted_at_source=posted_at_source,
                department=department,
                description=description,
                category=category,
                level=level,
            )
            result.append(job)

        logger.info("Normalized %d jobs from site %r", len(result), self.site)
        return result

