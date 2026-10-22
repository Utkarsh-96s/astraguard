"""Real Telegram Bot adapter for outbound alert delivery and acknowledgment editing."""
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.logging import logger
from app.db.models import Alert, NotificationChannel
from app.services.adapters.base import BaseProviderAdapter, ProviderResult
from app.services.telegram_service import (
    build_alert_inline_keyboard,
    format_telegram_alert_html,
    telegram_service,
)


class TelegramBotAdapter(BaseProviderAdapter):
    """Adapter delivering alerts to Telegram chats with interactive inline buttons."""

    async def send(
        self,
        alert: Alert,
        channel: NotificationChannel,
        test: bool = False,
        action_tokens: dict[str, str] | None = None,
    ) -> ProviderResult:
        if not settings.TELEGRAM_BOT_TOKEN:
            return ProviderResult(
                success=False,
                error="Telegram Bot adapter is NOT CONFIGURED: TELEGRAM_BOT_TOKEN is missing.",
                retryable=False,
            )

        chat_id = channel.encrypted_address
        if not chat_id:
            return ProviderResult(
                success=False,
                error="NotificationChannel missing encrypted_address (Telegram chat_id).",
                retryable=False,
            )

        # Get snapshot metadata if available
        drivers_list: list[dict[str, Any]] = []
        score_val = 0.0
        asset_id = "SENTINEL-2A"

        snapshot = getattr(alert, "_snapshot_cache", None) or alert.__dict__.get("snapshot")
        if snapshot:
            score_val = getattr(snapshot, "score", 0.0)
            asset_id = getattr(snapshot, "asset_id", "SENTINEL-2A")
            drivers = getattr(snapshot, "drivers", None)
            if isinstance(drivers, dict):
                drivers_list = drivers.get("drivers", [])

        # Format message and inline keyboard
        message_html = format_telegram_alert_html(
            alert=alert,
            asset_id=asset_id,
            score=score_val,
            drivers=drivers_list,
            test=test or alert.synthetic,
        )
        keyboard = build_alert_inline_keyboard(alert.id)

        now = datetime.now(UTC)
        res = await telegram_service.send_message(
            chat_id=chat_id,
            text=message_html,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

        if res.get("ok"):
            msg_id = str(res.get("result", {}).get("message_id"))
            logger.info(f"Delivered Telegram alert {alert.id} to chat {chat_id} (msg_id={msg_id})")
            return ProviderResult(
                success=True,
                provider_message_id=msg_id,
                delivered_at=now,
            )

        error_code = res.get("error_code")
        description = res.get("description", "Unknown Telegram API error")

        # 403 Forbidden: bot was blocked by the user
        if error_code == 403:
            channel.status = "ERROR"
            channel.last_error = f"Bot was blocked by user (HTTP 403): {description}"
            logger.error(f"Telegram bot blocked in chat {chat_id}: {description}")
            return ProviderResult(
                success=False,
                error=channel.last_error,
                retryable=False,
            )

        # 429 Too Many Requests: rate limited
        if error_code == 429:
            retry_after = res.get("parameters", {}).get("retry_after", 5)
            logger.warning(f"Telegram rate limit hit (429): retry after {retry_after}s")
            return ProviderResult(
                success=False,
                error=f"Rate limited by Telegram API (retry_after: {retry_after}s)",
                retryable=True,
            )

        return ProviderResult(
            success=False,
            error=f"Telegram API error [{error_code}]: {description}",
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
        if not settings.TELEGRAM_BOT_TOKEN or not provider_message_id:
            return False

        chat_id = channel.encrypted_address
        action_title = action.upper()
        time_str = timestamp.strftime("%H:%M:%S UTC")

        # Fetch snapshot metadata if available
        drivers_list: list[dict[str, Any]] = []
        score_val = 0.0
        asset_id = "SENTINEL-2A"

        snapshot = getattr(alert, "_snapshot_cache", None) or alert.__dict__.get("snapshot")
        if snapshot:
            score_val = getattr(snapshot, "score", 0.0)
            asset_id = getattr(snapshot, "asset_id", "SENTINEL-2A")
            drivers = getattr(snapshot, "drivers", None)
            if isinstance(drivers, dict):
                drivers_list = drivers.get("drivers", [])

        base_html = format_telegram_alert_html(
            alert=alert,
            asset_id=asset_id,
            score=score_val,
            drivers=drivers_list,
            test=alert.synthetic,
        )

        updated_text = (
            f"{base_html}\n\n"
            f"✅ <b>{action_title}</b> by <b>@{operator}</b> at <code>{time_str}</code>\n"
            f"🔒 <i>Decision recorded in tamper-evident mission audit log.</i>"
        )

        res = await telegram_service.edit_message_text(
            chat_id=chat_id,
            message_id=provider_message_id,
            text=updated_text,
            reply_markup={"inline_keyboard": []},  # Remove interactive action buttons
            parse_mode="HTML",
        )
        return bool(res.get("ok"))

    async def health_check(self) -> dict[str, Any]:
        if not settings.TELEGRAM_BOT_TOKEN:
            return {
                "type": "telegram",
                "status": "NOT CONFIGURED",
                "details": "TELEGRAM_BOT_TOKEN is missing in environment variables.",
                "missing_env": ["TELEGRAM_BOT_TOKEN"],
            }

        try:
            res = await telegram_service.get_me()
            if res.get("ok"):
                bot_user = res.get("result", {})
                username = bot_user.get("username", "UnknownBot")
                return {
                    "type": "telegram",
                    "status": "CONNECTED",
                    "details": f"Connected to Telegram Bot API as @{username} (ID: {bot_user.get('id')})",
                    "missing_env": [],
                }
            else:
                return {
                    "type": "telegram",
                    "status": "ERROR",
                    "details": f"Telegram API error: {res.get('description', 'Unauthorized')}",
                    "missing_env": [],
                }
        except Exception as e:
            return {
                "type": "telegram",
                "status": "ERROR",
                "details": f"Failed to connect to Telegram API: {e}",
                "missing_env": [],
            }
