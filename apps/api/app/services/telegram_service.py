"""Real Telegram Bot Service supporting polling, webhook, linking, inline keyboards, and commands."""
import html
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.websocket import ws_manager
from app.db.models import Alert, NotificationChannel, RiskSnapshot, Subscription
from app.services.alert_service import alert_service
from app.services.tokens import verify_and_consume_linking_token


def format_telegram_alert_html(
    alert: Alert,
    asset_id: str = "SENTINEL-2A",
    score: float = 0.0,
    drivers: list[dict[str, Any]] | None = None,
    test: bool = False,
) -> str:
    """Format rich HTML alert message with zero escaping bugs."""
    prefix = "[SIMULATED] " if (test or alert.synthetic) else ""
    level_emoji = "🚨" if alert.level == "CRITICAL" else "⚠️" if alert.level == "WARNING" else "ℹ️"

    lines = [
        f"{level_emoji} <b>{prefix}{alert.level} MISSION SAFETY ALERT</b>",
        "",
        f"🛰 <b>Asset:</b> <code>{html.escape(asset_id)}</code>",
        f"📊 <b>Severity:</b> <b>{alert.level}</b> (Score: {score:.1f}/100)",
        f"📝 <b>Title:</b> {html.escape(alert.title)}",
        "",
        "🔍 <b>Diagnostic Rationale:</b>",
        f"{html.escape(alert.rationale)}",
    ]

    if drivers:
        lines.append("")
        lines.append("⚡ <b>Primary Risk Drivers:</b>")
        for d in drivers[:3]:
            mod = html.escape(str(d.get("module", "telemetry")).upper())
            name = html.escape(str(d.get("driver", "anomaly")))
            share = d.get("share_pct")
            share_str = f" ({share:.1f}%)" if share is not None else ""
            lines.append(f"• <b>{mod}:</b> <code>{name}</code>{share_str}")

    lines.extend([
        "",
        "💡 <b>Advisory Recommendation:</b>",
        f"<code>{html.escape(alert.recommendation)}</code>",
        "",
        f"⏱ <i>Issued at {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</i>",
        "🔒 <b>HITL Safety Lock:</b> Advisory only. Spacecraft maneuvers require human authorization.",
    ])

    return "\n".join(lines)


def build_alert_inline_keyboard(alert_id: str) -> dict[str, Any]:
    """Construct inline keyboard with Approve, Snooze, Dismiss, and Web Console URL button."""
    web_url = f"{settings.WEB_BASE_URL}/dashboard/alerts?id={alert_id}"
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Approve Advisory", "callback_data": f"act:approve:{alert_id}"},
                {"text": "⏱ Snooze 30m", "callback_data": f"act:snooze:{alert_id}:30"},
            ],
            [
                {"text": "❌ Dismiss", "callback_data": f"act:dismiss:{alert_id}"},
                {"text": "📊 Web Console", "url": web_url},
            ],
        ]
    }


class TelegramService:
    """Manages Telegram Bot API interactions (polling, webhook, commands, and callback queries)."""

    def __init__(self) -> None:
        self.api_base = "https://api.telegram.org"
        self._polling_task: Any = None
        self._mock_transport: Any = None  # Injected during tests

    @property
    def bot_token(self) -> str:
        return settings.TELEGRAM_BOT_TOKEN

    def _get_client(self) -> httpx.AsyncClient:
        if self._mock_transport:
            return httpx.AsyncClient(transport=self._mock_transport, base_url="https://api.telegram.org")
        return httpx.AsyncClient(timeout=10.0)

    async def get_me(self) -> dict[str, Any]:
        """Fetch bot info to verify credentials."""
        if not self.bot_token:
            return {"ok": False, "description": "TELEGRAM_BOT_TOKEN is not configured."}

        url = f"{self.api_base}/bot{self.bot_token}/getMe"
        async with self._get_client() as client:
            res = await client.get(url)
            return res.json()

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        reply_markup: dict[str, Any] | None = None,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        """Send message via Telegram Bot API."""
        if not self.bot_token:
            return {"ok": False, "description": "TELEGRAM_BOT_TOKEN missing"}

        url = f"{self.api_base}/bot{self.bot_token}/sendMessage"
        payload: dict[str, Any] = {
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with self._get_client() as client:
            res = await client.post(url, json=payload)
            return res.json()

    async def edit_message_text(
        self,
        chat_id: str | int,
        message_id: int | str,
        text: str,
        reply_markup: dict[str, Any] | None = None,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        """Edit message text and update/remove inline keyboard."""
        if not self.bot_token:
            return {"ok": False, "description": "TELEGRAM_BOT_TOKEN missing"}

        url = f"{self.api_base}/bot{self.bot_token}/editMessageText"
        payload: dict[str, Any] = {
            "chat_id": str(chat_id),
            "message_id": int(message_id),
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        async with self._get_client() as client:
            res = await client.post(url, json=payload)
            return res.json()

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
        show_alert: bool = False,
    ) -> dict[str, Any]:
        """Acknowledge Telegram callback query to clear button spinner."""
        if not self.bot_token:
            return {"ok": False}

        url = f"{self.api_base}/bot{self.bot_token}/answerCallbackQuery"
        payload: dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
            payload["show_alert"] = show_alert

        async with self._get_client() as client:
            res = await client.post(url, json=payload)
            return res.json()

    async def set_webhook(self, webhook_url: str, secret_token: str | None = None) -> dict[str, Any]:
        """Configure Telegram webhook with secret token header verification."""
        if not self.bot_token:
            return {"ok": False, "description": "TELEGRAM_BOT_TOKEN missing"}

        url = f"{self.api_base}/bot{self.bot_token}/setWebhook"
        payload: dict[str, Any] = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"],
        }
        if secret_token:
            payload["secret_token"] = secret_token

        async with self._get_client() as client:
            res = await client.post(url, json=payload)
            return res.json()

    async def process_update(self, update: dict[str, Any], db: AsyncSession) -> dict[str, Any]:
        """Process incoming Telegram update (command, text, or inline callback query)."""
        logger.info(f"Processing Telegram update ID {update.get('update_id')}")

        # 1. Handle Inline Callback Query
        if "callback_query" in update:
            return await self._handle_callback_query(update["callback_query"], db)

        # 2. Handle Message
        if "message" in update:
            return await self._handle_message(update["message"], db)

        return {"status": "ignored", "reason": "No supported payload in update"}

    async def _handle_callback_query(self, query: dict[str, Any], db: AsyncSession) -> dict[str, Any]:
        """Process callback query when user clicks inline button (Approve, Snooze, Dismiss)."""
        query_id = query["id"]
        data = query.get("data", "")
        chat = query.get("message", {}).get("chat", {})
        chat_id = chat.get("id")
        message_id = query.get("message", {}).get("message_id")
        user = query.get("from", {})
        operator_name = user.get("username") or user.get("first_name") or "TelegramOperator"

        # Format: act:approve:ALT-12345 or act:snooze:ALT-12345:30 or act:dismiss:ALT-12345
        parts = data.split(":")
        if len(parts) < 3 or parts[0] != "act":
            await self.answer_callback_query(query_id, text="Unknown button action.")
            return {"status": "error", "message": "Malformed callback data"}

        action = parts[1]
        alert_id = parts[2]
        snooze_min = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 30

        alert = await db.get(Alert, alert_id)
        if not alert:
            await self.answer_callback_query(query_id, text=f"Alert {alert_id} not found.", show_alert=True)
            return {"status": "error", "message": "Alert not found"}

        now = datetime.now(UTC)
        note = f"Executed via Telegram inline button by @{operator_name}"
        if action == "snooze":
            note = f"Snoozed for {snooze_min}m via Telegram inline button by @{operator_name}"

        # Record action in DB (this halts escalation and updates status)
        try:
            await alert_service.record_operator_action(
                db=db,
                alert_id=alert_id,
                user=operator_name,
                action=action,
                note=note,
            )
        except Exception as e:
            await self.answer_callback_query(query_id, text=f"Failed to record action: {e}", show_alert=True)
            return {"status": "error", "detail": str(e)}

        # Answer callback query to remove Telegram spinner
        action_title = "ACKNOWLEDGED" if action == "approve" else "DISMISSED" if action == "dismiss" else f"SNOOZED ({snooze_min}m)"
        await self.answer_callback_query(query_id, text=f"Alert {alert_id} {action_title}!")

        # Edit original message: append confirmation and remove buttons
        clean_text = query.get("message", {}).get("text", "") or ""
        updated_text = (
            f"{clean_text}\n\n"
            f"✅ <b>{action_title}</b> by <b>@{operator_name}</b> at <code>{now.strftime('%H:%M:%S UTC')}</code>\n"
            f"🔒 <i>HITL audit trail entry committed to mission safety log.</i>"
        )

        if chat_id and message_id:
            await self.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=updated_text,
                reply_markup={"inline_keyboard": []},  # Remove buttons
            )

        return {"status": "action_recorded", "action": action, "alert_id": alert_id}

    async def _handle_message(self, message: dict[str, Any], db: AsyncSession) -> dict[str, Any]:
        """Handle incoming text commands (/start, /status, /alerts, /ack, /stop, /help)."""
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        chat_type = chat.get("type", "private")  # private, group, supergroup
        text = (message.get("text") or "").strip()
        user = message.get("from", {})
        username = user.get("username") or user.get("first_name") or "Operator"

        if not chat_id or not text:
            return {"status": "ignored"}

        # 1. /start [code]
        if text.startswith("/start"):
            parts = text.split(maxsplit=1)
            code = parts[1].strip() if len(parts) > 1 else None

            if code:
                try:
                    token = await verify_and_consume_linking_token(db, code, channel_type="telegram")
                    # Check or create notification channel
                    stmt = select(NotificationChannel).where(
                        NotificationChannel.type == "telegram",
                        NotificationChannel.encrypted_address == str(chat_id),
                    )
                    ch = (await db.execute(stmt)).scalars().first()
                    now = datetime.now(UTC)

                    if not ch:
                        ch = NotificationChannel(
                            id=f"CHN-TG-{chat_id}",
                            user_id=token.user_id,
                            type="telegram",
                            name=f"Telegram ({chat_type.capitalize()}: {chat.get('title') or username})",
                            encrypted_address=str(chat_id),
                            status="CONNECTED",
                            verified_at=now,
                            prefs={"chat_type": chat_type, "username": username},
                            created_at=now,
                        )
                        db.add(ch)
                        # Default subscription
                        sub = Subscription(
                            id=f"SUB-TG-{chat_id}",
                            channel_id=ch.id,
                            min_level="WATCH",
                            enabled=True,
                            created_at=now,
                        )
                        db.add(sub)
                    else:
                        ch.status = "CONNECTED"
                        ch.verified_at = now
                        ch.last_error = None

                    await db.commit()

                    # Live WebSocket broadcast to update web dashboard
                    await ws_manager.broadcast_alert({
                        "event": "CHANNEL_CONNECTED",
                        "channel": {
                            "id": ch.id,
                            "type": "telegram",
                            "status": "CONNECTED",
                            "name": ch.name,
                        },
                    })

                    welcome_msg = (
                        "🚀 <b>ASTRA-GUARD Space Mission Safety Bot Connected!</b>\n\n"
                        f"Target: <code>{html.escape(ch.name)}</code>\n"
                        f"Operator: <b>@{html.escape(username)}</b>\n"
                        f"Status: <b>CONNECTED</b>\n\n"
                        "You will now receive high-priority conjunction risk, subsystem anomaly, "
                        "and disaster intelligence alerts with interactive action buttons.\n\n"
                        "Type /help for available flight operations commands."
                    )
                    await self.send_message(chat_id, welcome_msg)
                    return {"status": "linked", "chat_id": chat_id}

                except Exception as e:
                    err_msg = f"❌ <b>Linking Failed:</b> {html.escape(str(e))}\n\nPlease generate a new link code from the web console."
                    await self.send_message(chat_id, err_msg)
                    return {"status": "link_error", "detail": str(e)}

            else:
                help_msg = (
                    "👋 <b>Welcome to ASTRA-GUARD Mission Safety Bot</b>\n\n"
                    "To pair this chat with your dashboard, navigate to <b>Alerts > Notifications > Connect Telegram</b> "
                    "in the web console and tap the pairing link or scan the QR code.\n\n"
                    "Available Commands:\n"
                    "• /status — Current fused risk scores across all assets\n"
                    "• /alerts — List active mission safety alerts\n"
                    "• /ack &lt;alert_id&gt; — Acknowledge an open alert\n"
                    "• /snooze &lt;alert_id&gt; &lt;minutes&gt; — Snooze alert\n"
                    "• /mute &lt;hours&gt; — Enable temporary quiet hours\n"
                    "• /unmute — Disable quiet hours\n"
                    "• /stop — Unsubscribe from alerts\n"
                    "• /help — Show this reference"
                )
                await self.send_message(chat_id, help_msg)
                return {"status": "start_unlinked"}

        # 2. /status
        elif text == "/status":
            stmt = select(RiskSnapshot).order_by(RiskSnapshot.ts.desc()).limit(5)
            snapshots = list((await db.execute(stmt)).scalars().all())

            if not snapshots:
                await self.send_message(chat_id, "ℹ️ No risk snapshots recorded yet.")
                return {"status": "no_status"}

            msg_lines = ["🛰 <b>ASTRA-GUARD CONSTELLATION RISK STATUS</b>", ""]
            seen_assets = set()
            for s in snapshots:
                if s.asset_id in seen_assets:
                    continue
                seen_assets.add(s.asset_id)
                emoji = "🚨" if s.level == "CRITICAL" else "⚠️" if s.level == "WARNING" else "✅"
                msg_lines.append(f"{emoji} <b>{s.asset_id}</b>: {s.level} (Score: {s.score:.1f}/100)")

            msg_lines.extend(["", "<i>All telemetry within active flight safety margins.</i>"])
            await self.send_message(chat_id, "\n".join(msg_lines))
            return {"status": "status_sent"}

        # 3. /alerts
        elif text == "/alerts":
            stmt = select(Alert).where(Alert.status == "ACTIVE").order_by(Alert.created_at.desc()).limit(10)
            alerts = list((await db.execute(stmt)).scalars().all())

            if not alerts:
                await self.send_message(chat_id, "✅ <b>No Active Alerts.</b> All spacecraft systems nominal.")
                return {"status": "no_alerts"}

            lines = [f"🚨 <b>ACTIVE MISSION SAFETY ALERTS ({len(alerts)}):</b>", ""]
            for a in alerts:
                lines.append(f"• <b>[{a.level}]</b> <code>{a.id}</code>: {html.escape(a.title)}")
            lines.extend(["", "Use inline buttons or /ack &lt;id&gt; to record operator decision."])
            await self.send_message(chat_id, "\n".join(lines))
            return {"status": "alerts_sent"}

        # 4. /ack <id>
        elif text.startswith("/ack"):
            parts = text.split()
            if len(parts) < 2:
                await self.send_message(chat_id, "Usage: <code>/ack ALT-12345</code>")
                return {"status": "bad_syntax"}
            alert_id = parts[1].strip()
            try:
                await alert_service.record_operator_action(
                    db=db,
                    alert_id=alert_id,
                    user=username,
                    action="approve",
                    note="Acknowledged via Telegram command /ack",
                )
                await self.send_message(chat_id, f"✅ Alert <code>{alert_id}</code> <b>ACKNOWLEDGED</b> by @{username}.")
                return {"status": "acked", "alert_id": alert_id}
            except Exception as e:
                await self.send_message(chat_id, f"❌ Failed to acknowledge alert: {e}")
                return {"status": "error", "detail": str(e)}

        # 5. /snooze <id> <minutes>
        elif text.startswith("/snooze"):
            parts = text.split()
            if len(parts) < 2:
                await self.send_message(chat_id, "Usage: <code>/snooze ALT-12345 [minutes]</code>")
                return {"status": "bad_syntax"}
            alert_id = parts[1].strip()
            minutes = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 30
            try:
                await alert_service.record_operator_action(
                    db=db,
                    alert_id=alert_id,
                    user=username,
                    action="snooze",
                    note=f"Snoozed for {minutes}m via Telegram command /snooze",
                )
                await self.send_message(chat_id, f"⏱ Alert <code>{alert_id}</code> <b>SNOOZED</b> for {minutes}m by @{username}.")
                return {"status": "snoozed", "alert_id": alert_id}
            except Exception as e:
                await self.send_message(chat_id, f"❌ Failed to snooze alert: {e}")
                return {"status": "error", "detail": str(e)}

        # 6. /mute [hours]
        elif text.startswith("/mute"):
            stmt = select(Subscription).join(NotificationChannel).where(NotificationChannel.encrypted_address == str(chat_id))
            sub = (await db.execute(stmt)).scalars().first()
            if sub:
                sub.quiet_hours = {"start": "00:00", "end": "23:59", "allow_critical_override": True}
                await db.commit()
                await self.send_message(chat_id, "🔇 Channel muted. Only CRITICAL safety alerts will break through.")
            else:
                await self.send_message(chat_id, "ℹ️ Channel not subscribed.")
            return {"status": "muted"}

        # 7. /unmute
        elif text == "/unmute":
            stmt = select(Subscription).join(NotificationChannel).where(NotificationChannel.encrypted_address == str(chat_id))
            sub = (await db.execute(stmt)).scalars().first()
            if sub:
                sub.quiet_hours = {"start": "", "end": "", "allow_critical_override": True}
                await db.commit()
                await self.send_message(chat_id, "🔔 Channel unmuted. Standard alert stream restored.")
            return {"status": "unmuted"}

        # 8. /stop (Unsubscribe)
        elif text == "/stop":
            stmt = select(NotificationChannel).where(NotificationChannel.encrypted_address == str(chat_id))
            ch = (await db.execute(stmt)).scalars().first()
            if ch:
                ch.status = "NOT CONFIGURED"
                ch.last_error = "Unsubscribed via /stop command."
                await db.commit()
                await self.send_message(chat_id, "🛑 You have unsubscribed from ASTRA-GUARD alerts. Send /start to reconnect.")
            return {"status": "stopped"}

        # 9. /help
        else:
            help_text = (
                "🛰 <b>ASTRA-GUARD Flight Controller Commands:</b>\n\n"
                "• /status — Fused risk score overview per satellite\n"
                "• /alerts — List active unacknowledged alerts\n"
                "• /ack &lt;alert_id&gt; — Acknowledge an alert\n"
                "• /snooze &lt;alert_id&gt; &lt;min&gt; — Snooze alert\n"
                "• /mute — Mute non-critical alerts\n"
                "• /unmute — Restore standard notifications\n"
                "• /stop — Unsubscribe this chat\n"
                "• /help — Display this command reference"
            )
            await self.send_message(chat_id, help_text)
            return {"status": "help_sent"}

    async def start_polling(self) -> None:
        """Run polling worker loop for local development without public webhook."""
        import asyncio

        from app.db.session import async_session_factory

        if not self.bot_token or settings.TELEGRAM_MODE != "polling":
            return

        logger.info("Starting Telegram Bot polling loop...")
        offset = 0
        while True:
            try:
                url = f"{self.api_base}/bot{self.bot_token}/getUpdates"
                async with self._get_client() as client:
                    res = await client.post(url, json={"offset": offset, "timeout": 10}, timeout=15.0)
                    data = res.json()
                    if data.get("ok"):
                        for update in data.get("result", []):
                            offset = max(offset, update["update_id"] + 1)
                            async with async_session_factory() as db:
                                await self.process_update(update, db)
            except asyncio.CancelledError:
                logger.info("Telegram polling loop stopped.")
                break
            except Exception as e:
                logger.warning(f"Error in Telegram polling loop: {e}")
                await asyncio.sleep(5)


telegram_service = TelegramService()
