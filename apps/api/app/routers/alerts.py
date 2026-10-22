"""Router for operational alerts, operator action auditing, delivery outbox tracking, and test alerts."""
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Alert,
    EscalationState,
    NotificationChannel,
    NotificationOutbox,
    OperatorAction,
    RiskSnapshot,
)
from app.db.session import get_db
from app.services.alert_service import alert_service
from app.services.outbox_worker import mask_contact_info
from app.services.tokens import verify_and_consume_action_token

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


class OperatorActionRequest(BaseModel):
    """Payload to record an operator action on an alert."""
    user: str = Field("FlightDirector", description="Operator name or callsign")
    action: str = Field(..., description="Action: 'approve', 'dismiss', 'snooze', 'assign', 'note', 'escalate'")
    note: str | None = Field(None, description="Optional engineering justification note")


class TestAlertRequest(BaseModel):
    """Payload to fire an end-to-end verified test alert."""
    level: str = Field("CRITICAL", description="Severity: WATCH, WARNING, CRITICAL")
    asset_id: str = Field("SENTINEL-2A", description="Target spacecraft asset")


@router.get("", summary="List mission alerts with server-side filters and cursor")
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None, description="Search query string matching title or rationale"),
    asset_id: str | None = Query(None, description="Filter by spacecraft asset ID"),
    status: str | None = Query(None, description="Filter by status (ACTIVE, ACKNOWLEDGED, DISMISSED, SNOOZED)"),
    level: str | None = Query(None, description="Filter by severity level (WATCH, WARNING, CRITICAL)"),
    channel: str | None = Query(None, description="Filter by delivered channel type (telegram, webpush, etc.)"),
    since: str | None = Query(None, description="ISO timestamp cursor to retrieve only alerts created after 'since'"),
    sort_by: str = Query("created_at", description="Sort field: created_at, level, status"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    """Retrieve filtered, searched, and paginated mission alerts."""
    stmt = (
        select(Alert, RiskSnapshot.asset_id)
        .join(RiskSnapshot, Alert.snapshot_id == RiskSnapshot.id, isouter=True)
    )

    if q:
        search_filter = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                Alert.title.ilike(search_filter),
                Alert.rationale.ilike(search_filter),
                Alert.recommendation.ilike(search_filter),
            )
        )
    if asset_id:
        stmt = stmt.where(RiskSnapshot.asset_id == asset_id)
    if status and status.upper() != "ALL":
        stmt = stmt.where(Alert.status == status.upper())
    if level and level.upper() != "ALL":
        stmt = stmt.where(Alert.level == level.upper())
    if since:
        try:
            clean_since = since.strip().replace(" ", "+")
            if clean_since.endswith("Z"):
                clean_since = clean_since[:-1] + "+00:00"
            since_dt = datetime.fromisoformat(clean_since)
            stmt = stmt.where(or_(Alert.created_at > since_dt, Alert.created_at > since_dt.replace(tzinfo=None)))
        except Exception:
            pass

    if sort_order.lower() == "asc":
        stmt = stmt.order_by(Alert.created_at.asc())
    else:
        stmt = stmt.order_by(Alert.created_at.desc())

    stmt = stmt.offset(offset).limit(limit)

    res = await db.execute(stmt)
    rows = list(res.all())

    output = []
    now = datetime.now(UTC)

    for a, a_asset_id in rows:
        # Fetch latest escalation state if active
        esc_stmt = select(EscalationState).where(EscalationState.alert_id == a.id)
        esc_state = (await db.execute(esc_stmt)).scalars().first()

        next_esc_countdown: int | None = None
        if esc_state and esc_state.next_escalation_at and not esc_state.halted_at:
            next_at = esc_state.next_escalation_at
            if next_at.tzinfo is None:
                next_at = next_at.replace(tzinfo=UTC)
            countdown = int((next_at - now).total_seconds())
            next_esc_countdown = max(0, countdown)

        # Audit action count
        actions_stmt = select(OperatorAction).where(OperatorAction.alert_id == a.id).order_by(OperatorAction.ts.asc())
        actions = list((await db.execute(actions_stmt)).scalars().all())

        output.append({
            "id": a.id,
            "snapshot_id": a.snapshot_id,
            "asset_id": a_asset_id or "SENTINEL-2A",
            "level": a.level,
            "title": a.title,
            "rationale": a.rationale,
            "recommendation": a.recommendation,
            "status": a.status,
            "dedup_key": a.dedup_key,
            "synthetic": a.synthetic,
            "created_at": a.created_at.isoformat(),
            "escalation": {
                "current_level": esc_state.current_level if esc_state else 1,
                "countdown_seconds": next_esc_countdown,
                "halted": bool(esc_state.halted_at) if esc_state else True,
            },
            "audit_actions": [
                {
                    "id": act.id,
                    "user": act.user,
                    "action": act.action,
                    "note": act.note,
                    "timestamp": act.ts.isoformat(),
                }
                for act in actions
            ],
        })

    return output


@router.post("/test", summary="Fire an end-to-end verified test alert")
async def fire_test_alert(
    req: TestAlertRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trigger a simulated test alert through the complete pipeline with test=true."""
    alert = await alert_service.fire_test_alert(
        db=db,
        level=req.level,
        asset_id=req.asset_id,
    )

    # Count outbox deliveries created
    outbox_stmt = select(NotificationOutbox).where(NotificationOutbox.alert_id == alert.id)
    outbox_items = list((await db.execute(outbox_stmt)).scalars().all())

    return {
        "status": "triggered",
        "alert": {
            "id": alert.id,
            "level": alert.level,
            "title": alert.title,
            "synthetic": alert.synthetic,
            "created_at": alert.created_at.isoformat(),
        },
        "outbox_deliveries_queued": len(outbox_items),
        "test": True,
    }


@router.get("/{alert_id}", summary="Get alert details and audit actions")
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve full details of an alert including its operator audit trail."""
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")

    actions_stmt = select(OperatorAction).where(OperatorAction.alert_id == alert_id).order_by(OperatorAction.ts.asc())
    actions = list((await db.execute(actions_stmt)).scalars().all())

    snapshot = await db.get(RiskSnapshot, alert.snapshot_id)

    # Escalation state
    esc_stmt = select(EscalationState).where(EscalationState.alert_id == alert.id)
    esc_state = (await db.execute(esc_stmt)).scalars().first()
    now = datetime.now(UTC)

    next_countdown = None
    if esc_state and esc_state.next_escalation_at and not esc_state.halted_at:
        next_at = esc_state.next_escalation_at
        if next_at.tzinfo is None:
            next_at = next_at.replace(tzinfo=UTC)
        next_countdown = max(0, int((next_at - now).total_seconds()))

    return {
        "id": alert.id,
        "snapshot_id": alert.snapshot_id,
        "asset_id": snapshot.asset_id if snapshot else "UNKNOWN",
        "level": alert.level,
        "title": alert.title,
        "rationale": alert.rationale,
        "recommendation": alert.recommendation,
        "status": alert.status,
        "dedup_key": alert.dedup_key,
        "synthetic": alert.synthetic,
        "created_at": alert.created_at.isoformat(),
        "escalation": {
            "current_level": esc_state.current_level if esc_state else 1,
            "countdown_seconds": next_countdown,
            "halted": bool(esc_state.halted_at) if esc_state else True,
            "halted_reason": esc_state.halted_reason if esc_state else None,
        },
        "audit_actions": [
            {
                "id": act.id,
                "user": act.user,
                "action": act.action,
                "note": act.note,
                "timestamp": act.ts.isoformat(),
            }
            for act in actions
        ],
    }


@router.get("/{alert_id}/deliveries", summary="Get delivery status chips per channel")
async def get_alert_deliveries(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve outbox deliveries, channels, latency, and delivery status chips for an alert."""
    stmt = (
        select(NotificationOutbox, NotificationChannel)
        .join(NotificationChannel, NotificationOutbox.channel_id == NotificationChannel.id)
        .where(NotificationOutbox.alert_id == alert_id)
        .order_by(NotificationOutbox.created_at.asc())
    )
    rows = list((await db.execute(stmt)).all())

    return [
        {
            "outbox_id": item.id,
            "channel_id": channel.id,
            "channel_name": channel.name,
            "channel_type": channel.type,
            "masked_address": mask_contact_info(channel.encrypted_address),
            "status": item.status,  # queued, sending, sent, delivered, failed, dead
            "escalation_level": item.escalation_level,
            "attempts": item.attempts,
            "max_attempts": item.max_attempts,
            "last_error": item.last_error,
            "provider_message_id": item.provider_message_id,
            "sent_at": item.sent_at.isoformat() if item.sent_at else None,
            "delivered_at": item.delivered_at.isoformat() if item.delivered_at else None,
            "acked_at": item.acked_at.isoformat() if item.acked_at else None,
            "test": item.test,
        }
        for item, channel in rows
    ]


@router.post("/{alert_id}/action", summary="Submit operator action on alert")
async def submit_operator_action(
    alert_id: str,
    request: OperatorActionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Record a human-in-the-loop operator action (approve, dismiss, snooze, assign, note, escalate)."""
    try:
        op_action = await alert_service.record_operator_action(
            db=db,
            alert_id=alert_id,
            user=request.user,
            action=request.action,
            note=request.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Retrieve updated alert
    alert = await db.get(Alert, alert_id)

    return {
        "status": "success",
        "action": {
            "id": op_action.id,
            "alert_id": op_action.alert_id,
            "user": op_action.user,
            "action": op_action.action,
            "note": op_action.note,
            "timestamp": op_action.ts.isoformat(),
        },
        "alert": {
            "id": alert.id if alert else alert_id,
            "status": alert.status if alert else "UPDATED",
            "level": alert.level if alert else "UNKNOWN",
        },
    }


@router.get("/{alert_id}/action-token/{token}", summary="Display signed action confirmation form (GET)")
async def get_action_token_confirmation(
    alert_id: str,
    token: str,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Confirmation landing page for email / browser scanner protection before executing action."""
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>ASTRA-GUARD Operator Action Confirmation</title>
  <style>
    body {{ background: #000; color: #f0f0fa; font-family: monospace; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
    .card {{ background: #121214; border: 1px solid #404040; border-radius: 8px; padding: 24px; max-width: 480px; width: 90%; }}
    .title {{ font-size: 16px; font-weight: bold; color: #fe1e34; margin-bottom: 8px; }}
    .btn {{ background: #fe1e34; color: #fff; border: none; padding: 10px 20px; font-weight: bold; border-radius: 4px; cursor: pointer; font-family: monospace; margin-top: 16px; }}
    .btn:hover {{ background: #dc2626; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="title">ASTRA-GUARD OPERATOR ACTION CONFIRMATION</div>
    <p>Alert ID: <strong>{alert.id}</strong></p>
    <p>Title: {alert.title}</p>
    <p>Severity: <strong>{alert.level}</strong></p>
    <p style="color: #888; font-size: 11px;">Human-in-the-Loop Protocol: Confirm below to execute signed operator acknowledgment.</p>
    <form method="POST">
      <button type="submit" class="btn">Confirm & Execute Action</button>
    </form>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.post("/{alert_id}/action-token/{token}", summary="Execute signed action token (POST)")
async def execute_action_token(
    alert_id: str,
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute HMAC-signed action token after single-use validation."""
    try:
        consumed = await verify_and_consume_action_token(db, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    action = consumed["action"]
    user = consumed.get("user") or "SignedTokenOperator"

    # Record action
    op_action = await alert_service.record_operator_action(
        db=db,
        alert_id=alert_id,
        user=user,
        action=action,
        note=f"Authorized via single-use signed token for channel {consumed.get('channel_id')}",
    )

    alert = await db.get(Alert, alert_id)
    return {
        "status": "success",
        "action_executed": action,
        "operator": user,
        "alert_status": alert.status if alert else "UPDATED",
        "timestamp": op_action.ts.isoformat(),
    }
