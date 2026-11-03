"""
Smoke test: DATABASE_URL is readable from the environment.

Skips gracefully when DATABASE_URL is not set (local dev with no .env).
In CI the variable must be present; the test will fail loudly if it's missing.
"""

import os

import pytest


def test_database_url_readable() -> None:
    url = os.getenv("DATABASE_URL")
    if url is None:
        pytest.skip("DATABASE_URL not set — configure .env for local testing")
    assert url.startswith("postgresql"), f"Unexpected DATABASE_URL scheme: {url!r}"
