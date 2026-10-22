"""Fake provider adapter for CI, deterministic tests, and failure injection."""
import uuid
from datetime import UTC, datetime
from typing import Any

from app.db.models import Alert, NotificationChannel
from app.services.adapters.base import BaseProviderAdapter, ProviderResult


class FakeProviderAdapter(BaseProviderAdapter):
    """In-memory provider adapter supporting failure injection and assertion tracking."""

    def __init__(self, channel_type: str = "fake") -> None:
        self.channel_type = channel_type
        self.injected_failures_remaining: int = 0
        self.permanent_failure: bool = False
        self.sent_deliveries: list[dict[str, Any]] = []
        self.edited_messages: list[dict[str, Any]] = []
        self.configured_status: str = "CONNECTED"

    def inject_failure(self, times: int = 1) -> None:
        """Inject N temporary failures before succeeding."""
        self.injected_failures_remaining = times

    def set_permanent_failure(self, fail: bool = True) -> None:
        """Inject permanent non-retryable or retryable failure."""
        self.permanent_failure = fail

    def reset(self) -> None:
        """Reset history and failure state."""
        self.injected_failures_remaining = 0
        self.permanent_failure = False
        self.sent_deliveries.clear()
        self.edited_messages.clear()
        self.configured_status = "CONNECTED"

    async def send(
        self,
        alert: Alert,
        channel: NotificationChannel,
        test: bool = False,
        action_tokens: dict[str, str] | None = None,
    ) -> ProviderResult:
        now = datetime.now(UTC)

        if self.permanent_failure:
            return ProviderResult(
                success=False,
                error="Injected permanent provider failure: connection refused.",
                retryable=False,
            )

        if self.injected_failures_remaining > 0:
            self.injected_failures_remaining -= 1
            return ProviderResult(
                success=False,
                error="Injected temporary network glitch (503 Service Unavailable).",
                retryable=True,
            )

        msg_id = f"FAKE-MSG-{uuid.uuid4().hex[:10].upper()}"
        self.sent_deliveries.append({
            "message_id": msg_id,
            "alert_id": alert.id,
            "channel_id": channel.id,
            "channel_type": channel.type,
            "level": alert.level,
            "title": alert.title,
            "test": test,
            "action_tokens": action_tokens or {},
            "sent_at": now.isoformat(),
        })

        return ProviderResult(
            success=True,
            provider_message_id=msg_id,
            delivered_at=now,
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
        self.edited_messages.append({
            "provider_message_id": provider_message_id,
            "alert_id": alert.id,
            "channel_id": channel.id,
            "operator": operator,
            "action": action,
            "timestamp": timestamp.isoformat(),
        })
        return True

    async def health_check(self) -> dict[str, Any]:
        return {
            "type": self.channel_type,
            "status": self.configured_status,
            "details": "Fake provider adapter operational (test / simulation mode).",
            "missing_env": [],
        }
