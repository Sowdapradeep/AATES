"""
runtime/autonomous_scheduler.py — Time / Goal / Event / Budget-aware Scheduler.

No human trigger required. The scheduler evaluates:
  - Time-based rules (e.g. publish every 3 days)
  - Goal-based rules (active goals needing episodes)
  - Event-based rules (milestone reached, universe evolving)
  - Budget-aware rules (don't schedule if budget exhausted)
  - Resource-aware rules (don't schedule if all workers busy)
  - Retry / delayed / backoff scheduling
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

logger = logging.getLogger("aros.scheduler")


class ScheduledJob:
    """A single scheduled work item."""

    def __init__(
        self,
        job_id: str,
        job_type: str,
        payload: dict[str, Any],
        run_at: datetime,
        priority: int = 5,
        max_retries: int = 3,
    ) -> None:
        self.job_id = job_id
        self.job_type = job_type
        self.payload = payload
        self.run_at = run_at
        self.priority = priority
        self.max_retries = max_retries
        self.attempt = 0
        self.status = "pending"   # pending | running | done | failed | delayed
        self.created_at = datetime.now(timezone.utc)

    def is_due(self) -> bool:
        return datetime.now(timezone.utc) >= self.run_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "run_at": self.run_at.isoformat(),
            "priority": self.priority,
            "attempt": self.attempt,
            "status": self.status,
        }


class AutonomousScheduler:
    """
    Budget-aware, resource-aware autonomous scheduler.

    All work enters through `schedule()`.
    Due jobs are returned by `drain_due()` which the ContinuousRuntimeLoop calls
    each cycle.
    """

    def __init__(
        self,
        decision_engine: Any,
        queue: Any,
        budget_limit_usd: float = 5.0,
        max_concurrent: int = 4,
    ) -> None:
        self.decision_engine = decision_engine
        self.queue = queue
        self.budget_limit_usd = budget_limit_usd
        self.max_concurrent = max_concurrent

        self._jobs: list[ScheduledJob] = []
        self._job_counter = 0
        self._completed: list[str] = []
        self._failed: list[str] = []
        self._current_spend_usd: float = 0.0
        self._retry_delays = [30, 120, 600]  # seconds: 30s, 2min, 10min

    def _next_id(self) -> str:
        self._job_counter += 1
        return f"job-{self._job_counter:06d}"

    # ── Scheduling types ──────────────────────────────────────────────────────

    def schedule(self, payload: dict[str, Any], delay_sec: int = 0) -> ScheduledJob:
        """Schedule an immediate (or delayed) job."""
        run_at = datetime.now(timezone.utc) + timedelta(seconds=delay_sec)
        job = ScheduledJob(
            job_id=self._next_id(),
            job_type=payload.get("type", "production"),
            payload=payload,
            run_at=run_at,
            priority=payload.get("priority", 5),
        )
        self._jobs.append(job)
        logger.info("Scheduled %s type=%s delay=%ds", job.job_id, job.job_type, delay_sec)
        return job

    def schedule_goal(self, goal: dict[str, Any]) -> ScheduledJob:
        """Schedule production driven by an active goal."""
        return self.schedule({
            "type": "goal_production",
            "goal_id": goal.get("goal_id"),
            "objective": goal.get("objective"),
            "priority": 7,
        })

    def schedule_retry(self, job: ScheduledJob) -> ScheduledJob | None:
        """Retry a failed job with exponential backoff."""
        if job.attempt >= job.max_retries:
            job.status = "failed"
            self._failed.append(job.job_id)
            logger.warning("Job %s exhausted retries — moved to dead-letter", job.job_id)
            return None
        delay = self._retry_delays[min(job.attempt, len(self._retry_delays) - 1)]
        retry_payload = {**job.payload, "_retry_of": job.job_id, "attempt": job.attempt + 1}
        new_job = self.schedule(retry_payload, delay_sec=delay)
        new_job.attempt = job.attempt + 1
        logger.info("Retry scheduled: %s → %s (delay=%ds)", job.job_id, new_job.job_id, delay)
        return new_job

    def schedule_time_based(self, interval_hours: int, payload: dict[str, Any]) -> None:
        """Schedule a recurring job (called once per loop; adds if slot is empty)."""
        active_types = {j.job_type for j in self._jobs if j.status == "pending"}
        if payload.get("type") not in active_types:
            self.schedule(payload, delay_sec=0)

    # ── Budget / resource guard ───────────────────────────────────────────────

    def _budget_ok(self, estimated_cost_usd: float = 0.5) -> bool:
        return (self._current_spend_usd + estimated_cost_usd) <= self.budget_limit_usd

    def _capacity_ok(self) -> bool:
        running = sum(1 for j in self._jobs if j.status == "running")
        return running < self.max_concurrent

    def record_spend(self, amount_usd: float) -> None:
        self._current_spend_usd += amount_usd

    # ── Drain ─────────────────────────────────────────────────────────────────

    def drain_due(self) -> list[ScheduledJob]:
        """Return all jobs that are due, pass budget/capacity guards, and mark running."""
        due = []
        for job in self._jobs:
            if job.status != "pending":
                continue
            if not job.is_due():
                continue
            if not self._budget_ok():
                logger.warning("Budget limit reached — deferring %s", job.job_id)
                continue
            if not self._capacity_ok():
                logger.debug("Capacity full — deferring %s", job.job_id)
                continue
            job.status = "running"
            due.append(job)
        return sorted(due, key=lambda j: j.priority, reverse=True)

    def complete(self, job_id: str, cost_usd: float = 0.0) -> None:
        for job in self._jobs:
            if job.job_id == job_id:
                job.status = "done"
                self._completed.append(job_id)
                self.record_spend(cost_usd)
                break

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        pending = [j for j in self._jobs if j.status == "pending"]
        running = [j for j in self._jobs if j.status == "running"]
        return {
            "pending": len(pending),
            "running": len(running),
            "completed": len(self._completed),
            "failed": len(self._failed),
            "budget_spent_usd": round(self._current_spend_usd, 4),
            "budget_limit_usd": self.budget_limit_usd,
            "next_job": pending[0].to_dict() if pending else None,
        }
