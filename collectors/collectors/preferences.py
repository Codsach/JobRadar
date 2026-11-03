"""
User preference loading and matching logic.
Mirrors the SQL query filtering logic in web/src/lib/jobs.ts.
"""

from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy import select

from collectors.models import preferences


def load_preferences(conn) -> dict[str, Any]:
    """Load user preferences row from database (id=1), or return defaults."""
    stmt = select(preferences).where(preferences.c.id == 1).limit(1)
    row = conn.execute(stmt).first()
    if not row:
        return {
            "include_keywords": [],
            "exclude_keywords": [],
            "locations": [],
            "levels": [],
            "companies": [],
            "categories": [],
        }

    return {
        "include_keywords": list(row.include_keywords or []),
        "exclude_keywords": list(row.exclude_keywords or []),
        "locations": list(row.locations or []),
        "levels": list(row.levels or []),
        "companies": list(row.companies or []),
        "categories": list(row.categories or []),
    }


def matches_preferences(job: Mapping[str, Any], prefs: Mapping[str, Any]) -> bool:
    """
    Check if a job matches user preferences.
    Empty preference lists mean the field is not restricted (matches anything).
    """
    title = (job.get("title") or "").lower()
    description = (job.get("description") or "").lower()
    location = (job.get("location") or "").lower()
    level = (job.get("level") or "").strip()
    category = (job.get("category") or "").strip()
    company = (job.get("company_name") or "").strip()

    # 1. Level filter
    pref_levels = [lvl.strip() for lvl in prefs.get("levels", []) if lvl.strip()]
    if pref_levels and level not in pref_levels:
        return False

    # 2. Category filter
    pref_categories = [c.strip() for c in prefs.get("categories", []) if c.strip()]
    if pref_categories and category not in pref_categories:
        return False

    # 3. Company filter
    pref_companies = [c.strip() for c in prefs.get("companies", []) if c.strip()]
    if pref_companies and company not in pref_companies:
        return False

    # 4. Location filter (case-insensitive substring match)
    pref_locations = [loc.strip().lower() for loc in prefs.get("locations", []) if loc.strip()]
    if pref_locations:
        if not any(loc in location for loc in pref_locations):
            return False

    # Combined text for keyword checks
    combined_text = f"{title} {description}"

    # 5. Include keywords (at least one must match if specified)
    include_kws = [kw.strip().lower() for kw in prefs.get("include_keywords", []) if kw.strip()]
    if include_kws:
        if not any(kw in combined_text for kw in include_kws):
            return False

    # 6. Exclude keywords (none may match if specified)
    exclude_kws = [kw.strip().lower() for kw in prefs.get("exclude_keywords", []) if kw.strip()]
    if exclude_kws:
        if any(kw in combined_text for kw in exclude_kws):
            return False

    return True
