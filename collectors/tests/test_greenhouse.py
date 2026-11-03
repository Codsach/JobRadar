"""
Tests for GreenhouseCollector.normalize() using the saved real fixture.

The fixture (tests/fixtures/greenhouse_stripe.json) was saved from a live
call to https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true
and contains the first 5 real jobs as returned by the API.
No network calls are made here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from collectors.adapters.greenhouse import GreenhouseCollector
from collectors.base import Job

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "greenhouse_stripe.json"


@pytest.fixture
def raw_fixture() -> dict:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # The fixture wraps the raw API response under a "meta" key plus the jobs list.
    # We need to reconstruct the shape the API actually returns: {"jobs": [...]}
    return {"jobs": data["jobs"]}


@pytest.fixture
def collector() -> GreenhouseCollector:
    return GreenhouseCollector(board_token="stripe")


def test_normalize_returns_list(collector, raw_fixture):
    jobs = collector.normalize(raw_fixture)
    assert isinstance(jobs, list)
    assert len(jobs) > 0, "Expected at least one job from fixture"


def test_normalize_job_type(collector, raw_fixture):
    jobs = collector.normalize(raw_fixture)
    for job in jobs:
        assert isinstance(job, Job)


def test_normalize_required_fields(collector, raw_fixture):
    """Every job must have non-empty required string fields."""
    jobs = collector.normalize(raw_fixture)
    for job in jobs:
        assert job.external_id, f"Missing external_id: {job}"
        assert job.title, f"Missing title: {job}"
        assert job.company_name, f"Missing company_name: {job}"
        assert job.url.startswith("http"), f"Bad URL: {job.url}"
        assert job.source_slug == "greenhouse:stripe"


def test_normalize_posted_at_source(collector, raw_fixture):
    """posted_at_source must be 'api' when first_published is present, else 'none'."""
    jobs = collector.normalize(raw_fixture)
    for job in jobs:
        assert job.posted_at_source in ("api", "none"), (
            f"Unexpected posted_at_source={job.posted_at_source!r}"
        )
        if job.posted_at is not None:
            assert job.posted_at_source == "api"
        else:
            assert job.posted_at_source == "none"


def test_normalize_fingerprint_stable(collector, raw_fixture):
    """Running normalize() twice on the same data gives the same fingerprints."""
    jobs_a = collector.normalize(raw_fixture)
    jobs_b = collector.normalize(raw_fixture)
    fps_a = [j.fingerprint for j in jobs_a]
    fps_b = [j.fingerprint for j in jobs_b]
    assert fps_a == fps_b


def test_normalize_fingerprint_length(collector, raw_fixture):
    jobs = collector.normalize(raw_fixture)
    for job in jobs:
        assert len(job.fingerprint) == 64, f"Fingerprint is not SHA-256: {job.fingerprint!r}"


def test_fixture_contains_stripe_jobs(raw_fixture):
    """Sanity: fixture has jobs and they are from Stripe."""
    assert len(raw_fixture["jobs"]) >= 1
    first = raw_fixture["jobs"][0]
    assert first["company_name"] == "Stripe"
