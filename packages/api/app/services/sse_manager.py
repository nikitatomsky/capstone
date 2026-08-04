"""Server-Sent Events manager for real-time assignment updates."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


class SSEManager:
    """Manages Server-Sent Events connections for real-time updates."""

    def __init__(self):
        """Initialize the SSE manager with an empty connection set."""
        self.connections: set[asyncio.Queue] = set()
        logger.info("SSE Manager initialized")

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """
        Subscribe to assignment update events.

        Creates a new queue for this client connection and yields messages
        as they are broadcast. Automatically cleans up the connection when
        the client disconnects.

        Yields:
            str: SSE-formatted messages (event: <type>\ndata: <json>\n\n)
        """
        queue: asyncio.Queue = asyncio.Queue()
        self.connections.add(queue)
        logger.info(f"New SSE client connected. Total connections: {len(self.connections)}")

        try:
            while True:
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            logger.info("SSE client disconnected (cancelled)")
            raise
        finally:
            self.connections.remove(queue)
            logger.info(f"SSE client disconnected. Total connections: {len(self.connections)}")

    async def broadcast(self, event_type: str, data: dict):
        """
        Broadcast event to all connected clients.

        Args:
            event_type: Type of event (e.g., "assignment_created", "assignment_updated")
            data: Event data to be JSON-serialized and sent to clients

        Example:
            await sse_manager.broadcast("assignment_created", {
                "assignment_id": "abc123",
                "status": "pending",
                "technician_name": "John Doe"
            })
        """
        if not self.connections:
            logger.debug(f"No SSE clients connected, skipping broadcast of {event_type}")
            return

        message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        logger.info(f"Broadcasting {event_type} to {len(self.connections)} clients")

        # Send to all connected clients
        disconnected = []
        for queue in self.connections:
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"Failed to send SSE message to client: {e}")
                disconnected.append(queue)

        # Clean up any failed connections
        for queue in disconnected:
            self.connections.discard(queue)


# Global SSE manager instance
sse_manager = SSEManager()
