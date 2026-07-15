import asyncio
import logging
from typing import Callable, Coroutine, Any
from contracts.interfaces.eventbus import EventBus

logger = logging.getLogger("memory_event_bus")

class MemoryEventBus(EventBus):
    """Fully operational in-memory Event Bus implementation using asyncio."""
    
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[dict[str, Any]], Coroutine[Any, Any, None]]]] = {}

    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        """Publishes an event to all subscribed async handlers."""
        logger.info(f"EventBus: Publishing event to topic '{topic}'")
        if topic in self._handlers:
            for handler in self._handlers[topic]:
                asyncio.create_task(self._safe_execute(handler, message))

    async def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]]) -> None:
        """Registers an async callback handler to listen for events on a topic."""
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append(handler)
        logger.info(f"EventBus: Registered listener for topic '{topic}'")

    async def _safe_execute(
        self,
        handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
        message: dict[str, Any]
    ) -> None:
        """Executes a handler safely capturing and logging exceptions."""
        try:
            await handler(message)
        except Exception as e:
            logger.error(f"EventBus handler execution error: {str(e)}", exc_info=True)
pre_configured_bus = MemoryEventBus()
