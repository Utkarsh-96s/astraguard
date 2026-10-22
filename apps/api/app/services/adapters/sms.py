"""SMS and WhatsApp adapter with E.164 phone validation, daily cost cap, and Twilio dispatch."""
import logging
import re
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import settings
from app.db.models import Alert, NotificationChannel
from app.services.adapters.base import BaseProviderAdapter, ProviderResult

logger = logging.getLogger("astraguard.adapters.sms")

# Strict E.164 international phone number format: +[country code][subscriber number], up to 15 digits
E164_REGEX = re.compile(r"^\+[1-9]\d{1,14}$")


class SmsAdapter(BaseProviderAdapter):
    """Adapter for sending urgent SMS alerts via Twilio with cost protection caps."""

    def __init__(self) -> None:
        # Per-channel daily dispatch counter: {channel_id: {"date": "YYYY-MM-DD", "count": N}}
        self._daily_counts: dict[str, dict[str, Any]] = {}

    def _resolve_recipient(self, channel: NotificationChannel) -> str:
        if channel.prefs and channel.prefs.get("phone"):
            return channel.prefs["phone"].strip()
        if channel.encrypted_address and channel.encrypted_address.startswith("+"):
            return channel.encrypted_address.strip()
        return ""

    def _check_and_increment_daily_cap(self, channel_id: str, cap: int = 20) -> tuple[bool, int]:
        """Check if channel has exceeded its daily SMS dispatch limit."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        record = self._daily_counts.get(channel_id)
        if not record or record["date"] != today:
            self._daily_counts[channel_id] = {"date": today, "count": 1}
            return True, 1

        if record["count"] >= cap:
            return False, record["count"]

        record["count"] += 1
        return True, record["count"]

    async def send(
        self,
        alert: Alert,
        channel: NotificationChannel,
        test: bool = False,
        action_tokens: dict[str, str] | None = None,
    ) -> ProviderResult:
        """Deliver short 160-char SMS alert with phone validation and rate limiting."""
        missing = []
        if not settings.TWILIO_ACCOUNT_SID:
            missing.append("TWILIO_ACCOUNT_SID")
        if not settings.TWILIO_AUTH_TOKEN:
            missing.append("TWILIO_AUTH_TOKEN")
        if not settings.TWILIO_FROM_NUMBER:
            missing.append("TWILIO_FROM_NUMBER")

        if missing:
            return ProviderResult(
                success=False,
                error=f"SMS adapter is NOT CONFIGURED. Missing environment variable(s): {', '.join(missing)}.",
                retryable=False,
            )

        to_phone = self._resolve_recipient(channel)
        if not to_phone or not E164_REGEX.match(to_phone):
            return ProviderResult(
                success=False,
                error=f"Invalid recipient phone '{to_phone}'. Must follow international E.164 format (e.g. +14155552671).",
                retryable=False,
            )

        # Enforce daily cost cap (default 20 SMS/day per channel)
        cap = int(channel.prefs.get("daily_cap", 20)) if channel.prefs else 20
        allowed, count = self._check_and_increment_daily_cap(channel.id, cap)
        if not allowed:
            return ProviderResult(
                success=False,
                error=f"Daily SMS dispatch quota reached ({count}/{cap} sent today). Throttled to prevent runaway costs.",
                retryable=False,
            )

        is_synthetic = bool(getattr(alert, "synthetic", False)) or test
        title_prefix = "[TEST] " if test else ("[SIMULATED] " if is_synthetic else "")

        # Format concise 160-character GSM message
        approve_link = (action_tokens and action_tokens.get("approve_url")) or f"{settings.WEB_BASE_URL}/alerts"
        # Truncate title cleanly
        short_title = alert.title[:30] + ("..." if len(alert.title) > 30 else "")
        short_rec = alert.recommendation[:35] + ("..." if len(alert.recommendation) > 35 else "")

        sms_body = f"{title_prefix}[{alert.level}] {short_title}. {short_rec}. Ack: {approve_link}"
        if len(sms_body) > 160:
            sms_body = sms_body[:157] + "..."

        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
        data = {
            "To": to_phone,
            "From": settings.TWILIO_FROM_NUMBER,
            "Body": sms_body,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    data=data,
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                )
                if resp.status_code >= 400:
                    retryable = resp.status_code >= 500
                    return ProviderResult(
                        success=False,
                        error=f"Twilio API error {resp.status_code}: {resp.text[:150]}",
                        retryable=retryable,
                    )

                data_json = resp.json() if resp.text.startswith("{") else {}
                sid = data_json.get("sid") or f"sms_{uuid.uuid4().hex[:12]}"

                return ProviderResult(
                    success=True,
                    provider_message_id=sid,
                    delivered_at=datetime.now(UTC),
                )
        except Exception as e:
            logger.warning(f"SMS dispatch failed to {to_phone}: {e}")
            return ProviderResult(
                success=False,
                error=f"SMS network error: {e}",
                retryable=True,
            )

    async def edit_after_ack(
        self,
        alert: Alert,
        channel: NotificationChannel,
        provider_message_id: str,
        operator: str,
        action: str,
        timestamp: datetime,
    ) -> bool:
        """SMS delivery is immutable; optionally send confirmation text if enabled."""
        return True

    async def health_check(self) -> dict[str, Any]:
        """Verify Twilio API credentials and account status."""
        missing = []
        if not settings.TWILIO_ACCOUNT_SID:
            missing.append("TWILIO_ACCOUNT_SID")
        if not settings.TWILIO_AUTH_TOKEN:
            missing.append("TWILIO_AUTH_TOKEN")
        if not settings.TWILIO_FROM_NUMBER:
            missing.append("TWILIO_FROM_NUMBER")

        if missing:
            return {
                "type": "sms",
                "status": "NOT CONFIGURED",
                "details": f"Missing required environment variables: {', '.join(missing)}",
                "missing_env": missing,
            }

        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}.json"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    url,
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                )
                if resp.status_code == 200:
                    return {
                        "type": "sms",
                        "status": "CONNECTED",
                        "details": f"Twilio account active. Origin number: {settings.TWILIO_FROM_NUMBER}",
                        "missing_env": [],
                    }
                return {
                    "type": "sms",
                    "status": "ERROR",
                    "details": f"Twilio authentication failed with HTTP {resp.status_code}.",
                    "missing_env": [],
                }
        except Exception as e:
            return {
                "type": "sms",
                "status": "PENDING VERIFICATION",
                "details": f"Twilio configured, handshake check: {e}",
                "missing_env": [],
            }
