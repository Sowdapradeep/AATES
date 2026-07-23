"""
Runtime API Router — AROS operational endpoints.

Prefix: /v1/runtime

Routes:
  GET  /v1/runtime/status
  GET  /v1/runtime/workers
  GET  /v1/runtime/queues
  GET  /v1/runtime/checkpoints
  GET  /v1/runtime/scheduler
  POST /v1/runtime/replay
  GET  /v1/runtime/supervisor
  GET  /v1/runtime/metrics
"""
from __future__ import annotations

from fastapi import APIRouter
from typing import Any

router = APIRouter(prefix="/v1/runtime", tags=["Runtime"])


def _get_runtime() -> Any:
    """Return the studio_runtime singleton (imported lazily to avoid circular imports)."""
    from runtime.studio_runtime import studio_runtime
    return studio_runtime


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status")
def get_runtime_status() -> dict[str, Any]:
    """Full AROS runtime status."""
    rt = _get_runtime()
    return rt.get_status()


# ── Workers ───────────────────────────────────────────────────────────────────

@router.get("/workers")
def get_workers() -> dict[str, Any]:
    """Status of all long-running workers."""
    rt = _get_runtime()
    if rt.worker_runtime:
        return rt.worker_runtime.get_status()
    return {"workers": {}}


@router.post("/workers/{worker_type}/restart")
async def restart_worker(worker_type: str) -> dict[str, Any]:
    """Manually restart a specific worker (supervisor also does this automatically)."""
    rt = _get_runtime()
    if rt.worker_runtime:
        success = await rt.worker_runtime.restart(worker_type)
        return {"restarted": success, "worker_type": worker_type}
    return {"restarted": False}


# ── Queues ────────────────────────────────────────────────────────────────────

@router.get("/queues")
def get_queues() -> dict[str, Any]:
    """Distributed queue status."""
    rt = _get_runtime()
    if rt.queue:
        return rt.queue.get_status()
    return {"status": "not_initialized"}


@router.post("/queues/push")
def push_queue_job(payload: dict) -> dict[str, Any]:
    """Manually push a job to the queue (for testing / override)."""
    rt = _get_runtime()
    if rt.queue:
        job = rt.queue.push(
            job_type=payload.get("job_type", "generic"),
            payload=payload,
            priority=payload.get("priority", 5),
        )
        return {"job_id": job.job_id, "status": "queued"}
    return {"status": "queue_not_initialized"}


# ── Checkpoints ───────────────────────────────────────────────────────────────

@router.get("/checkpoints")
def get_checkpoints() -> dict[str, Any]:
    """List all active workflow checkpoints."""
    from runtime.runtime_checkpoints import checkpoint_store
    return {
        "checkpoints": checkpoint_store.list_all(),
        "stats": checkpoint_store.get_status(),
    }


@router.get("/checkpoints/{workflow_id}")
def get_checkpoint(workflow_id: str) -> dict[str, Any]:
    """Get a specific workflow checkpoint for replay or inspection."""
    from runtime.runtime_checkpoints import checkpoint_store
    cp = checkpoint_store.load(workflow_id)
    if not cp:
        return {"found": False, "workflow_id": workflow_id}
    return {"found": True, "checkpoint": cp}


# ── Scheduler ─────────────────────────────────────────────────────────────────

@router.get("/scheduler")
def get_scheduler() -> dict[str, Any]:
    """Autonomous scheduler status and upcoming jobs."""
    rt = _get_runtime()
    if rt.scheduler:
        return rt.scheduler.get_status()
    return {"status": "not_initialized"}


# ── Replay ────────────────────────────────────────────────────────────────────

@router.post("/replay")
async def replay_workflow(payload: dict) -> dict[str, Any]:
    """
    Replay a workflow from its checkpoint.

    Supports replaying:
      - workflow_id: specific workflow
      - episode_id: specific episode
      - universe_id: all workflows in a universe
    """
    from runtime.workflow_runtime import WorkflowRuntime
    from runtime.runtime_checkpoints import checkpoint_store

    workflow_id = payload.get("workflow_id")
    if not workflow_id:
        return {"error": "workflow_id required"}

    cp = checkpoint_store.load(workflow_id)
    if not cp:
        return {"error": f"no checkpoint for {workflow_id}"}

    wfr = WorkflowRuntime()
    spec = cp.get("memory", {}).get("spec", {})
    spec["workflow_id"] = workflow_id
    state = await wfr.execute(spec)
    return {
        "replayed": True,
        "workflow_id": workflow_id,
        "status": state.status,
        "steps_completed": state.current_step,
    }


# ── Supervisor ────────────────────────────────────────────────────────────────

@router.get("/supervisor")
def get_supervisor_status() -> dict[str, Any]:
    """Runtime supervisor health events and worker restart history."""
    rt = _get_runtime()
    if rt.supervisor:
        return rt.supervisor.get_status()
    return {"status": "not_initialized"}


@router.post("/supervisor/health-check")
async def run_health_check() -> dict[str, Any]:
    """Manually trigger a supervisor health check cycle."""
    rt = _get_runtime()
    if rt.supervisor:
        return await rt.supervisor.health_check()
    return {"status": "supervisor_not_initialized"}


# ── Metrics ───────────────────────────────────────────────────────────────────

@router.get("/metrics")
def get_runtime_metrics() -> dict[str, Any]:
    """Live runtime telemetry: CPU, memory, queue, workers, Bedrock, costs."""
    rt = _get_runtime()
    if rt.telemetry:
        return rt.telemetry.get_metrics()
    return {"status": "telemetry_not_initialized"}
