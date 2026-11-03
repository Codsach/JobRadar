"""
Tests for Telegram sender (formatting, rate limits, chunking, and health alerts).
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from collectors.telegram import TelegramSender, format_honest_date


def test_format_honest_date_with_posted_at():
    posted = datetime(2026, 11, 2, 10, 0, 0, tzinfo=timezone.utc)
    first_seen = datetime(2026, 11, 3, 10, 0, 0, tzinfo=timezone.utc)
    res = format_honest_date(posted, first_seen)
    assert res == "Posted 02 Nov"


def test_format_honest_date_without_posted_at_discovered_today():
    now_utc = datetime.now(timezone.utc)
    res = format_honest_date(None, now_utc)
    assert res == "Discovered today — posting date unavailable"


def test_format_honest_date_without_posted_at_discovered_past():
    past = datetime(2026, 10, 15, 10, 0, 0, tzinfo=timezone.utc)
    res = format_honest_date(None, past)
    assert "Discovered 15 Oct — posting date unavailable" in res


def test_format_single_job():
    sender = TelegramSender(bot_token="fake_token", chat_id="12345")
    job = {
        "title": "Software Engineer & Backend",
        "company_name": "Acme Corp <Tech>",
        "url": "https://example.com/job/1",
        "location": "Bengaluru, India",
        "category": "SDE",
        "level": "fresher",
        "first_seen_at": datetime(2026, 11, 3, 10, 0, 0, tzinfo=timezone.utc),
        "posted_at": None,
    }
    msg = sender.format_single_job(job)
    assert "Software Engineer &amp; Backend" in msg
    assert "Acme Corp &lt;Tech&gt;" in msg
    assert "Bengaluru, India" in msg
    assert "SDE" in msg
    assert "fresher" in msg
    assert "https://example.com/job/1" in msg


def test_format_digest():
    sender = TelegramSender(bot_token="fake_token", chat_id="12345")
    jobs = [
        {
            "title": f"Job {i}",
            "company_name": "Company X",
            "url": f"https://example.com/{i}",
            "location": "Remote",
            "category": "SDE",
            "level": "fresher",
        }
        for i in range(1, 8)
    ]
    digest = sender.format_digest(jobs)
    assert "JobRadar Digest: 7 New Matching Jobs Found" in digest
    assert "Job 1" in digest
    assert "Job 7" in digest


def test_chunking_long_messages():
    sender = TelegramSender(bot_token="fake_token", chat_id="12345")
    long_line = "A" * 100
    text = "\n".join([long_line] * 50)  # 5000+ chars
    chunks = sender._chunk_text(text, max_len=2000)
    assert len(chunks) >= 3
    for chunk in chunks:
        assert len(chunk) <= 2000


@patch("httpx.Client.post")
def test_send_raw_message_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    sender = TelegramSender(bot_token="fake_token", chat_id="12345")
    success = sender.send_raw_message("Hello Test")
    assert success is True
    assert mock_post.called


@patch("time.sleep", return_value=None)
@patch("httpx.Client.post")
def test_send_raw_message_429_retry(mock_post, mock_sleep):
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.json.return_value = {"parameters": {"retry_after": 1}}

    resp_200 = MagicMock()
    resp_200.status_code = 200

    mock_post.side_effect = [resp_429, resp_200]

    sender = TelegramSender(bot_token="fake_token", chat_id="12345")
    success = sender.send_raw_message("Hello Retry")
    assert success is True
    assert mock_post.call_count == 2
    assert mock_sleep.called


@patch("httpx.Client.post")
def test_send_health_alerts(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    sender = TelegramSender(bot_token="fake_token", chat_id="12345")

    # Failure alert
    sender.send_health_alert("greenhouse:stripe", "failure", "Connection refused")
    payload1 = mock_post.call_args_list[-1][1]["json"]["text"]
    assert "Source Run Failed" in payload1
    assert "Connection refused" in payload1

    # Zero jobs alert
    sender.send_health_alert("greenhouse:stripe", "zero_jobs", "0 jobs returned")
    payload2 = mock_post.call_args_list[-1][1]["json"]["text"]
    assert "Source Health Warning: 0 Jobs" in payload2

    # Drop alert
    sender.send_health_alert("greenhouse:stripe", "drop", "Returned 10 jobs vs 100")
    payload3 = mock_post.call_args_list[-1][1]["json"]["text"]
    assert "Job Count Drop" in payload3
