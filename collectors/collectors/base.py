"""
Base interface for all job collectors.

Every adapter must implement:
  fetch()     → raw API response (dict) — no transformation
  normalize() → list[Job] — validated, typed records

Rules (AGENTS.md):
- posted_at is nullable; only set it when the source gives a real date.
- first_seen_at is set by the caller (run.py), NOT the adapter.
- Never fabricate data.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Job:
    """Normalised job record produced by every adapter."""

    # Identity
    external_id: str  # source's own job ID (string form)
    source_slug: str  # e.g. "greenhouse:stripe"

    # Content
    title: str
    company_name: str
    location: str  # single string; multi-location → join with ", "
    url: str

    # Dates — all UTC-aware datetimes or None
    posted_at: datetime | None  # nullable; only from source
    posted_at_source: str  # "api" | "parsed" | "none"
    # first_seen_at and last_seen_at are managed by run.py / DB

    # Optional
    department: str | None = field(default=None)
    description: str | None = field(default=None)
    category: str = field(default="Other Tech")
    level: str = field(default="unknown")

    @property
    def fingerprint(self) -> str:
        """SHA-256 of company + title + location (lower-cased, stripped)."""
        raw = "\n".join(
            [
                self.company_name.lower().strip(),
                self.title.lower().strip(),
                self.location.lower().strip(),
            ]
        )
        return hashlib.sha256(raw.encode()).hexdigest()


class Collector(ABC):
    """Abstract base class every adapter must implement."""

    @abstractmethod
    def fetch(self) -> dict[str, Any]:
        """
        Fetch the raw API response.
        Must return the parsed JSON as a dict (or raise on error).
        Do NOT transform data here.
        """
        ...

    @abstractmethod
    def normalize(self, raw: dict[str, Any]) -> list[Job]:
        """
        Convert a raw API response (as returned by fetch) into Job records.
        Must only use field names that actually exist in the raw response.
        """
        ...
