"""WebSocket streaming manager for real-time browser telemetry updates."""
import json
import asyncio
from typing import Set, Dict, Any
from fastapi import WebSocket
from app.schemas.telemetry import RealtimeOperationalState


class TelemetryStreamManager:
    """Manages active browser WebSocket client connections and broadcasts live telemetry frames."""

    def __init__(self):
        self._active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection and register client."""
        await websocket.accept()
        async with self._lock:
            self._active_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        """Unregister a disconnected WebSocket client."""
        async with self._lock:
            self._active_connections.discard(websocket)

    @property
    def client_count(self) -> int:
        return len(self._active_connections)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a generic JSON payload to all connected clients."""
        payload_str = json.dumps(message, default=str)
        dead_connections = set()

        async with self._lock:
            for conn in self._active_connections:
                try:
                    await conn.send_text(payload_str)
                except Exception:
                    dead_connections.add(conn)

            for dead in dead_connections:
                self._active_connections.discard(dead)

    async def broadcast_state(self, state: RealtimeOperationalState):
        """Broadcast a full fused operational state snapshot."""
        frame = {
            "type": "REALTIME_STATE_UPDATE",
            "data": state.model_dump(),
        }
        await self.broadcast(frame)


# Global singleton instance
stream_manager = TelemetryStreamManager()
