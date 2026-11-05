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


# ---------------------------------------------------------------------------
# Role preset keyword matching tests
# Mirrors the ROLE_PRESETS defined in web/src/app/settings/PresetToggles.tsx.
# Tests verify that matches_preferences() with OR semantics (any keyword can
# match) correctly handles preset-sourced include_keywords lists.
# ---------------------------------------------------------------------------

# Software Development preset keywords
_SOFTWARE_DEV_KEYWORDS = [
    "software engineer",
    "developer",
    "SDE",
    "SWE",
    "frontend",
    "backend",
    "fullstack",
    "full-stack",
    "web developer",
    "mobile developer",
]

# QA / Testing preset keywords
_QA_KEYWORDS = [
    "QA",
    "quality assurance",
    "test engineer",
    "SDET",
    "automation tester",
    "software tester",
    "manual tester",
]

# Cloud / DevOps preset keywords
_CLOUD_DEVOPS_KEYWORDS = [
    "devops",
    "cloud engineer",
    "SRE",
    "site reliability",
    "platform engineer",
    "infrastructure engineer",
    "kubernetes",
]


def test_software_development_preset_matches():
    """Jobs with any Software Development preset keyword should match."""
    prefs = {"include_keywords": _SOFTWARE_DEV_KEYWORDS}

    matching_jobs = [
        {"title": "Software Engineer", "description": "Build distributed systems"},
        {"title": "Junior Frontend Developer", "description": "React, TypeScript"},
        {"title": "SDE I — Payments Team", "description": "Python, Go"},
        {"title": "Full-Stack Engineer", "description": "Node.js, PostgreSQL"},
        {"title": "Mobile Developer (Android)", "description": "Kotlin, Jetpack Compose"},
    ]
    for job in matching_jobs:
        assert matches_preferences(job, prefs) is True, f"Should match: {job['title']!r}"

    non_matching_jobs = [
        {"title": "Sales Manager", "description": "Drive B2B revenue growth"},
        {"title": "HR Business Partner", "description": "Talent acquisition and retention"},
        {"title": "Data Analyst", "description": "SQL, Tableau, business intelligence"},
    ]
    for job in non_matching_jobs:
        assert matches_preferences(job, prefs) is False, f"Should NOT match: {job['title']!r}"


def test_qa_preset_matches():
    """Jobs with any QA/Testing preset keyword should match."""
    prefs = {"include_keywords": _QA_KEYWORDS}

    matching_jobs = [
        {"title": "QA Engineer", "description": "Selenium, Cypress"},
        {"title": "SDET", "description": "Test automation frameworks"},
        {"title": "Software Tester — Manual", "description": "Regression, smoke, UAT"},
        {"title": "Quality Assurance Analyst", "description": "Functional testing"},
        {"title": "Automation Tester", "description": "Python pytest"},
    ]
    for job in matching_jobs:
        assert matches_preferences(job, prefs) is True, f"Should match: {job['title']!r}"

    non_matching_jobs = [
        {"title": "Software Engineer", "description": "Backend Python services"},
        {"title": "DevOps Engineer", "description": "CI/CD, Kubernetes, AWS"},
    ]
    for job in non_matching_jobs:
        assert matches_preferences(job, prefs) is False, f"Should NOT match: {job['title']!r}"


def test_cloud_devops_preset_matches():
    """Jobs with any Cloud/DevOps preset keyword should match."""
    prefs = {"include_keywords": _CLOUD_DEVOPS_KEYWORDS}

    matching_jobs = [
        {"title": "DevOps Engineer", "description": "CI/CD pipelines, Jenkins"},
        {"title": "Site Reliability Engineer (SRE)", "description": "On-call, observability"},
        {"title": "Cloud Engineer", "description": "AWS, Azure, Terraform"},
        {"title": "Platform Engineer", "description": "Kubernetes, Helm, ArgoCD"},
        {"title": "Infrastructure Engineer", "description": "Linux, networking, automation"},
    ]
    for job in matching_jobs:
        assert matches_preferences(job, prefs) is True, f"Should match: {job['title']!r}"

    non_matching_jobs = [
        {"title": "Sales Development Representative", "description": "Cold outreach"},
        {"title": "Graphic Designer", "description": "Figma, Adobe Illustrator"},
    ]
    for job in non_matching_jobs:
        assert matches_preferences(job, prefs) is False, f"Should NOT match: {job['title']!r}"


def test_or_semantics_with_multiple_preset_keywords():
    """
    Regression: when include_keywords has multiple items, any single match is
    sufficient (OR semantics). Previously the SQL used AND, which would exclude
    jobs matching only one keyword. This test guards that Python logic stays OR.
    """
    prefs = {
        "include_keywords": ["software engineer", "developer", "SDE", "frontend", "backend"]
    }

    # Each job title matches ONLY ONE keyword — must still match with OR semantics
    single_match_jobs = [
        {"title": "Software Engineer I", "description": "No other keywords here"},
        {"title": "Frontend Developer", "description": "No other keywords here"},
        {"title": "SDE Intern", "description": "No other keywords here"},
    ]
    for job in single_match_jobs:
        assert matches_preferences(job, prefs) is True, (
            f"OR semantics: single keyword match should be sufficient for {job['title']!r}"
        )

