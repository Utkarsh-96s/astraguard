"""Base provider adapter interfaces and data structures."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.db.models import Alert, NotificationChannel


@dataclass
class ProviderResult:
    """Standardized response from an external provider notification attempt."""
    success: bool
    provider_message_id: str | None = None
    error: str | None = None
    retryable: bool = True
    delivered_at: datetime | None = None


class BaseProviderAdapter(ABC):
    """Abstract interface that every notification channel adapter must implement."""

    @abstractmethod
    async def send(
        self,
        alert: Alert,
        channel: NotificationChannel,
        test: bool = False,
        action_tokens: dict[str, str] | None = None,
    ) -> ProviderResult:
        """Send notification for alert through channel."""
        pass

    @abstractmethod
    async def edit_after_ack(
        self,
        alert: Alert,
        channel: NotificationChannel,
        provider_message_id: str,
        operator: str,
        action: str,
        timestamp: datetime,
    ) -> bool:
        """Update delivered notification message after operator acknowledgment."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Perform real provider handshake/credential check. Never fake success."""
        pass
