"""Outbound alert notification dispatcher (Webhook and SMTP)."""
from typing import Any

import httpx

from app.core.logging import logger
from app.db.models import Alert


class NotificationDispatcher:
    """Dispatches alerts to external channels (webhook and email notifications)."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url

    async def notify_alert(self, alert: Alert) -> bool:
        """Dispatch outbound alert notification to webhook or external channel."""
        logger.info(f"Dispatching alert notification: id={alert.id}, level={alert.level}, title='{alert.title}'")

        if not self.webhook_url:
            logger.debug("No external webhook URL configured; alert logged to operational audit trail.")
            return True

        payload: dict[str, Any] = {
            "source": "ASTRA-GUARD Space Mission Safety",
            "alert_id": alert.id,
            "level": alert.level,
            "title": alert.title,
            "rationale": alert.rationale,
            "recommendation": alert.recommendation,
            "created_at": alert.created_at.isoformat(),
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(self.webhook_url, json=payload)
                return bool(res.is_success)
        except Exception as e:
            logger.warning(f"Failed to post alert to webhook {self.webhook_url}: {e}")
            return False


notifier = NotificationDispatcher()
