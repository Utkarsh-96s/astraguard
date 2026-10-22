"""Generic Webhook adapter with HMAC-SHA256 signatures and strict SSRF protection."""
import hashlib
import hmac
import ipaddress
import json
import logging
import socket
import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.db.models import Alert, NotificationChannel
from app.services.adapters.base import BaseProviderAdapter, ProviderResult

logger = logging.getLogger("astraguard.adapters.webhook")


def is_safe_webhook_url(url: str, allow_local: bool = False) -> tuple[bool, str]:
    """Validate webhook URL against SSRF attacks (private IPs, loopback, cloud metadata).
    
    Args:
        url: The candidate webhook URL to validate.
        allow_local: If True (e.g. in test/dev), permits loopback and private networks.
        
    Returns:
        tuple[bool, str]: (is_safe, error_reason)
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL: {e}"

    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported scheme '{parsed.scheme}': only HTTP and HTTPS are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL is missing a valid hostname."

    # In development or testing with ALLOW_LOCAL_WEBHOOKS=True, skip strict blocking
    if allow_local or settings.ALLOW_LOCAL_WEBHOOKS:
        return True, ""

    # Check for direct local hostnames
    if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
        return False, f"Destination hostname '{hostname}' is a reserved local or metadata target."

    try:
        # Resolve all IPv4 and IPv6 addresses for the host
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        return False, f"Failed to resolve hostname '{hostname}': {e}"

    for item in addr_info:
        ip_str = item[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if ip.is_loopback:
            return False, f"Target IP {ip_str} is a loopback address (SSRF blocked)."
        if ip.is_private:
            return False, f"Target IP {ip_str} is a private RFC1918 address (SSRF blocked)."
        if ip.is_link_local:
            return False, f"Target IP {ip_str} is a link-local / cloud metadata address (SSRF blocked)."
        if ip.is_multicast or ip.is_reserved:
            return False, f"Target IP {ip_str} is a reserved/multicast address (SSRF blocked)."

    return True, ""


class WebhookAdapter(BaseProviderAdapter):
    """Adapter for delivering signed JSON webhooks with HMAC-SHA256 authentication."""

    def __init__(self) -> None:
        pass

    async def send(
        self,
        alert: Alert,
        channel: NotificationChannel,
        test: bool = False,
        action_tokens: dict[str, str] | None = None,
    ) -> ProviderResult:
        """Sign and dispatch JSON webhook event to destination URL."""
        target_url = channel.encrypted_address or (channel.prefs and channel.prefs.get("url", ""))
        if not target_url:
            return ProviderResult(
                success=False,
                error=f"Channel {channel.id} is missing a destination webhook URL.",
                retryable=False,
            )

        # SSRF Security Guard
        safe, reason = is_safe_webhook_url(target_url)
        if not safe:
            return ProviderResult(
                success=False,
                error=f"SSRF validation blocked webhook to '{target_url}': {reason}",
                retryable=False,
            )

        secret = (channel.prefs and channel.prefs.get("secret")) or settings.SECRET_KEY
        timestamp = datetime.now(UTC).isoformat()
        delivery_id = f"wh_{uuid.uuid4().hex[:12]}"

        is_synthetic = bool(getattr(alert, "synthetic", False)) or test
        payload = {
            "event": "alert.triggered",
            "delivery_id": delivery_id,
            "timestamp": timestamp,
            "alert": {
                "id": alert.id,
                "level": alert.level,
                "title": alert.title,
                "rationale": alert.rationale,
                "recommendation": alert.recommendation,
                "status": alert.status,
                "synthetic": is_synthetic,
                "created_at": alert.created_at.isoformat() if alert.created_at else timestamp,
            },
            "actions": {
                "approve_url": (action_tokens and action_tokens.get("approve_url")) or "",
                "snooze_url": (action_tokens and action_tokens.get("snooze_url")) or "",
                "console_url": f"{settings.WEB_BASE_URL}/dashboard/alerts?id={alert.id}",
            },
        }

        body_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ASTRA-GUARD-Webhook/1.0",
            "X-AstraGuard-Delivery": delivery_id,
            "X-AstraGuard-Event": "alert.triggered",
            "X-AstraGuard-Timestamp": timestamp,
            "X-AstraGuard-Signature": f"sha256={signature}",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(target_url, content=body_bytes, headers=headers)
                if resp.status_code >= 400:
                    retryable = resp.status_code >= 500
                    return ProviderResult(
                        success=False,
                        error=f"Webhook destination returned HTTP {resp.status_code}: {resp.text[:150]}",
                        retryable=retryable,
                    )

                return ProviderResult(
                    success=True,
                    provider_message_id=delivery_id,
                    delivered_at=datetime.now(UTC),
                )
        except Exception as e:
            logger.warning(f"Webhook dispatch failed to {target_url}: {e}")
            return ProviderResult(
                success=False,
                error=f"Webhook connection error: {e}",
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
        """Send follow-up webhook event notifying that alert was acknowledged."""
        target_url = channel.encrypted_address or (channel.prefs and channel.prefs.get("url", ""))
        if not target_url:
            return False

        safe, _ = is_safe_webhook_url(target_url)
        if not safe:
            return False

        secret = (channel.prefs and channel.prefs.get("secret")) or settings.SECRET_KEY
        delivery_id = f"wh_ack_{uuid.uuid4().hex[:12]}"
        iso_time = timestamp.isoformat()

        payload = {
            "event": "alert.acknowledged",
            "delivery_id": delivery_id,
            "timestamp": iso_time,
            "alert_id": alert.id,
            "operator": operator,
            "action": action.upper(),
        }

        body_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ASTRA-GUARD-Webhook/1.0",
            "X-AstraGuard-Delivery": delivery_id,
            "X-AstraGuard-Event": "alert.acknowledged",
            "X-AstraGuard-Timestamp": iso_time,
            "X-AstraGuard-Signature": f"sha256={signature}",
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(target_url, content=body_bytes, headers=headers)
                return True
        except Exception as e:
            logger.warning(f"Failed to deliver ack webhook: {e}")
            return False

    async def health_check(self) -> dict[str, Any]:
        """Webhook adapter operational health."""
        return {
            "type": "webhook",
            "status": "CONNECTED",
            "details": "Webhook signing and SSRF security guard operational.",
            "missing_env": [],
        }
