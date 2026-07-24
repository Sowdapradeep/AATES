import datetime
from typing import Any, Callable, Dict, List

class NarrativeEventBus:
    """
    Event Bus for emitting and subscribing to Narrative Core events
    (e.g., UNIVERSE_CREATED, CHARACTER_ADDED, STORY_BIBLE_MUTATED).
    """
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable[[dict[str, Any]], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[dict[str, Any]], None]) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "event_type": event_type,
            "timestamp": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(),
            "payload": payload,
        }
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                pass

narrative_event_bus = NarrativeEventBus()
