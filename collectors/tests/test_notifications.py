"""
Tests for notification alerting logic:
- Baseline run suppresses notifications
- Jobs first seen after baseline trigger alerts
- Deduplication: each job notified at most once
- Batched digest when > 5 matches arrive in one run
- Health alert triggers on 0 jobs, sudden drop, or fetch failure
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from collectors.base import Job
from collectors.run import run_source
from collectors.telegram import TelegramSender


@pytest.fixture
def sample_jobs():
    return [
        Job(
            external_id=f"stripe-{i}",
            title=f"Software Engineer {i}",
            company_name="Stripe",
            source_slug="greenhouse:stripe",
            url=f"https://stripe.com/jobs/{i}",
            location="Bengaluru, India",
            department="Engineering",
            description="Backend engineering role",
            category="SDE",
            level="fresher",
            posted_at=None,
            posted_at_source="none",
        )
        for i in range(1, 4)
    ]


def test_baseline_run_suppresses_notifications(sample_jobs):
    """
    On the first run for a source, baseline_finished_at is None.
    Jobs are stored, but notifications are suppressed per PRD §8.
    """
    mock_collector = MagicMock()
    mock_collector.fetch.return_value = {}
    mock_collector.normalize.return_value = sample_jobs

    mock_telegram = MagicMock(spec=TelegramSender)
    mock_telegram.enabled = True

    # Mock engine & connection
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    with (
        patch("collectors.run._ensure_company", return_value=1),
        patch("collectors.run._ensure_source", return_value=1),
        patch("collectors.run._get_baseline_finished_at", return_value=None),  # Baseline run!
        patch("collectors.run._get_previous_run_job_count", return_value=None),
        patch("collectors.run.load_preferences", return_value={}),
    ):
        run_source(
            engine=mock_engine,
            collector=mock_collector,
            telegram=mock_telegram,
            board_token="stripe",
        )

    # Telegram must NOT send any job messages during baseline run
    assert mock_telegram.send_raw_message.call_count == 0
    assert mock_telegram.send_health_alert.call_count == 0


def test_subsequent_run_sends_individual_alerts_when_few(sample_jobs):
    """
    On subsequent run with <= 5 matches, send individual alerts.
    """
    mock_collector = MagicMock()
    mock_collector.fetch.return_value = {}
    mock_collector.normalize.return_value = sample_jobs

    mock_telegram = MagicMock(spec=TelegramSender)
    mock_telegram.enabled = True
    mock_telegram.format_single_job.return_value = "Formatted Job"
    mock_telegram.send_raw_message.return_value = True

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    # Mock candidate unnotified jobs
    unnotified = [
        {
            "id": 101,
            "title": "Software Engineer 1",
            "company_name": "Stripe",
            "location": "Bengaluru",
            "url": "https://stripe.com/jobs/1",
            "category": "SDE",
            "level": "fresher",
            "description": "Backend",
            "posted_at": None,
            "first_seen_at": datetime.now(timezone.utc),
        }
    ]
    mock_mappings = MagicMock()
    mock_mappings.all.return_value = unnotified
    mock_conn.execute.return_value.mappings.return_value = mock_mappings

    baseline_time = datetime(2026, 11, 1, 0, 0, 0, tzinfo=timezone.utc)

    with (
        patch("collectors.run._ensure_company", return_value=1),
        patch("collectors.run._ensure_source", return_value=1),
        patch("collectors.run._get_baseline_finished_at", return_value=baseline_time),
        patch("collectors.run._get_previous_run_job_count", return_value=3),
        patch("collectors.run.load_preferences", return_value={}),
        patch("time.sleep", return_value=None),
    ):
        run_source(
            engine=mock_engine,
            collector=mock_collector,
            telegram=mock_telegram,
            board_token="stripe",
        )

    # 1 individual alert sent
    assert mock_telegram.send_raw_message.call_count == 1
    assert mock_telegram.format_single_job.call_count == 1


def test_subsequent_run_sends_batched_digest_when_many(sample_jobs):
    """
    On subsequent run with > 5 matches, send a single batched digest.
    """
    mock_collector = MagicMock()
    mock_collector.fetch.return_value = {}
    mock_collector.normalize.return_value = sample_jobs

    mock_telegram = MagicMock(spec=TelegramSender)
    mock_telegram.enabled = True
    mock_telegram.format_digest.return_value = "Batched Digest Message"
    mock_telegram.send_raw_message.return_value = True

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    # 7 matching jobs (> 5)
    unnotified = [
        {
            "id": 200 + i,
            "title": f"Software Engineer {i}",
            "company_name": "Stripe",
            "location": "Bengaluru",
            "url": f"https://stripe.com/jobs/{i}",
            "category": "SDE",
            "level": "fresher",
            "description": "Backend",
            "posted_at": None,
            "first_seen_at": datetime.now(timezone.utc),
        }
        for i in range(1, 8)
    ]
    mock_mappings = MagicMock()
    mock_mappings.all.return_value = unnotified
    mock_conn.execute.return_value.mappings.return_value = mock_mappings

    baseline_time = datetime(2026, 11, 1, 0, 0, 0, tzinfo=timezone.utc)

    with (
        patch("collectors.run._ensure_company", return_value=1),
        patch("collectors.run._ensure_source", return_value=1),
        patch("collectors.run._get_baseline_finished_at", return_value=baseline_time),
        patch("collectors.run._get_previous_run_job_count", return_value=10),
        patch("collectors.run.load_preferences", return_value={}),
    ):
        run_source(
            engine=mock_engine,
            collector=mock_collector,
            telegram=mock_telegram,
            board_token="stripe",
        )

    # Format digest called, single send_raw_message called
    assert mock_telegram.format_digest.call_count == 1
    assert mock_telegram.send_raw_message.call_count == 1


def test_health_alert_on_fetch_failure():
    """When fetch fails, record failure and dispatch health alert."""
    mock_collector = MagicMock()
    mock_collector.fetch.side_effect = RuntimeError("Greenhouse API 500 Internal Error")

    mock_telegram = MagicMock(spec=TelegramSender)
    mock_telegram.enabled = True

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    with (
        patch("collectors.run._ensure_company", return_value=1),
        patch("collectors.run._ensure_source", return_value=1),
        patch("collectors.run._get_baseline_finished_at", return_value=None),
        patch("collectors.run._get_previous_run_job_count", return_value=None),
        patch("collectors.run.load_preferences", return_value={}),
    ):
        run_source(
            engine=mock_engine,
            collector=mock_collector,
            telegram=mock_telegram,
            board_token="stripe",
        )

    assert mock_telegram.send_health_alert.call_count == 1
    args = mock_telegram.send_health_alert.call_args[0]
    assert args[0] == "greenhouse:stripe"
    assert args[1] == "failure"
    assert "Greenhouse API 500" in args[2]


def test_health_alert_on_zero_jobs():
    """When source returns 0 jobs, dispatch health warning."""
    mock_collector = MagicMock()
    mock_collector.fetch.return_value = {}
    mock_collector.normalize.return_value = []

    mock_telegram = MagicMock(spec=TelegramSender)
    mock_telegram.enabled = True

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    with (
        patch("collectors.run._ensure_company", return_value=1),
        patch("collectors.run._ensure_source", return_value=1),
        patch("collectors.run._get_baseline_finished_at", return_value=None),
        patch("collectors.run._get_previous_run_job_count", return_value=None),
        patch("collectors.run.load_preferences", return_value={}),
    ):
        run_source(
            engine=mock_engine,
            collector=mock_collector,
            telegram=mock_telegram,
            board_token="stripe",
        )

    assert mock_telegram.send_health_alert.call_count == 1
    args = mock_telegram.send_health_alert.call_args[0]
    assert args[0] == "greenhouse:stripe"
    assert args[1] == "zero_jobs"


def test_health_alert_on_significant_drop():
    """When source returns >= 50% fewer jobs than previous run, dispatch drop alert."""
    # 2 jobs vs 20 previously (90% drop)
    jobs = [
        Job(
            external_id=f"stripe-{i}",
            title=f"SWE {i}",
            company_name="Stripe",
            source_slug="greenhouse:stripe",
            url=f"https://stripe.com/{i}",
            location="Remote",
            department="Eng",
            description="",
            category="SDE",
            level="fresher",
            posted_at=None,
            posted_at_source="none",
        )
        for i in range(2)
    ]

    mock_collector = MagicMock()
    mock_collector.fetch.return_value = {}
    mock_collector.normalize.return_value = jobs

    mock_telegram = MagicMock(spec=TelegramSender)
    mock_telegram.enabled = True

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn

    with (
        patch("collectors.run._ensure_company", return_value=1),
        patch("collectors.run._ensure_source", return_value=1),
        patch("collectors.run._get_baseline_finished_at", return_value=datetime.now(timezone.utc)),
        patch("collectors.run._get_previous_run_job_count", return_value=20),
        patch("collectors.run.load_preferences", return_value={}),
    ):
        run_source(
            engine=mock_engine,
            collector=mock_collector,
            telegram=mock_telegram,
            board_token="stripe",
        )

    assert mock_telegram.send_health_alert.call_count == 1
    args = mock_telegram.send_health_alert.call_args[0]
    assert args[0] == "greenhouse:stripe"
    assert args[1] == "drop"
    assert "90% decrease" in args[2]


def test_manual_source_is_skipped_without_failure_or_alerts():
    """Manual sources must be skipped without executing collection or alerts."""
    mock_engine = MagicMock()
    mock_telegram = MagicMock(spec=TelegramSender)
    mock_telegram.enabled = True

    run_source(
        engine=mock_engine,
        collector=None,
        telegram=mock_telegram,
        board_token="ibm",
        source_slug="manual:ibm",
        source_type="manual",
        enabled=False,
    )

    # Engine connection should not write source_runs or failure
    assert mock_engine.begin.return_value.__enter__.return_value.execute.call_count == 0
    # No health alerts should be dispatched
    assert mock_telegram.send_health_alert.call_count == 0
    assert mock_telegram.send_raw_message.call_count == 0
