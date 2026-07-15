import abc
from typing import Callable, Coroutine, Any

class EventBus(abc.ABC):
    """Abstract interface defining the message broker event bus operations."""
    
    @abc.abstractmethod
    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        """Publishes a structured data payload to a named topic routing queue."""
        pass

    @abc.abstractmethod
    async def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]]) -> None:
        """Subscribes an asynchronous listener callback handler to a topic channel."""
        pass
