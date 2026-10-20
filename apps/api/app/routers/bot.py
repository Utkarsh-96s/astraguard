"""Phone Alert Bot Router (Telegram & Webhook)."""
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.bot_service import bot_service
from app.services.feature_service import feature_service

router = APIRouter(prefix="/bot", tags=["Phone Alert Bot"])


class BotActionRequest(BaseModel):
    """Payload for executing an operator action via the bot."""

    alert_id: str = Field(..., description="ID of the alert to act on")
    action: Literal["approve", "dismiss", "snooze"] = Field(
        ..., description="Action: approve, dismiss, or snooze"
    )
    operator: str = Field(
        "MobileOperator_Sarah", description="Operator identifier"
    )
    note: str = Field(
        "Executed via Mobile Telegram Bot inline button",
        description="Audit note for action",
    )


@router.get("/preview/{alert_id}", summary="Get Telegram alert dispatch preview")
async def get_bot_preview(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate Telegram Markdown message preview and interactive inline keyboard."""
    if not feature_service.is_enabled("phone_alert_bot"):
        raise HTTPException(
            status_code=403,
            detail="Phone Alert Bot feature is currently disabled via feature flags.",
        )

    try:
        return await bot_service.get_bot_preview(alert_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate bot preview: {e!s}"
        ) from e


@router.post("/dispatch/{alert_id}", summary="Dispatch alert to Telegram bot")
async def dispatch_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Dispatch alert to Telegram or trigger the deterministic mobile receiver."""
    if not feature_service.is_enabled("phone_alert_bot"):
        raise HTTPException(
            status_code=403,
            detail="Phone Alert Bot feature is currently disabled via feature flags.",
        )

    try:
        return await bot_service.dispatch_alert(alert_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to dispatch alert: {e!s}"
        ) from e


@router.post("/action", summary="Handle mobile callback action from bot")
async def bot_action(
    req: BotActionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute operator action (Approve / Dismiss / Snooze) originating from bot."""
    if not feature_service.is_enabled("phone_alert_bot"):
        raise HTTPException(
            status_code=403,
            detail="Phone Alert Bot feature is currently disabled via feature flags.",
        )

    try:
        return await bot_service.handle_callback_action(
            alert_id=req.alert_id,
            action=req.action,
            operator=req.operator,
            note=req.note,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to execute bot action: {e!s}"
        ) from e
