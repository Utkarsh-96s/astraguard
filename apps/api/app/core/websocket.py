"""WebSocket Connection Manager for real-time alerts and risk streams."""
import json
from typing import Any

from fastapi import WebSocket

from app.core.logging import logger


class ConnectionManager:
    """Manages active WebSocket connections for alerts and asset risk streams."""

    def __init__(self) -> None:
        self.alerts_connections: set[WebSocket] = set()
        self.risk_connections: dict[str, set[WebSocket]] = {}

    async def connect_alerts(self, websocket: WebSocket) -> None:
        """Accept and register connection to the /ws/alerts feed."""
        await websocket.accept()
        self.alerts_connections.add(websocket)
        logger.info(f"WebSocket client connected to /ws/alerts (total: {len(self.alerts_connections)})")

    def disconnect_alerts(self, websocket: WebSocket) -> None:
        """Unregister connection from /ws/alerts."""
        self.alerts_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected from /ws/alerts (total: {len(self.alerts_connections)})")

    async def connect_risk(self, asset_id: str, websocket: WebSocket) -> None:
        """Accept and register connection to /ws/risk/{asset_id}."""
        await websocket.accept()
        if asset_id not in self.risk_connections:
            self.risk_connections[asset_id] = set()
        self.risk_connections[asset_id].add(websocket)
        logger.info(f"WebSocket client connected to /ws/risk/{asset_id} (total: {len(self.risk_connections[asset_id])})")

    def disconnect_risk(self, asset_id: str, websocket: WebSocket) -> None:
        """Unregister connection from /ws/risk/{asset_id}."""
        if asset_id in self.risk_connections:
            self.risk_connections[asset_id].discard(websocket)
            if not self.risk_connections[asset_id]:
                del self.risk_connections[asset_id]
        logger.info(f"WebSocket client disconnected from /ws/risk/{asset_id}")

    async def broadcast_alert(self, message: dict[str, Any]) -> None:
        """Broadcast alert message to all connected /ws/alerts clients."""
        text = json.dumps(message)
        dead_connections: list[WebSocket] = []
        for connection in list(self.alerts_connections):
            try:
                await connection.send_text(text)
            except Exception as e:
                logger.warning(f"Error sending to alerts WS connection: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect_alerts(dead)

    async def broadcast_risk(self, asset_id: str, message: dict[str, Any]) -> None:
        """Broadcast risk snapshot to all connected clients for asset_id."""
        if asset_id not in self.risk_connections:
            return

        text = json.dumps(message)
        dead_connections: list[WebSocket] = []
        for connection in list(self.risk_connections[asset_id]):
            try:
                await connection.send_text(text)
            except Exception as e:
                logger.warning(f"Error sending to risk WS connection for {asset_id}: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect_risk(asset_id, dead)


ws_manager = ConnectionManager()
