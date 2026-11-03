"""
Telegram sender using the Telegram Bot API.
Handles individual job alerts, batched digests, and source health alerts.
Adheres to Telegram rate limits and message length constraints.
"""

from __future__ import annotations

import html
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

import httpx

logger = logging.getLogger(__name__)

# Asia/Kolkata (+05:30, no DST)
IST = timezone(timedelta(hours=5, minutes=30))
TELEGRAM_API_URL = "https://api.telegram.org"
MAX_MESSAGE_LENGTH = 4096


def format_honest_date(posted_at: datetime | None, first_seen_at: datetime) -> str:
    """Format date per PRD §4."""
    if posted_at:
        posted_ist = posted_at.astimezone(IST)
        return f"Posted {posted_ist.strftime('%d %b')}"

    first_seen_ist = first_seen_at.astimezone(IST)
    now_ist = datetime.now(timezone.utc).astimezone(IST)

    if first_seen_ist.date() == now_ist.date():
        return "Discovered today — posting date unavailable"

    return f"Discovered {first_seen_ist.strftime('%d %b')} — posting date unavailable"


class TelegramSender:
    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        self.timeout = timeout
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            logger.warning(
                "TelegramSender disabled: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured."
            )

    def send_raw_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send a raw text message to Telegram Bot API.
        Respects Telegram rate limits, handles 429 Too Many Requests, and retries.
        """
        if not self.enabled:
            logger.info("TelegramSender: dry-run (disabled). Message:\n%s", text)
            return False

        url = f"{TELEGRAM_API_URL}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        # Handle message length limit: Telegram max length is 4096
        if len(text) > MAX_MESSAGE_LENGTH:
            chunks = self._chunk_text(text, max_len=MAX_MESSAGE_LENGTH - 100)
            all_ok = True
            for chunk in chunks:
                ok = self.send_raw_message(chunk, parse_mode=parse_mode)
                if not ok:
                    all_ok = False
                time.sleep(1.0)
            return all_ok

        max_retries = 3
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload)

                    if resp.status_code == 200:
                        return True

                    if resp.status_code == 429:
                        # Telegram rate limit exceeded
                        retry_after = 2
                        try:
                            data = resp.json()
                            retry_after = data.get("parameters", {}).get("retry_after", 2)
                        except Exception:
                            pass
                        logger.warning(
                            "Telegram rate limited (429). Sleeping %s seconds...",
                            retry_after,
                        )
                        time.sleep(retry_after)
                        continue

                    logger.error(
                        "Telegram API error %d: %s",
                        resp.status_code,
                        resp.text,
                    )
                    return False
            except httpx.RequestError as exc:
                logger.error("HTTP error sending Telegram message: %s", exc)
                time.sleep(1.0)

        return False

    def _chunk_text(self, text: str, max_len: int = 4000) -> list[str]:
        """Split long text by newlines so lines stay intact."""
        lines = text.split("\n")
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        for line in lines:
            line_len = len(line) + 1
            if current_len + line_len > max_len and current:
                chunks.append("\n".join(current))
                current = [line]
                current_len = line_len
            else:
                current.append(line)
                current_len += line_len

        if current:
            chunks.append("\n".join(current))

        return chunks

    def format_single_job(self, job: Mapping[str, Any]) -> str:
        """Format an alert for a single job listing."""
        title = html.escape(str(job.get("title", "")))
        company = html.escape(str(job.get("company_name", "")))
        url = job.get("url", "")
        location = html.escape(str(job.get("location") or "Not specified"))
        category = html.escape(str(job.get("category") or "Other Tech"))
        level = html.escape(str(job.get("level") or "unknown"))

        posted_at = job.get("posted_at")
        first_seen_at = job.get("first_seen_at")
        if isinstance(first_seen_at, str):
            first_seen_at = datetime.fromisoformat(first_seen_at)
        if isinstance(posted_at, str):
            posted_at = datetime.fromisoformat(posted_at)
        if not first_seen_at:
            first_seen_at = datetime.now(timezone.utc)

        date_str = html.escape(format_honest_date(posted_at, first_seen_at))

        return (
            f"🎯 <b>New Matching Job</b>\n\n"
            f'<b><a href="{url}">{title}</a></b>\n'
            f"🏢 <b>Company:</b> {company}\n"
            f"📍 <b>Location:</b> {location}\n"
            f"🏷 <b>Category:</b> {category} | <b>Level:</b> {level}\n"
            f"📅 <i>{date_str}</i>\n\n"
            f'🔗 <a href="{url}">Apply / View Details</a>'
        )

    def format_digest(self, jobs: list[Mapping[str, Any]]) -> str:
        """Format a batched digest when > 5 matching jobs arrive."""
        lines = [f"🎯 <b>JobRadar Digest: {len(jobs)} New Matching Jobs Found</b>\n"]
        for idx, job in enumerate(jobs, 1):
            title = html.escape(str(job.get("title", "")))
            company = html.escape(str(job.get("company_name", "")))
            url = job.get("url", "")
            location = html.escape(str(job.get("location") or "Not specified"))
            category = html.escape(str(job.get("category") or "Other Tech"))
            level = html.escape(str(job.get("level") or "unknown"))

            lines.append(
                f'{idx}. <b><a href="{url}">{title}</a></b> @ <b>{company}</b>\n'
                f"   📍 {location} | 🏷 {category} ({level})\n"
            )

        lines.append("<i>Visit dashboard to view and track all listings.</i>")
        return "\n".join(lines)

    def send_health_alert(
        self,
        source_slug: str,
        alert_type: str,
        details: str,
    ) -> bool:
        """
        Send a source health alert.
        alert_type: "failure" | "zero_jobs" | "drop"
        """
        safe_slug = html.escape(source_slug)
        safe_details = html.escape(details)

        if alert_type == "failure":
            text = (
                f"🚨 <b>Source Run Failed</b>\n\n"
                f"<b>Source:</b> <code>{safe_slug}</code>\n"
                f"<b>Error:</b>\n<pre>{safe_details}</pre>"
            )
        elif alert_type == "zero_jobs":
            text = (
                f"⚠️ <b>Source Health Warning: 0 Jobs</b>\n\n"
                f"<b>Source:</b> <code>{safe_slug}</code> returned 0 jobs.\n"
                f"<i>Verify if the career page layout or API has changed.</i>"
            )
        elif alert_type == "drop":
            text = (
                f"⚠️ <b>Source Health Warning: Job Count Drop</b>\n\n"
                f"<b>Source:</b> <code>{safe_slug}</code>\n"
                f"<b>Notice:</b> {safe_details}\n"
                f"<i>Investigate if jobs are missing or filtered unexpectedly.</i>"
            )
        else:
            text = (
                f"⚠️ <b>Source Alert</b>\n\n<b>Source:</b> <code>{safe_slug}</code>\n{safe_details}"
            )

        return self.send_raw_message(text)
