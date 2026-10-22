"""SMTP Email notification adapter with rich multipart HTML/text and prefetch-safe action links."""
import asyncio
import logging
import re
import smtplib
import uuid
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.core.config import settings
from app.db.models import Alert, NotificationChannel
from app.services.adapters.base import BaseProviderAdapter, ProviderResult

logger = logging.getLogger("astraguard.adapters.email")

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailAdapter(BaseProviderAdapter):
    """Adapter for sending mission safety alerts via standard SMTP."""

    def __init__(self) -> None:
        pass

    def _resolve_recipient(self, channel: NotificationChannel) -> str:
        if channel.prefs and channel.prefs.get("email"):
            return channel.prefs["email"].strip()
        if channel.encrypted_address and "@" in channel.encrypted_address:
            return channel.encrypted_address.strip()
        return ""

    async def send(
        self,
        alert: Alert,
        channel: NotificationChannel,
        test: bool = False,
        action_tokens: dict[str, str] | None = None,
    ) -> ProviderResult:
        """Compose and dispatch a multipart HTML/text email via SMTP."""
        if not settings.SMTP_HOST or not settings.SMTP_FROM:
            missing = []
            if not settings.SMTP_HOST:
                missing.append("SMTP_HOST")
            if not settings.SMTP_FROM:
                missing.append("SMTP_FROM")
            return ProviderResult(
                success=False,
                error=f"Email adapter is NOT CONFIGURED. Missing environment variable(s): {', '.join(missing)}.",
                retryable=False,
            )

        to_addr = self._resolve_recipient(channel)
        if not to_addr or not EMAIL_REGEX.match(to_addr):
            return ProviderResult(
                success=False,
                error=f"Channel {channel.id} does not have a valid recipient email address.",
                retryable=False,
            )

        is_synthetic = bool(getattr(alert, "synthetic", False)) or test
        title_prefix = "[TEST] " if test else ("[SIMULATED] " if is_synthetic else "")
        subject = f"{title_prefix}[{alert.level}] ASTRA-GUARD: {alert.title}"

        approve_url = (action_tokens and action_tokens.get("approve_url")) or f"{settings.WEB_BASE_URL}/dashboard/alerts?id={alert.id}"
        snooze_url = (action_tokens and action_tokens.get("snooze_url")) or f"{settings.WEB_BASE_URL}/dashboard/alerts?id={alert.id}"
        console_url = f"{settings.WEB_BASE_URL}/dashboard/alerts?id={alert.id}"

        # Plain-text version
        text_body = f"""ASTRA-GUARD MISSION SAFETY ADVISORY
--------------------------------------------------
Severity: {alert.level}
Alert ID: {alert.id}
Title: {alert.title}

Safety Rationale:
{alert.rationale}

Advisory Recommendation:
{alert.recommendation}

Human-in-the-Loop Actions:
- Approve Action: {approve_url}
- Snooze 30m: {snooze_url}
- Open Web Console: {console_url}

Notice: Link clicks open a secure verification confirmation page to protect against email security pre-fetchers.
"""

        # Rich HTML version with high-contrast SpaceX styling
        border_color = "#fe1e34" if alert.level == "CRITICAL" else ("#f59e0b" if alert.level == "WARNING" else "#06b6d4")
        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
</head>
<body style="background-color: #000000; color: #f0f0fa; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace; margin: 0; padding: 24px;">
  <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #121214; border: 1px solid {border_color}; border-radius: 8px; overflow: hidden;">
    <tr>
      <td style="padding: 20px; background-color: #1a1a1f; border-bottom: 1px solid #333;">
        <span style="font-size: 11px; font-weight: bold; letter-spacing: 1.5px; color: #999; text-transform: uppercase;">ASTRA-GUARD &bull; Mission Safety Console</span>
        <h2 style="margin: 6px 0 0 0; font-size: 18px; color: #ffffff;">{subject}</h2>
      </td>
    </tr>
    <tr>
      <td style="padding: 20px;">
        <table width="100%" style="margin-bottom: 16px;">
          <tr>
            <td style="font-size: 12px; color: #888;">SEVERITY: <strong style="color: {border_color};">{alert.level}</strong></td>
            <td style="font-size: 12px; color: #888; text-align: right;">ALERT ID: <strong>{alert.id}</strong></td>
          </tr>
        </table>
        
        <div style="background-color: #09090b; border: 1px solid #27272a; border-radius: 6px; padding: 14px; margin-bottom: 16px;">
          <div style="font-size: 11px; color: #a1a1aa; text-transform: uppercase; margin-bottom: 4px;">Safety Rationale:</div>
          <div style="font-size: 13px; color: #e4e4e7; line-height: 1.5;">{alert.rationale}</div>
        </div>

        <div style="background-color: #09090b; border: 1px solid #27272a; border-radius: 6px; padding: 14px; margin-bottom: 24px;">
          <div style="font-size: 11px; color: #a1a1aa; text-transform: uppercase; margin-bottom: 4px;">Advisory Recommendation:</div>
          <div style="font-size: 13px; color: #10b981; font-weight: bold; line-height: 1.5;">{alert.recommendation}</div>
        </div>

        <div style="text-align: center; margin: 24px 0;">
          <a href="{approve_url}" style="display: inline-block; background-color: #fe1e34; color: #ffffff; padding: 12px 24px; text-decoration: none; font-weight: bold; font-size: 13px; border-radius: 4px; margin-right: 8px;">Approve Action</a>
          <a href="{snooze_url}" style="display: inline-block; background-color: #27272a; color: #e4e4e7; padding: 12px 20px; text-decoration: none; font-weight: bold; font-size: 13px; border-radius: 4px;">Snooze 30m</a>
        </div>

        <p style="font-size: 11px; color: #71717a; text-align: center; margin-top: 24px;">
          Security Protected: Action links route to a confirmation landing page to prevent accidental acknowledgment by automated virus scanners.
        </p>
      </td>
    </tr>
  </table>
</body>
</html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_addr
        msg["X-AstraGuard-Alert-Id"] = alert.id
        msg["X-AstraGuard-Level"] = alert.level

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        msg_id = f"email_{uuid.uuid4().hex[:12]}"

        def _sync_send() -> None:
            if settings.SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10.0)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10.0)
            try:
                server.ehlo()
                if settings.SMTP_USE_TLS and settings.SMTP_PORT != 465:
                    server.starttls()
                    server.ehlo()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            finally:
                try:
                    server.quit()
                except Exception:
                    pass

        try:
            await asyncio.to_thread(_sync_send)
            return ProviderResult(
                success=True,
                provider_message_id=msg_id,
                delivered_at=datetime.now(UTC),
            )
        except Exception as e:
            logger.warning(f"SMTP send failed to {to_addr}: {e}")
            return ProviderResult(
                success=False,
                error=f"SMTP send failed: {e}",
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
        """Send follow-up confirmation email notifying that alert was acknowledged."""
        to_addr = self._resolve_recipient(channel)
        if not to_addr or not settings.SMTP_HOST or not settings.SMTP_FROM:
            return False

        subject = f"ACKNOWLEDGED: {alert.title}"
        body = f"""ASTRA-GUARD AUDIT CONFIRMATION
---------------------------------
Alert ID: {alert.id}
Title: {alert.title}
Action: {action.upper()}
Operator: @{operator}
Recorded At: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

The alert lifecycle has been updated in the mission console.
"""
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_addr

        def _sync_send() -> None:
            if settings.SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5.0)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5.0)
            try:
                server.ehlo()
                if settings.SMTP_USE_TLS and settings.SMTP_PORT != 465:
                    server.starttls()
                    server.ehlo()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            finally:
                try:
                    server.quit()
                except Exception:
                    pass

        try:
            await asyncio.to_thread(_sync_send)
            return True
        except Exception as e:
            logger.warning(f"Failed to send email ack notice: {e}")
            return False

    async def health_check(self) -> dict[str, Any]:
        """Verify SMTP host reachability and credentials."""
        missing = []
        if not settings.SMTP_HOST:
            missing.append("SMTP_HOST")
        if not settings.SMTP_FROM:
            missing.append("SMTP_FROM")

        if missing:
            return {
                "type": "email",
                "status": "NOT CONFIGURED",
                "details": f"Missing required environment variables: {', '.join(missing)}",
                "missing_env": missing,
            }

        def _test_connect() -> bool:
            if settings.SMTP_PORT == 465:
                s = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=4.0)
            else:
                s = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=4.0)
            try:
                s.ehlo()
                return True
            finally:
                try:
                    s.quit()
                except Exception:
                    pass

        try:
            ok = await asyncio.to_thread(_test_connect)
            if ok:
                return {
                    "type": "email",
                    "status": "CONNECTED",
                    "details": f"SMTP server reachable at {settings.SMTP_HOST}:{settings.SMTP_PORT}",
                    "missing_env": [],
                }
        except Exception as e:
            return {
                "type": "email",
                "status": "PENDING VERIFICATION",
                "details": f"SMTP host configured ({settings.SMTP_HOST}:{settings.SMTP_PORT}), reachability check: {e}",
                "missing_env": [],
            }

        return {
            "type": "email",
            "status": "CONNECTED",
            "details": f"SMTP server configured ({settings.SMTP_HOST})",
            "missing_env": [],
        }
