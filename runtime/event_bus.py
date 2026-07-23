"""
runtime/event_bus.py — Lightweight in-process event bus.

Decouples runtime components. Components publish events; subscribers react.
Designed to swap to Amazon EventBridge without changing publisher interfaces.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

logger = logging.getLogger("aros.event_bus")

Handler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class EventBus:
    """Async publish/subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = {}
        self._history: list[dict[str, Any]] = []

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)
        logger.debug("EventBus: subscribed to %s", event_type)

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "event_type": event_type,
            "payload": payload,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        self._history.append(event)
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(payload)
            except Exception as exc:
                logger.error("EventBus handler error (%s): %s", event_type, exc)
        logger.debug("EventBus: published %s → %d handlers", event_type, len(handlers))

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._history[-limit:]

    def get_status(self) -> dict[str, Any]:
        return {
            "subscriptions": {k: len(v) for k, v in self._subscribers.items()},
            "total_events": len(self._history),
        }
