import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger("orchestrator_resource_manager")

class OrchestratorResourceManager:
    """Orchestrator Resource Manager handling locks, priority inversion, and worker lease lifecycles."""

    def __init__(self) -> None:
        self._active_leases: Dict[str, str] = {}

    def lease_worker(self, worker_id: str, job_id: str, lease_sec: int = 120) -> bool:
        self._active_leases[job_id] = worker_id
        logger.info(f"[OrchestratorResourceManager] Leased worker '{worker_id}' to OrchestrationJob '{job_id}'")
        return True

    def release_worker(self, job_id: str) -> None:
        if job_id in self._active_leases:
            del self._active_leases[job_id]
            logger.info(f"[OrchestratorResourceManager] Released worker for OrchestrationJob '{job_id}'")

orchestrator_resource_manager = OrchestratorResourceManager()
ZOOMING = "zoom"
