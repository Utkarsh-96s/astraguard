"""WebSocket router for real-time alert and risk streams."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import logger
from app.core.websocket import ws_manager

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket) -> None:
    """Real-time streaming feed for platform alerts and operator action events."""
    await ws_manager.connect_alerts(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "event": "CONNECTED",
            "channel": "alerts",
            "message": "Connected to ASTRA-GUARD real-time alert feed.",
        })
        while True:
            # Keep connection open, receive ping/messages if client sends any
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_alerts(websocket)
    except Exception as e:
        logger.warning(f"Exception in /ws/alerts: {e}")
        ws_manager.disconnect_alerts(websocket)


@router.websocket("/ws/risk/{asset_id}")
async def websocket_risk_endpoint(websocket: WebSocket, asset_id: str) -> None:
    """Real-time streaming feed for fused mission risk updates for a specific satellite."""
    await ws_manager.connect_risk(asset_id, websocket)
    try:
        await websocket.send_json({
            "event": "CONNECTED",
            "channel": f"risk/{asset_id}",
            "asset_id": asset_id,
            "message": f"Connected to ASTRA-GUARD risk telemetry feed for {asset_id}.",
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_risk(asset_id, websocket)
    except Exception as e:
        logger.warning(f"Exception in /ws/risk/{asset_id}: {e}")
        ws_manager.disconnect_risk(asset_id, websocket)
