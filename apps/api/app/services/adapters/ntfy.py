"""ntfy.sh push alert adapter with priority tags, action buttons, and single-use action tokens."""
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import settings
from app.db.models import Alert, NotificationChannel
from app.services.adapters.base import BaseProviderAdapter, ProviderResult

logger = logging.getLogger("astraguard.adapters.ntfy")


class NtfyAdapter(BaseProviderAdapter):
    """Adapter for ntfy.sh instant mobile push notifications with interactive action buttons."""

    def __init__(self) -> None:
        pass

    def _resolve_topic(self, channel: NotificationChannel) -> str:
        """Resolve topic from channel prefs, address, or settings."""
        if channel.prefs and channel.prefs.get("topic"):
            return channel.prefs["topic"]
        if channel.encrypted_address and not channel.encrypted_address.startswith("http"):
            return channel.encrypted_address
        return getattr(settings, "NTFY_TOPIC", "astraguard_alerts") or "astraguard_alerts"

    def _resolve_base_url(self, channel: NotificationChannel) -> str:
        if channel.prefs and channel.prefs.get("server_url"):
            return channel.prefs["server_url"].rstrip("/")
        if channel.encrypted_address and channel.encrypted_address.startswith("http"):
            # If full URL like https://ntfy.sh/topic, split
            parts = channel.encrypted_address.rstrip("/").rsplit("/", 1)
            return parts[0]
        return (settings.NTFY_BASE_URL or "https://ntfy.sh").rstrip("/")

    async def send(
        self,
        alert: Alert,
        channel: NotificationChannel,
        test: bool = False,
        action_tokens: dict[str, str] | None = None,
    ) -> ProviderResult:
        """Publish push notification to the configured ntfy topic."""
        base_url = self._resolve_base_url(channel)
        topic = self._resolve_topic(channel)

        if not base_url or not topic:
            return ProviderResult(
                success=False,
                error="ntfy is NOT CONFIGURED: missing server URL or topic.",
                retryable=False,
            )

        is_synthetic = bool(getattr(alert, "synthetic", False)) or test
        title_prefix = "[TEST] " if test else ("[SIMULATED] " if is_synthetic else "")
        title = f"{title_prefix}{alert.level}: {alert.title}"

        # Map severity to ntfy priority (1 to 5)
        level_upper = (alert.level or "WATCH").upper()
        if level_upper == "CRITICAL":
            priority = 5
            tags = ["satellite", "warning", "rotating_light"]
        elif level_upper == "WARNING":
            priority = 4
            tags = ["satellite", "warning"]
        else:
            priority = 3
            tags = ["satellite", "information_source"]

        message = f"Advisory Recommendation: {alert.recommendation}\nRationale: {alert.rationale}"
        if len(message) > 400:
            message = message[:397] + "..."

        actions: list[dict[str, Any]] = [
            {
                "action": "view",
                "label": "Open Console",
                "url": f"{settings.WEB_BASE_URL}/dashboard/alerts?id={alert.id}",
                "clear": True,
            }
        ]

        if action_tokens and action_tokens.get("approve_url"):
            actions.append({
                "action": "http",
                "label": "Approve",
                "url": action_tokens["approve_url"],
                "method": "POST",
                "clear": True,
            })

        if action_tokens and action_tokens.get("snooze_url"):
            actions.append({
                "action": "http",
                "label": "Snooze 30m",
                "url": action_tokens["snooze_url"],
                "method": "POST",
                "clear": True,
            })

        payload = {
            "topic": topic,
            "title": title,
            "message": message,
            "priority": priority,
            "tags": tags,
            "click": f"{settings.WEB_BASE_URL}/dashboard/alerts?id={alert.id}",
            "actions": actions,
        }

        headers: dict[str, str] = {"Content-Type": "application/json"}
        auth_token = channel.prefs.get("auth_token") or getattr(settings, "NTFY_AUTH_TOKEN", "")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        target_url = f"{base_url}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(target_url, json=payload, headers=headers)
                if resp.status_code >= 400:
                    retryable = resp.status_code >= 500
                    return ProviderResult(
                        success=False,
                        error=f"ntfy server returned HTTP {resp.status_code}: {resp.text[:200]}",
                        retryable=retryable,
                    )

                data = resp.json() if resp.text.startswith("{") else {}
                provider_msg_id = data.get("id") or f"ntfy_{uuid.uuid4().hex[:12]}"

                return ProviderResult(
                    success=True,
                    provider_message_id=provider_msg_id,
                    delivered_at=datetime.now(UTC),
                )
        except Exception as e:
            return ProviderResult(
                success=False,
                error=f"Failed to publish to ntfy: {e}",
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
        """Publish acknowledgment notice on ntfy channel."""
        base_url = self._resolve_base_url(channel)
        topic = self._resolve_topic(channel)
        if not base_url or not topic:
            return False

        payload = {
            "topic": topic,
            "title": f"ACKNOWLEDGED: {alert.title}",
            "message": f"Action '{action.upper()}' recorded by @{operator} at {timestamp.strftime('%H:%M:%S UTC')}.",
            "priority": 2,
            "tags": ["white_check_mark", "satellite"],
            "click": f"{settings.WEB_BASE_URL}/dashboard/alerts?id={alert.id}",
        }

        headers = {"Content-Type": "application/json"}
        auth_token = channel.prefs.get("auth_token") or getattr(settings, "NTFY_AUTH_TOKEN", "")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(base_url, json=payload, headers=headers)
                return True
        except Exception as e:
            logger.warning(f"Failed to post ntfy ack notice: {e}")
            return False

    async def health_check(self) -> dict[str, Any]:
        """Verify reachability of ntfy endpoint."""
        base_url = (settings.NTFY_BASE_URL or "https://ntfy.sh").rstrip("/")
        topic = getattr(settings, "NTFY_TOPIC", "astraguard_alerts")

        if not base_url or not topic:
            return {
                "type": "ntfy",
                "status": "NOT CONFIGURED",
                "details": "Missing NTFY_BASE_URL or NTFY_TOPIC.",
                "missing_env": ["NTFY_BASE_URL", "NTFY_TOPIC"],
            }

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                # Lightweight check to ntfy server
                resp = await client.get(f"{base_url}")
                if resp.status_code < 500:
                    return {
                        "type": "ntfy",
                        "status": "CONNECTED",
                        "details": f"ntfy server reachable at {base_url} (default topic: {topic})",
                        "missing_env": [],
                    }
        except Exception as e:
            return {
                "type": "ntfy",
                "status": "PENDING VERIFICATION",
                "details": f"ntfy configured at {base_url} (handshake pending or offline: {e})",
                "missing_env": [],
            }

        return {
            "type": "ntfy",
            "status": "CONNECTED",
            "details": f"ntfy configured at {base_url}",
            "missing_env": [],
        }
