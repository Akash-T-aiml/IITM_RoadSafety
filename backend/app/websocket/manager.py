"""
SmartRescue AI — WebSocket Connection Manager
Manages WebSocket connections grouped by channels for real-time communication.
"""

import json
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections organized by channels.
    
    Channel naming convention:
        - case:{case_id}      — Emergency case updates
        - ambulance:{id}      — Ambulance-specific channel
        - hospital:{id}       — Hospital dashboard channel
        - tracking:{case_id}  — Live location tracking for a case
        - admin:dashboard     — Admin monitoring
        - user:{uid}          — User-specific notifications
    """

    def __init__(self):
        # channel -> {client_id -> WebSocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # client_id -> set of channels they're subscribed to
        self.client_channels: Dict[str, Set[str]] = {}

    async def connect(
        self, websocket: WebSocket, channel: str, client_id: str
    ):
        """Accept a WebSocket connection and register it to a channel."""
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = {}
        self.active_connections[channel][client_id] = websocket

        if client_id not in self.client_channels:
            self.client_channels[client_id] = set()
        self.client_channels[client_id].add(channel)

        logger.info(
            f"WebSocket connected: client={client_id}, channel={channel}",
            extra={"channel": channel, "client_id": client_id}
        )

    async def disconnect(self, channel: str, client_id: str):
        """Remove a WebSocket connection from a channel."""
        if channel in self.active_connections:
            self.active_connections[channel].pop(client_id, None)
            if not self.active_connections[channel]:
                del self.active_connections[channel]

        if client_id in self.client_channels:
            self.client_channels[client_id].discard(channel)
            if not self.client_channels[client_id]:
                del self.client_channels[client_id]

        logger.info(
            f"WebSocket disconnected: client={client_id}, channel={channel}"
        )

    async def disconnect_client(self, client_id: str):
        """Remove a client from all channels."""
        channels = self.client_channels.get(client_id, set()).copy()
        for channel in channels:
            await self.disconnect(channel, client_id)

    async def broadcast(self, channel: str, message: Dict[str, Any]):
        """Send a message to all clients in a channel."""
        if channel not in self.active_connections:
            return

        disconnected = []
        payload = json.dumps(message, default=str)

        for client_id, websocket in self.active_connections[channel].items():
            try:
                await websocket.send_text(payload)
            except Exception as e:
                logger.warning(
                    f"Failed to send to {client_id} on {channel}: {e}"
                )
                disconnected.append(client_id)

        # Clean up dead connections
        for client_id in disconnected:
            await self.disconnect(channel, client_id)

    async def send_personal(
        self, channel: str, client_id: str, message: Dict[str, Any]
    ):
        """Send a message to a specific client on a channel."""
        if (
            channel in self.active_connections
            and client_id in self.active_connections[channel]
        ):
            try:
                payload = json.dumps(message, default=str)
                await self.active_connections[channel][client_id].send_text(
                    payload
                )
            except Exception as e:
                logger.warning(
                    f"Failed to send personal message to {client_id}: {e}"
                )
                await self.disconnect(channel, client_id)

    async def broadcast_to_multiple_channels(
        self, channels: List[str], message: Dict[str, Any]
    ):
        """Send a message to multiple channels at once."""
        for channel in channels:
            await self.broadcast(channel, message)

    def get_channel_clients(self, channel: str) -> List[str]:
        """Get list of client IDs connected to a channel."""
        if channel in self.active_connections:
            return list(self.active_connections[channel].keys())
        return []

    def get_connection_count(self, channel: Optional[str] = None) -> int:
        """Get total connections or connections for a specific channel."""
        if channel:
            return len(self.active_connections.get(channel, {}))
        return sum(len(clients) for clients in self.active_connections.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": self.get_connection_count(),
            "total_channels": len(self.active_connections),
            "total_clients": len(self.client_channels),
            "channels": {
                channel: len(clients)
                for channel, clients in self.active_connections.items()
            },
        }


# Global singleton instance
ws_manager = ConnectionManager()
