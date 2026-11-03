"""
Tests for preference matching logic.
"""

from __future__ import annotations

from collectors.preferences import matches_preferences


def test_matches_empty_preferences():
    """Empty preferences should match any active job."""
    job = {
        "title": "Software Engineer",
        "company_name": "Stripe",
        "location": "Bengaluru",
        "category": "SDE",
        "level": "fresher",
        "description": "Python, Go, Distributed systems",
    }
    prefs = {
        "include_keywords": [],
        "exclude_keywords": [],
        "locations": [],
        "levels": [],
        "companies": [],
        "categories": [],
    }
    assert matches_preferences(job, prefs) is True


def test_level_filtering():
    job = {"title": "SWE", "company_name": "Stripe", "level": "fresher", "category": "SDE"}
    prefs = {"levels": ["experienced"]}
    assert matches_preferences(job, prefs) is False

    prefs_ok = {"levels": ["fresher", "unknown"]}
    assert matches_preferences(job, prefs_ok) is True


def test_category_filtering():
    job = {"title": "QA Engineer", "company_name": "Stripe", "category": "QA", "level": "fresher"}
    prefs = {"categories": ["SDE", "Cloud"]}
    assert matches_preferences(job, prefs) is False

    prefs_ok = {"categories": ["QA"]}
    assert matches_preferences(job, prefs_ok) is True


def test_company_filtering():
    job = {"title": "SWE", "company_name": "Stripe", "category": "SDE", "level": "fresher"}
    prefs = {"companies": ["Google", "Meta"]}
    assert matches_preferences(job, prefs) is False

    prefs_ok = {"companies": ["Stripe"]}
    assert matches_preferences(job, prefs_ok) is True


def test_location_filtering():
    job = {
        "title": "SWE",
        "location": "Bengaluru, Karnataka, India",
        "level": "fresher",
        "category": "SDE",
    }
    prefs = {"locations": ["Hyderabad", "Pune"]}
    assert matches_preferences(job, prefs) is False

    prefs_ok = {"locations": ["Bengaluru", "Remote"]}
    assert matches_preferences(job, prefs_ok) is True


def test_include_keywords():
    job = {
        "title": "Junior Python Backend Developer",
        "description": "Looking for entry level engineers with FastAPI and PostgreSQL",
        "level": "fresher",
        "category": "SDE",
    }
    prefs = {"include_keywords": ["Django", "Ruby"]}
    assert matches_preferences(job, prefs) is False

    prefs_ok = {"include_keywords": ["fastapi", "react"]}
    assert matches_preferences(job, prefs_ok) is True


def test_exclude_keywords():
    job = {
        "title": "Senior Staff Architect",
        "description": "Lead cross-functional teams with 15+ years experience",
        "level": "experienced",
        "category": "SDE",
    }
    prefs = {"exclude_keywords": ["staff", "director"]}
    assert matches_preferences(job, prefs) is False
