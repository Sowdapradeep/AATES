import logging
from datetime import UTC, datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("orchestrator_scheduler")

class ResourceReservation(BaseModel):
    reservation_id: str
    resource_type: str  # GPU, WORKER_SLOT, API_QUOTA, PUBLISHING_WINDOW
    allocated_to_node: str
    granted_at: str = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None).isoformat())
    status: str = "ACTIVE"

class SchedulingEngine:
    """Scheduling Engine managing worker slots, GPU allocation, provider quotas, publishing windows, and rate limits."""

    def __init__(self) -> None:
        self._reservations: Dict[str, ResourceReservation] = {}
        self.available_gpu_slots = 2
        self.available_worker_slots = 8

    def reserve_resources(self, node_id: str, resource_requirements: Dict[str, bool]) -> Optional[ResourceReservation]:
        import uuid
        res_type = "WORKER_SLOT"
        if resource_requirements.get("gpu"):
            if self.available_gpu_slots <= 0:
                logger.warning(f"[SchedulingEngine] GPU slots exhausted for node '{node_id}'")
                return None
            self.available_gpu_slots -= 1
            res_type = "GPU"
        else:
            if self.available_worker_slots <= 0:
                logger.warning(f"[SchedulingEngine] Worker slots exhausted for node '{node_id}'")
                return None
            self.available_worker_slots -= 1

        res = ResourceReservation(
            reservation_id=str(uuid.uuid4()),
            resource_type=res_type,
            allocated_to_node=node_id
        )
        self._reservations[res.reservation_id] = res
        logger.info(f"[SchedulingEngine] Granted {res_type} reservation '{res.reservation_id}' to node '{node_id}'")
        return res

    def release_reservation(self, reservation_id: str) -> None:
        if reservation_id in self._reservations:
            res = self._reservations[reservation_id]
            if res.resource_type == "GPU":
                self.available_gpu_slots += 1
            else:
                self.available_worker_slots += 1
            del self._reservations[reservation_id]
            logger.info(f"[SchedulingEngine] Released reservation '{reservation_id}'")

scheduling_engine = SchedulingEngine()
ZOOMING = "zoom"
