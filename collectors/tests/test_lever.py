"""
Tests for LeverCollector.normalize() using the saved real fixture.

The fixture (tests/fixtures/lever_spotify.json) was saved from a live
call to https://api.lever.co/v0/postings/spotify?mode=json
and contains real jobs as returned by the Lever Postings API.
No network calls are made here.
"""

from __future__ import annotations

import json
from datetime import timezone
from pathlib import Path

import pytest

from collectors.adapters.lever import LeverCollector
from collectors.base import Job

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "lever_spotify.json"


@pytest.fixture
def raw_fixture() -> list[dict]:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def collector() -> LeverCollector:
    return LeverCollector(site="spotify", company_name="Spotify")


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
        assert job.company_name == "Spotify"
        assert job.url.startswith("http"), f"Bad URL: {job.url}"
        assert job.source_slug == "lever:spotify"


def test_normalize_posted_at_source(collector, raw_fixture):
    """posted_at_source must be 'api' when createdAt is present, else 'none'."""
    jobs = collector.normalize(raw_fixture)
    for job in jobs:
        assert job.posted_at_source in ("api", "none"), (
            f"Unexpected posted_at_source={job.posted_at_source!r}"
        )
        if job.posted_at is not None:
            assert job.posted_at_source == "api"
            assert job.posted_at.tzinfo == timezone.utc
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


def test_normalize_multi_location(collector, raw_fixture):
    """Postings with multiple locations in allLocations join them with comma."""
    jobs = collector.normalize(raw_fixture)
    # Find jobs from raw fixture that have multiple locations
    multi_raw_ids = {
        item["id"]
        for item in raw_fixture
        if len(item.get("categories", {}).get("allLocations", [])) > 1
    }
    assert len(multi_raw_ids) > 0, "Expected at least one multi-location job in fixture"
    multi_jobs = [j for j in jobs if j.external_id in multi_raw_ids]
    assert len(multi_jobs) > 0
    for j in multi_jobs:
        assert "," in j.location


def test_normalize_handles_wrapped_dict(collector, raw_fixture):
    """normalize() accepts either list or dict with 'postings' key."""
    jobs_from_list = collector.normalize(raw_fixture)
    jobs_from_dict = collector.normalize({"postings": raw_fixture})
    assert len(jobs_from_list) == len(jobs_from_dict)
    assert [j.external_id for j in jobs_from_list] == [j.external_id for j in jobs_from_dict]


def test_fixture_contains_spotify_jobs(raw_fixture):
    """Sanity: fixture has jobs and they contain Spotify posting data."""
    assert len(raw_fixture) >= 1
    first = raw_fixture[0]
    assert "hostedUrl" in first
    assert "spotify" in first["hostedUrl"].lower()

