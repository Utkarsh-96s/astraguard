"""Adapter registry for notification providers."""
from typing import Any

from app.core.config import settings
from app.db.models import Alert, NotificationChannel
from app.services.adapters.base import BaseProviderAdapter, ProviderResult
from app.services.adapters.email import EmailAdapter
from app.services.adapters.fake import FakeProviderAdapter
from app.services.adapters.ntfy import NtfyAdapter
from app.services.adapters.sms import SmsAdapter
from app.services.adapters.telegram import TelegramBotAdapter
from app.services.adapters.webhook import WebhookAdapter
from app.services.adapters.webpush import WebPushAdapter


class StubProviderAdapter(BaseProviderAdapter):
    """Stub adapter reporting honest configuration status based on environment variables."""

    def __init__(self, channel_type: str, required_env_vars: list[str]) -> None:
        self.channel_type = channel_type
        self.required_env_vars = required_env_vars

    async def send(
        self,
        alert: Alert,
        channel: NotificationChannel,
        test: bool = False,
        action_tokens: dict[str, str] | None = None,
    ) -> ProviderResult:
        missing = [var for var in self.required_env_vars if not getattr(settings, var, "")]
        if missing:
            return ProviderResult(
                success=False,
                error=f"Channel '{self.channel_type}' is NOT CONFIGURED. Missing environment variable(s): {', '.join(missing)}.",
                retryable=False,
            )
        return ProviderResult(
            success=False,
            error=f"Adapter for '{self.channel_type}' pending verification handshake.",
            retryable=False,
        )

    async def edit_after_ack(
        self,
        alert: Alert,
        channel: NotificationChannel,
        provider_message_id: str,
        operator: str,
        action: str,
        timestamp: Any,
    ) -> bool:
        return False

    async def health_check(self) -> dict[str, Any]:
        missing = [var for var in self.required_env_vars if not getattr(settings, var, "")]
        if missing:
            return {
                "type": self.channel_type,
                "status": "NOT CONFIGURED",
                "details": f"Missing required environment variables: {', '.join(missing)}",
                "missing_env": missing,
            }
        return {
            "type": self.channel_type,
            "status": "PENDING VERIFICATION",
            "details": "Credentials configured, awaiting handshake verification.",
            "missing_env": [],
        }


class AdapterRegistry:
    """Registry managing provider adapters for each channel type."""

    def __init__(self) -> None:
        self._adapters: dict[str, BaseProviderAdapter] = {
            "fake": FakeProviderAdapter("fake"),
            "telegram": TelegramBotAdapter(),
            "webpush": WebPushAdapter(),
            "ntfy": NtfyAdapter(),
            "email": EmailAdapter(),
            "webhook": WebhookAdapter(),
            "sms": SmsAdapter(),
        }

    def register(self, channel_type: str, adapter: BaseProviderAdapter) -> None:
        """Register or override an adapter for a given channel type."""
        self._adapters[channel_type.lower()] = adapter

    def get(self, channel_type: str) -> BaseProviderAdapter:
        """Get the adapter for a channel type, defaulting to fake if unknown."""
        return self._adapters.get(channel_type.lower(), self._adapters["fake"])

    async def check_all_health(self) -> list[dict[str, Any]]:
        """Run health check across all registered provider adapters."""
        results = []
        for _channel_type, adapter in self._adapters.items():
            res = await adapter.health_check()
            results.append(res)
        return results


adapter_registry = AdapterRegistry()
