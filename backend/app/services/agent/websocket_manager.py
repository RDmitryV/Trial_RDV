"""WebSocket manager for real-time agent progress updates."""

from typing import Dict, Set, Optional
from fastapi import WebSocket
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections for agent progress updates."""

    def __init__(self):
        """Initialize connection manager."""
        # Map research_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, research_id: str):
        """
        Connect a WebSocket for a specific research.

        Args:
            websocket: WebSocket connection
            research_id: Research ID
        """
        await websocket.accept()

        async with self._lock:
            if research_id not in self.active_connections:
                self.active_connections[research_id] = set()
            self.active_connections[research_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, research_id: str):
        """
        Disconnect a WebSocket.

        Args:
            websocket: WebSocket connection
            research_id: Research ID
        """
        async with self._lock:
            if research_id in self.active_connections:
                self.active_connections[research_id].discard(websocket)
                if not self.active_connections[research_id]:
                    del self.active_connections[research_id]

    async def send_progress_update(self, research_id: str, data: dict):
        """
        Send progress update to all connections for a research.

        Args:
            research_id: Research ID
            data: Progress data
        """
        async with self._lock:
            if research_id not in self.active_connections:
                return

            connections = list(self.active_connections[research_id])

        # Send to all connections (outside lock to avoid blocking)
        message = json.dumps(data)
        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception:
                # Connection is broken
                disconnected.append(websocket)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for websocket in disconnected:
                    if research_id in self.active_connections:
                        self.active_connections[research_id].discard(websocket)

    async def broadcast_to_all(self, data: dict):
        """
        Broadcast message to all active connections.

        Args:
            data: Message data
        """
        async with self._lock:
            all_connections = []
            for connections in self.active_connections.values():
                all_connections.extend(connections)

        message = json.dumps(data)
        for websocket in all_connections:
            try:
                await websocket.send_text(message)
            except Exception:
                pass

    def get_connection_count(self, research_id: Optional[str] = None) -> int:
        """
        Get number of active connections.

        Args:
            research_id: Optional research ID to filter by

        Returns:
            Connection count
        """
        if research_id:
            return len(self.active_connections.get(research_id, set()))
        else:
            return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()
