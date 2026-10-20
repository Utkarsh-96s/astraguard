"""Router for operational alerts and operator action auditing."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Alert, OperatorAction, RiskSnapshot
from app.db.session import get_db
from app.services.alert_service import alert_service

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


class OperatorActionRequest(BaseModel):
    """Payload to record an operator action on an alert."""

    user: str = Field("FlightDirector", description="Operator name or callsign")
    action: str = Field(..., description="Action: 'approve', 'dismiss', 'snooze'")
    note: str | None = Field(None, description="Optional engineering justification note")


@router.get("", summary="List mission alerts")
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None, description="Filter by status (ACTIVE, ACKNOWLEDGED, DISMISSED, SNOOZED)"),
    level: str | None = Query(None, description="Filter by severity level (WATCH, WARNING, CRITICAL)"),
    limit: int = Query(50, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Retrieve filtered mission alerts."""
    stmt = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Alert.status == status.upper())
    if level:
        stmt = stmt.where(Alert.level == level.upper())

    res = await db.execute(stmt)
    alerts = list(res.scalars().all())
    return [
        {
            "id": a.id,
            "snapshot_id": a.snapshot_id,
            "level": a.level,
            "title": a.title,
            "rationale": a.rationale,
            "recommendation": a.recommendation,
            "status": a.status,
            "dedup_key": a.dedup_key,
            "synthetic": a.synthetic,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


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
    res_actions = await db.execute(actions_stmt)
    actions = list(res_actions.scalars().all())

    snapshot = await db.get(RiskSnapshot, alert.snapshot_id)

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


@router.post("/{alert_id}/action", summary="Submit operator action on alert")
async def submit_operator_action(
    alert_id: str,
    request: OperatorActionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Record a human-in-the-loop operator action (approve, dismiss, snooze) on an active alert."""
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
