"""Server-Sent Events (SSE) and WebSocket event dispatcher."""

import asyncio
import json
from typing import Any, AsyncGenerator

from fastapi import WebSocket


class EventDispatcher:
    """
    Manages real-time event broadcasting to connected clients.

    Supports both SSE and WebSocket consumers.
    """

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, channel: str) -> asyncio.Queue:
        """Subscribe to a channel and receive an event queue."""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[channel].append(queue)
        return queue

    def unsubscribe(self, channel: str, queue: asyncio.Queue) -> None:
        """Unsubscribe a queue from a channel."""
        if channel in self._subscribers:
            self._subscribers[channel].remove(queue)
            if not self._subscribers[channel]:
                del self._subscribers[channel]

    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        """Publish an event to all subscribers of a channel."""
        if channel in self._subscribers:
            for queue in self._subscribers[channel]:
                await queue.put(event)

    async def sse_stream(self, channel: str) -> AsyncGenerator[str, None]:
        """Generate SSE-formatted events for a channel."""
        queue = self.subscribe(channel)
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            self.unsubscribe(channel, queue)

    async def websocket_handler(self, websocket: WebSocket, channel: str) -> None:
        """Handle a WebSocket connection for a channel."""
        await websocket.accept()
        queue = self.subscribe(channel)
        try:
            while True:
                event = await queue.get()
                await websocket.send_json(event)
        except Exception:
            pass
        finally:
            self.unsubscribe(channel, queue)


# ── Global dispatcher instance ──
event_dispatcher = EventDispatcher()
