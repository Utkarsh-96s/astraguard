"""Web Push (PWA) notification adapter supporting VAPID and Service Worker actions."""
import asyncio
import base64
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid

from app.core.config import settings
from app.db.models import Alert, NotificationChannel
from app.services.adapters.base import BaseProviderAdapter, ProviderResult

logger = logging.getLogger("astraguard.adapters.webpush")

try:
    from pywebpush import WebPushException, webpush
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False
    webpush = None
    WebPushException = Exception


def generate_vapid_keypair() -> tuple[str, str]:
    """Generate a new P-256 EC VAPID keypair.
    
    Returns:
        tuple[str, str]: (public_key_b64url, private_pem_str)
    """
    v = Vapid()
    v.generate_keys()
    raw_pub = v.public_key.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    pub_b64url = base64.urlsafe_b64encode(raw_pub).decode("utf-8").rstrip("=")
    priv_pem = v.private_pem().decode("utf-8")
    return pub_b64url, priv_pem


class WebPushAdapter(BaseProviderAdapter):
    """Adapter for Web Push notifications to desktop and mobile PWA browsers."""

    def __init__(self) -> None:
        pass

    async def send(
        self,
        alert: Alert,
        channel: NotificationChannel,
        test: bool = False,
        action_tokens: dict[str, str] | None = None,
    ) -> ProviderResult:
        """Send a Web Push notification to an operator's subscribed browser/device."""
        if not WEBPUSH_AVAILABLE:
            return ProviderResult(
                success=False,
                error="pywebpush package is not installed on the system.",
                retryable=False,
            )

        if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
            return ProviderResult(
                success=False,
                error="Web Push is NOT CONFIGURED: missing VAPID_PUBLIC_KEY or VAPID_PRIVATE_KEY.",
                retryable=False,
            )

        # Extract subscription info from channel prefs or encrypted_address
        sub_info = channel.prefs.get("subscription") or channel.prefs
        if not sub_info.get("endpoint") or not sub_info.get("keys"):
            try:
                sub_info = json.loads(channel.encrypted_address)
            except Exception:
                pass

        if not sub_info or not sub_info.get("endpoint") or not sub_info.get("keys"):
            return ProviderResult(
                success=False,
                error=f"Channel {channel.id} does not contain valid push subscription endpoint and keys.",
                retryable=False,
            )

        is_synthetic = bool(getattr(alert, "synthetic", False)) or test
        title_prefix = "[TEST] " if test else ("[SIMULATED] " if is_synthetic else "")
        title = f"{title_prefix}{alert.level}: {alert.title}"

        body = f"[{alert.level}] {alert.recommendation}\nRationale: {alert.rationale}"
        if len(body) > 300:
            body = body[:297] + "..."

        approve_url = action_tokens.get("approve_url", "") if action_tokens else ""
        snooze_url = action_tokens.get("snooze_url", "") if action_tokens else ""

        payload = {
            "title": title,
            "body": body,
            "icon": "/icons/icon-192x192.png",
            "badge": "/icons/badge-72x72.png",
            "tag": f"alert-{alert.id}",
            "data": {
                "alert_id": alert.id,
                "level": alert.level,
                "url": f"{settings.WEB_BASE_URL}/dashboard/alerts?id={alert.id}",
                "actions": [
                    {"action": "approve", "title": "Approve", "url": approve_url},
                    {"action": "snooze", "title": "Snooze 30m", "url": snooze_url},
                ],
            },
            "actions": [
                {"action": "approve", "title": "Approve"},
                {"action": "snooze", "title": "Snooze 30m"},
            ],
        }

        try:
            await asyncio.to_thread(
                webpush,
                subscription_info=sub_info,
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_ADMIN_EMAIL},
                ttl=86400,
            )
            msg_id = f"wp_{uuid.uuid4().hex[:12]}"
            return ProviderResult(
                success=True,
                provider_message_id=msg_id,
                delivered_at=datetime.now(UTC),
            )
        except WebPushException as ex:
            status_code = getattr(getattr(ex, "response", None), "status_code", None)
            if status_code in (404, 410):
                channel.status = "ERROR"
                channel.last_error = f"Push subscription expired/unregistered (HTTP {status_code})."
                return ProviderResult(
                    success=False,
                    error=f"Push subscription is no longer active (HTTP {status_code}).",
                    retryable=False,
                )
            retryable = bool(status_code and status_code >= 500)
            return ProviderResult(
                success=False,
                error=f"Web Push delivery failed: {ex}",
                retryable=retryable,
            )
        except Exception as e:
            return ProviderResult(
                success=False,
                error=f"Web Push unexpected error: {str(e)}",
                retryable=False,
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
        """Update delivered notification to show acknowledgment and dismiss action buttons."""
        if not WEBPUSH_AVAILABLE or not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
            return False

        sub_info = channel.prefs.get("subscription") or channel.prefs
        if not sub_info.get("endpoint"):
            return False

        payload = {
            "title": f"ACKNOWLEDGED: {alert.title}",
            "body": f"Action '{action.upper()}' recorded by @{operator} at {timestamp.strftime('%H:%M:%S UTC')}.",
            "icon": "/icons/icon-192x192.png",
            "badge": "/icons/badge-72x72.png",
            "tag": f"alert-{alert.id}",  # Replaces existing notification with same tag
            "data": {
                "alert_id": alert.id,
                "url": f"{settings.WEB_BASE_URL}/dashboard/alerts?id={alert.id}",
                "actions": [],
            },
            "actions": [],
        }

        try:
            await asyncio.to_thread(
                webpush,
                subscription_info=sub_info,
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_ADMIN_EMAIL},
                ttl=3600,
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to update webpush notification after ack: {e}")
            return False

    async def health_check(self) -> dict[str, Any]:
        """Verify VAPID keys and webpush capability."""
        missing = []
        if not settings.VAPID_PUBLIC_KEY:
            missing.append("VAPID_PUBLIC_KEY")
        if not settings.VAPID_PRIVATE_KEY:
            missing.append("VAPID_PRIVATE_KEY")

        if missing:
            return {
                "type": "webpush",
                "status": "NOT CONFIGURED",
                "details": f"Missing required environment variables: {', '.join(missing)}",
                "missing_env": missing,
            }

        return {
            "type": "webpush",
            "status": "CONNECTED",
            "details": "VAPID keypair configured. Browser push service ready.",
            "missing_env": [],
        }
