"""Server-Sent Events router for real-time updates."""

import logging

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.services.sse_manager import sse_manager

router = APIRouter(tags=["sse"])
logger = logging.getLogger(__name__)


@router.get("/api/assignments/stream")
async def stream_assignments():
    """
    Stream assignment updates via Server-Sent Events.

    Clients can connect to this endpoint to receive real-time
    updates when assignments are created or their status changes.

    Returns:
        EventSourceResponse: SSE stream with assignment update events

    Events:
        - assignment_update: Assignment created or status changed

    Example client usage (JavaScript):
        ```javascript
        const eventSource = new EventSource('http://localhost:4000/api/assignments/stream');

        eventSource.addEventListener('assignment_update', (event) => {
            const data = JSON.parse(event.data);
            console.log('Assignment update:', data);
        });
        ```
    """
    logger.info("New SSE client connected to /api/assignments/stream")
    return EventSourceResponse(sse_manager.subscribe())
