"""WebSocket manager for AI chat connections."""

import asyncio
import json
from typing import Dict, Optional, Set

from fastapi import WebSocket


class ChatConnectionManager:
    """Manages WebSocket connections for AI chat."""

    def __init__(self):
        """Initialize chat connection manager."""
        # Map research_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, research_id: str):
        """
        Connect a WebSocket for a specific research chat.

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

    async def send_message(self, research_id: str, data: dict):
        """
        Send message to all connections for a research chat.

        Args:
            research_id: Research ID
            data: Message data
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

    async def stream_chunk(self, research_id: str, chunk: str):
        """
        Stream a chunk of text to all connections.

        Args:
            research_id: Research ID
            chunk: Text chunk to stream
        """
        await self.send_message(research_id, {"type": "chunk", "content": chunk})

    async def send_complete(self, research_id: str, full_message: str):
        """
        Send completion signal with full message.

        Args:
            research_id: Research ID
            full_message: Complete message text
        """
        await self.send_message(
            research_id, {"type": "complete", "content": full_message}
        )

    async def send_error(self, research_id: str, error: str):
        """
        Send error message.

        Args:
            research_id: Research ID
            error: Error message
        """
        await self.send_message(research_id, {"type": "error", "content": error})

    async def send_tool_use(self, research_id: str, tool_name: str, tool_args: dict):
        """
        Send tool usage notification.

        Args:
            research_id: Research ID
            tool_name: Tool name
            tool_args: Tool arguments
        """
        await self.send_message(
            research_id, {"type": "tool_use", "tool": tool_name, "arguments": tool_args}
        )

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


# Global chat connection manager instance
chat_manager = ChatConnectionManager()
