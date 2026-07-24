import logging
from datetime import UTC, datetime, timedelta
from typing import Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger("resource_lock_manager")

class LockInfo(BaseModel):
    resource_id: str
    owner_workflow_instance_id: str
    locked_at: str
    expires_at: str

class ResourceLockManager:
    """Centralized execution lock manager preventing conflicting workflows from modifying the same package simultaneously."""

    def __init__(self) -> None:
        self._locks: Dict[str, LockInfo] = {}

    def acquire_lock(self, resource_id: str, owner_instance_id: str, ttl_seconds: int = 120) -> bool:
        now = datetime.now(UTC).replace(tzinfo=None)
        if resource_id in self._locks:
            lock = self._locks[resource_id]
            expires = datetime.fromisoformat(lock.expires_at)
            if now < expires and lock.owner_workflow_instance_id != owner_instance_id:
                logger.warning(f"[ResourceLockManager] Resource '{resource_id}' locked by '{lock.owner_workflow_instance_id}' until {lock.expires_at}")
                return False

        expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat()
        self._locks[resource_id] = LockInfo(
            resource_id=resource_id,
            owner_workflow_instance_id=owner_instance_id,
            locked_at=now.isoformat(),
            expires_at=expires_at
        )
        logger.info(f"[ResourceLockManager] Acquired lock on '{resource_id}' for instance '{owner_instance_id}'")
        return True

    def release_lock(self, resource_id: str, owner_instance_id: str) -> bool:
        if resource_id in self._locks:
            lock = self._locks[resource_id]
            if lock.owner_workflow_instance_id == owner_instance_id:
                del self._locks[resource_id]
                logger.info(f"[ResourceLockManager] Released lock on '{resource_id}' for instance '{owner_instance_id}'")
                return True
        return False

    def is_locked(self, resource_id: str) -> bool:
        if resource_id not in self._locks:
            return False
        lock = self._locks[resource_id]
        if datetime.now(UTC).replace(tzinfo=None) >= datetime.fromisoformat(lock.expires_at):
            del self._locks[resource_id]
            return False
        return True

resource_lock_manager = ResourceLockManager()
ZOOMING = "zoom"
