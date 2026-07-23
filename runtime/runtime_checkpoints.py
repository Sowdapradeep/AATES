"""
runtime/runtime_checkpoints.py — Persistent workflow checkpoints.

Every workflow records:
  - Current Step
  - Current Assets
  - Current Budget
  - Current Decision
  - Current Memory
  - Current Queue position

If runtime stops, the system resumes from the last checkpoint.
Completed steps are NEVER regenerated.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("aros.checkpoints")


class CheckpointStore:
    """
    In-process checkpoint store.

    Interface designed for migration to DynamoDB / S3 without
    changing the read/write API.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._writes = 0
        self._reads = 0

    # ── Write ─────────────────────────────────────────────────────────────────

    def save(
        self,
        workflow_id: str,
        step: int,
        assets: list[dict[str, Any]],
        budget_spent_usd: float,
        decision: str,
        memory: dict[str, Any],
        queue_position: int = 0,
    ) -> None:
        checkpoint = {
            "workflow_id": workflow_id,
            "step": step,
            "assets": assets,
            "budget_spent_usd": budget_spent_usd,
            "decision": decision,
            "memory": memory,
            "queue_position": queue_position,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._store[workflow_id] = checkpoint
        self._writes += 1
        logger.debug("Checkpoint saved: %s (step=%d)", workflow_id, step)

    # ── Read ──────────────────────────────────────────────────────────────────

    def load(self, workflow_id: str) -> dict[str, Any] | None:
        cp = self._store.get(workflow_id)
        if cp:
            self._reads += 1
            logger.debug("Checkpoint loaded: %s (step=%d)", workflow_id, cp.get("step"))
        return cp

    def exists(self, workflow_id: str) -> bool:
        return workflow_id in self._store

    def delete(self, workflow_id: str) -> bool:
        removed = self._store.pop(workflow_id, None)
        return removed is not None

    # ── Listing ───────────────────────────────────────────────────────────────

    def list_all(self) -> list[dict[str, Any]]:
        return [
            {
                "workflow_id": cp["workflow_id"],
                "step": cp["step"],
                "saved_at": cp["saved_at"],
            }
            for cp in self._store.values()
        ]

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        return {
            "stored": len(self._store),
            "total_writes": self._writes,
            "total_reads": self._reads,
        }

    # ── Export / replay helpers ───────────────────────────────────────────────

    def export_json(self, workflow_id: str) -> str | None:
        cp = self._store.get(workflow_id)
        if not cp:
            return None
        return json.dumps(cp, indent=2)


# Module-level singleton
checkpoint_store = CheckpointStore()
