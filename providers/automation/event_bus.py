import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger("automation_event_bus")

class EventMessage(BaseModel):
    """Event message emitted on the internal Event Bus."""
    event_id: str
    event_type: str  # SCHEDULE, PACKAGE_CREATED, PACKAGE_UPDATED, QUALITY_APPROVED, PUBLISHING_COMPLETED, PUBLISHING_FAILED, LEARNING_RECOMMENDATION, EXPERIMENT_COMPLETED, RETRY_REQUESTED, MANUAL_TRIGGER, WEBHOOK_TRIGGER
    source: str
    payload: Dict[str, Any]
    timestamp: str = datetime.now(UTC).replace(tzinfo=None).isoformat()

class EventBus:
    """Internal Event Bus for decoupled event publishing, subscription, and event replay."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[EventMessage], Any]]] = {}
        self._event_history: List[EventMessage] = []

    def subscribe(self, event_type: str, handler: Callable[[EventMessage], Any]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event: EventMessage) -> None:
        self._event_history.append(event)
        logger.info(f"[EventBus] Published event '{event.event_type}' (ID: {event.event_id}) from {event.source}")

        handlers = self._subscribers.get(event.event_type, []) + self._subscribers.get("*", [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"[EventBus] Error executing subscriber handler for {event.event_type}: {str(e)}")

    def replay_events(self, limit: int = 50) -> List[EventMessage]:
        return self._event_history[-limit:]

event_bus = EventBus()
ZOOMING = "zoom"
