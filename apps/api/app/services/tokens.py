"""HMAC-signed single-use action and channel-linking tokens."""
import base64
import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import LinkToken


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding and padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def compute_token_hash(token: str) -> str:
    """Compute deterministic SHA-256 hash of a token for DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def generate_action_token(
    db: AsyncSession,
    alert_id: str,
    channel_id: str | None,
    action: str,
    user_id: str = "Operator",
    expiry_seconds: int = 86400,
) -> tuple[str, str]:
    """Generate an HMAC-signed single-use action token and return (token, full_action_url)."""
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=expiry_seconds)
    expiry_ts = int(expires_at.timestamp())
    nonce = uuid.uuid4().hex[:8]

    # payload: alert_id:channel_id:action:user_id:expiry_ts:nonce
    channel_val = channel_id or "none"
    payload_str = f"{alert_id}:{channel_val}:{action}:{user_id}:{expiry_ts}:{nonce}"
    payload_b64 = _b64encode(payload_str.encode("utf-8"))

    sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64encode(sig)

    token_str = f"{payload_b64}.{sig_b64}"
    token_hash = compute_token_hash(token_str)

    # Persist in link_tokens table
    db_token = LinkToken(
        id=f"TKN-{uuid.uuid4().hex[:12].upper()}",
        token_hash=token_hash,
        token_type="action",
        user_id=user_id,
        channel_id=channel_id,
        alert_id=alert_id,
        action=action.lower(),
        expires_at=expires_at,
        created_at=now,
    )
    db.add(db_token)
    await db.commit()

    action_url = f"{settings.API_BASE_URL}/api/v1/alerts/{alert_id}/action-token/{token_str}"
    return token_str, action_url


async def verify_and_consume_action_token(
    db: AsyncSession,
    token_str: str,
) -> dict[str, Any]:
    """Verify HMAC signature, expiry, and single-use state; marks token as used."""
    if "." not in token_str:
        raise ValueError("Malformed action token.")

    payload_b64, sig_b64 = token_str.split(".", 1)

    expected_sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    try:
        actual_sig = _b64decode(sig_b64)
    except Exception as e:
        raise ValueError("Invalid signature format.") from e

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature.")

    try:
        payload_str = _b64decode(payload_b64).decode("utf-8")
        parts = payload_str.split(":")
        if len(parts) != 6:
            raise ValueError("Invalid payload segments.")
        alert_id, channel_val, action, user_id, expiry_ts_str, _nonce = parts
        expiry_ts = int(expiry_ts_str)
    except Exception as e:
        raise ValueError(f"Failed to unpack token payload: {e}") from e

    now = datetime.now(UTC)
    if datetime.fromtimestamp(expiry_ts, tz=UTC) < now:
        raise ValueError("Action token has expired.")

    token_hash = compute_token_hash(token_str)
    stmt = select(LinkToken).where(LinkToken.token_hash == token_hash)
    res = await db.execute(stmt)
    db_token = res.scalars().first()

    if not db_token:
        raise ValueError("Token not found in registry.")

    if db_token.used_at is not None:
        raise ValueError(f"Action token has already been used at {db_token.used_at.isoformat()}.")

    # Mark consumed
    db_token.used_at = now
    await db.commit()

    return {
        "alert_id": alert_id,
        "channel_id": None if channel_val == "none" else channel_val,
        "action": action,
        "user": user_id,
        "consumed_at": now.isoformat(),
    }


async def generate_linking_token(
    db: AsyncSession,
    user_id: str,
    channel_type: str = "telegram",
    expiry_seconds: int = 3600,
) -> tuple[str, str]:
    """Generate a one-time linking code for bot / channel pairing."""
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=expiry_seconds)
    code = f"LINK-{uuid.uuid4().hex[:12].upper()}"
    token_hash = compute_token_hash(code)

    db_token = LinkToken(
        id=f"LNK-{uuid.uuid4().hex[:12].upper()}",
        token_hash=token_hash,
        token_type=f"{channel_type}_link",
        user_id=user_id,
        expires_at=expires_at,
        created_at=now,
    )
    db.add(db_token)
    await db.commit()

    bot_username = settings.TELEGRAM_BOT_USERNAME or "AstraGuardAlertsBot"
    deep_link = f"https://t.me/{bot_username}?start={code}"
    return code, deep_link


async def verify_and_consume_linking_token(
    db: AsyncSession,
    code: str,
    channel_type: str = "telegram",
) -> LinkToken:
    """Verify linking code and mark it consumed upon successful handshake."""
    token_hash = compute_token_hash(code.strip())
    stmt = select(LinkToken).where(
        LinkToken.token_hash == token_hash,
        LinkToken.token_type == f"{channel_type}_link",
    )
    res = await db.execute(stmt)
    db_token = res.scalars().first()

    if not db_token:
        raise ValueError("Invalid or unknown linking code.")

    now = datetime.now(UTC)
    exp = db_token.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)
    if exp < now:
        raise ValueError("Linking code has expired.")

    if db_token.used_at is not None:
        raise ValueError(f"Linking code was already used at {db_token.used_at.isoformat()}.")

    db_token.used_at = now
    await db.commit()
    return db_token
