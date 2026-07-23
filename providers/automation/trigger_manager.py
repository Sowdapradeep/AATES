import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from providers.automation.event_bus import event_bus, EventMessage

logger = logging.getLogger("trigger_manager")

class TriggerEvent(BaseModel):
    """Trigger event representation supporting 11 trigger types."""
    trigger_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger_type: str  # SCHEDULE, PACKAGE_CREATED, PACKAGE_UPDATED, QUALITY_APPROVED, PUBLISHING_COMPLETED, PUBLISHING_FAILED, LEARNING_RECOMMENDATION, EXPERIMENT_COMPLETED, RETRY_REQUESTED, MANUAL_TRIGGER, WEBHOOK_TRIGGER
    source_component: str
    source_package_id: Optional[str] = None
    target_platform: str = "all"
    event_data: Dict[str, Any] = Field(default_factory=dict)
    triggered_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class TriggerManager:
    """Trigger Manager intercepting events from EventBus and registering trigger instances."""

    def __init__(self) -> None:
        self._history: List[TriggerEvent] = []
        event_bus.subscribe("*", self._handle_event_bus_msg)

    async def _handle_event_bus_msg(self, msg: EventMessage) -> None:
        trig = TriggerEvent(
            trigger_id=msg.event_id,
            trigger_type=msg.event_type,
            source_component=msg.source,
            source_package_id=msg.payload.get("package_id"),
            target_platform=msg.payload.get("target_platform", "all"),
            event_data=msg.payload,
            triggered_at=msg.timestamp
        )
        self._history.append(trig)
        logger.info(f"[TriggerManager] Registered TriggerEvent '{trig.trigger_type}' (ID: {trig.trigger_id})")

    def register_manual_trigger(
        self, 
        trigger_type: str = "MANUAL_TRIGGER", 
        source_package_id: Optional[str] = None, 
        target_platform: str = "all", 
        event_data: Optional[Dict[str, Any]] = None
    ) -> TriggerEvent:
        trig = TriggerEvent(
            trigger_id=str(uuid.uuid4()),
            trigger_type=trigger_type,
            source_component="ManualUserRequest",
            source_package_id=source_package_id,
            target_platform=target_platform,
            event_data=event_data or {}
        )
        self._history.append(trig)
        return trig

    def list_triggers(self, limit: int = 50) -> List[TriggerEvent]:
        return self._history[-limit:]

trigger_manager = TriggerManager()
ZOOMING = "zoom"
