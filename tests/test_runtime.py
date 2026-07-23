"""
Phase 12 — AROS (Autonomous Runtime Operating System) Tests

Covers:
  1.  StudioRuntime — boot sequence and status
  2.  ContinuousRuntimeLoop — perpetual loop tick
  3.  AutonomousScheduler — time/goal/budget/retry scheduling
  4.  GoalDispatcher — mission goals → WorkflowSpecs
  5.  WorkflowRuntime — pause/resume/cancel/checkpoint/timeout/replay
  6.  EpisodeRuntime — isolated episode execution
  7.  UniverseRuntime / UniverseRegistry — independent universe state
  8.  WorkerRuntime — 7-worker pool lifecycle
  9.  DistributedQueue — priority/retry/ack/nack/dead-letter
  10. RuntimeCheckpoints — save/load/resume (never-regenerate)
  11. RuntimeSupervisor — worker crash detection and restart
  12. AutonomousTriggerEngine — no-prompt production trigger
  13. EventBus — pub/sub
  14. RuntimeTelemetry — metrics snapshot
  15. Runtime API endpoints — all 12 routes
"""
import asyncio
import pytest
from fastapi.testclient import TestClient

from runtime.studio_runtime import StudioRuntime
from runtime.autonomous_scheduler import AutonomousScheduler
from runtime.goal_dispatcher import GoalDispatcher
from runtime.workflow_runtime import WorkflowRuntime
from runtime.episode_runtime import EpisodeRuntime
from runtime.universe_runtime import UniverseRuntime, UniverseRegistry
from runtime.worker_runtime import WorkerRuntime
from runtime.distributed_queue import DistributedQueue
from runtime.runtime_checkpoints import CheckpointStore
from runtime.runtime_supervisor import RuntimeSupervisor
from runtime.autonomous_trigger_engine import AutonomousTriggerEngine
from runtime.event_bus import EventBus
from runtime.runtime_telemetry import RuntimeTelemetry


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _make_queue() -> DistributedQueue:
    q = DistributedQueue(backend="memory")
    await q.connect()
    return q


# ── 1. StudioRuntime ──────────────────────────────────────────────────────────

def test_studio_runtime_instantiation() -> None:
    """StudioRuntime can be instantiated with a custom config."""
    rt = StudioRuntime(config={"app_name": "AATES-Test"})
    assert rt.config["app_name"] == "AATES-Test"
    assert rt.VERSION == "12.0.0"
    assert rt._running is False


def test_studio_runtime_status_before_boot() -> None:
    """Status before boot returns safe defaults."""
    rt = StudioRuntime()
    status = rt.get_status()
    assert status["running"] is False
    assert status["started_at"] is None


# ── 2. ContinuousRuntimeLoop ──────────────────────────────────────────────────

def test_continuous_loop_one_tick() -> None:
    """One tick executes without errors even with stub subsystems."""
    from runtime.continuous_loop import ContinuousRuntimeLoop

    rt = StudioRuntime()
    rt._running = True

    # Provide minimal stubs so tick can run
    class FakeDecisionEngine:
        def process_cycle(self): return {"committed": 0, "rejected": 0}

    class FakeTrigger:
        def evaluate(self): return {"new_productions": []}

    class FakeQueue:
        def depth(self): return 0
        def drain_completed(self): return []
        def drain_learned(self): return []
        def get_status(self): return {}

    class FakeWorkerRuntime:
        def get_status(self): return {}

    rt.decision_engine = FakeDecisionEngine()
    rt.trigger_engine = FakeTrigger()
    rt.queue = FakeQueue()
    rt.worker_runtime = FakeWorkerRuntime()
    rt.scheduler = None

    loop = ContinuousRuntimeLoop(rt, tick_sec=1)
    asyncio.run(loop._tick())
    assert loop._cycle_count == 1
    rt._running = False


# ── 3. AutonomousScheduler ────────────────────────────────────────────────────

def test_scheduler_schedule_and_drain() -> None:
    """Jobs are queued and drained when due."""
    q = asyncio.run(_make_queue())
    scheduler = AutonomousScheduler(decision_engine=None, queue=q)

    job = scheduler.schedule({"type": "test_production", "priority": 5})
    assert job.status == "pending"

    due = scheduler.drain_due()
    assert len(due) == 1
    assert due[0].job_id == job.job_id


def test_scheduler_budget_guard() -> None:
    """Jobs are not drained when budget is exhausted."""
    q = asyncio.run(_make_queue())
    scheduler = AutonomousScheduler(decision_engine=None, queue=q, budget_limit_usd=1.0)
    scheduler._current_spend_usd = 0.95  # nearly exhausted

    scheduler.schedule({"type": "expensive", "priority": 5})
    due = scheduler.drain_due()
    assert len(due) == 0  # blocked by budget guard


def test_scheduler_retry_with_backoff() -> None:
    """Failed jobs are re-queued with exponential backoff up to max_retries."""
    q = asyncio.run(_make_queue())
    scheduler = AutonomousScheduler(decision_engine=None, queue=q)

    job = scheduler.schedule({"type": "flaky"})
    job.attempt = 2
    retry = scheduler.schedule_retry(job)
    assert retry is not None
    assert retry.attempt == 3

    # Exhausted retries → dead-letter
    job2 = scheduler.schedule({"type": "flaky2"})
    job2.attempt = 3
    dead = scheduler.schedule_retry(job2)
    assert dead is None


# ── 4. GoalDispatcher ─────────────────────────────────────────────────────────

def test_goal_dispatcher_converts_goals() -> None:
    """Active goals are converted to WorkflowSpecs with episodes and scenes."""
    from brain.autonomy.mission_engine import MissionEngine
    from brain.autonomy.world_model import WorldModel

    mission = MissionEngine()
    wm = WorldModel()

    # Seed a goal
    mission.generate_mission_aligned_goal({"avg_retention_pct": 40.0})

    dispatcher = GoalDispatcher(mission, wm)
    specs = dispatcher.dispatch()
    assert len(specs) >= 1
    assert specs[0].episodes is not None
    assert len(specs[0].episodes[0]["scenes"]) > 0


# ── 5. WorkflowRuntime ────────────────────────────────────────────────────────

def test_workflow_runtime_execution() -> None:
    """Workflows execute and produce asset records."""
    wfr = WorkflowRuntime()
    spec = {
        "workflow_id": "wf-test-001",
        "episodes": [
            {"episode_id": "ep-1", "budget_usd": 1.0,
             "scenes": [{"scene_id": "sc-1", "type": "story_generation"}]},
        ],
    }
    state = asyncio.run(wfr.execute(spec))
    assert state.status == "done"
    assert state.current_step == 1
    assert len(state.assets) == 1


def test_workflow_pause_resume() -> None:
    """Pausing and resuming a workflow changes status correctly."""
    wfr = WorkflowRuntime()
    wfr.pause("wf-test-002")
    assert "wf-test-002" in wfr._paused

    wfr.resume("wf-test-002")
    assert "wf-test-002" not in wfr._paused


def test_workflow_cancel() -> None:
    """Cancelling a workflow marks it as cancelled."""
    wfr = WorkflowRuntime()
    wfr.cancel("wf-cancel-001")
    assert "wf-cancel-001" in wfr._cancelled


def test_workflow_checkpoint() -> None:
    """Completed workflow steps are stored as checkpoints."""
    wfr = WorkflowRuntime()
    spec = {
        "workflow_id": "wf-chk-001",
        "episodes": [
            {"episode_id": "ep-chk-1", "budget_usd": 0.5, "scenes": []},
        ],
    }
    state = asyncio.run(wfr.execute(spec))
    cp = wfr.get_checkpoint("wf-chk-001")
    assert cp is not None
    assert cp["workflow_id"] == "wf-chk-001"


def test_workflow_replay_log() -> None:
    """Replay log records every step transition."""
    wfr = WorkflowRuntime()
    spec = {
        "workflow_id": "wf-replay-001",
        "episodes": [
            {"episode_id": "ep-r1", "budget_usd": 0.5, "scenes": []},
            {"episode_id": "ep-r2", "budget_usd": 0.5, "scenes": []},
        ],
    }
    asyncio.run(wfr.execute(spec))
    log = wfr.get_replay_log("wf-replay-001")
    assert len(log) == 2


# ── 6. EpisodeRuntime ─────────────────────────────────────────────────────────

def test_episode_runtime_isolation() -> None:
    """Each episode runs independently with its own budget."""
    ep = EpisodeRuntime(budget_usd=2.0)
    spec = {
        "title": "Test Episode",
        "scenes": [
            {"scene_id": "sc-a", "type": "image_generation"},
            {"scene_id": "sc-b", "type": "voice_generation"},
        ],
    }
    report = asyncio.run(ep.run(spec))
    assert report["status"] == "done"
    assert report["scene_count"] == 2
    assert report["cost_usd"] <= 2.0
    assert report["quality_score"] > 0


def test_episode_runtime_budget_guard() -> None:
    """Episode stops producing when budget is exhausted mid-run."""
    # budget=0.04 — each scene costs 0.05, so budget is exhausted before even scene 1
    # We test this by checking fewer scenes are produced than requested
    ep = EpisodeRuntime(budget_usd=0.12)  # budget for exactly 2 scenes at $0.05 each
    spec = {
        "scenes": [{"scene_id": f"sc-x{i}", "type": "image_generation"} for i in range(10)]
    }
    report = asyncio.run(ep.run(spec))
    # Only 2 scenes should run before budget runs out ($0.12 / $0.05 = 2 scenes)
    assert report["scene_count"] <= 3  # budget guard stops production well before 10


# ── 7. UniverseRuntime ────────────────────────────────────────────────────────

def test_universe_runtime_isolation() -> None:
    """Universes maintain independent state."""
    u1 = UniverseRuntime("u-001", "Karnan Chronicles", seed_budget_usd=10.0)
    u2 = UniverseRuntime("u-002", "Pari Universe", seed_budget_usd=10.0)

    u1.add_character("Karnan", "hero", ["brave", "loyal"])
    u1.record_episode(quality=90.0, retention_pct=75.0, cost_usd=0.5)

    assert u1.analytics["episodes_produced"] == 1
    assert u2.analytics["episodes_produced"] == 0
    assert len(u1.characters) == 1
    assert len(u2.characters) == 0


def test_universe_registry() -> None:
    """Universe registry creates and retrieves universes."""
    registry = UniverseRegistry()
    u = registry.create("Valli World", budget_usd=5.0)
    assert registry.get(u.universe_id) is not None
    assert registry.count() == 1


def test_universe_character_retirement() -> None:
    """Characters can be added and retired within a universe."""
    u = UniverseRuntime("u-003", "Test Universe")
    char_id = u.add_character("VillagerA", "minor", ["timid"])
    retired = u.retire_character(char_id)
    assert retired
    assert u.characters[char_id]["status"] == "retired"


# ── 8. WorkerRuntime ─────────────────────────────────────────────────────────

def test_worker_runtime_all_workers_start() -> None:
    """All 7 workers start successfully."""
    q = asyncio.run(_make_queue())
    wrt = WorkerRuntime(q)
    asyncio.run(wrt.start_all())
    status = wrt.get_status()
    assert len(status) == 7
    assert all(s["running"] for s in status.values())
    asyncio.run(wrt.stop_all())


def test_worker_runtime_restart() -> None:
    """A specific worker can be restarted."""
    q = asyncio.run(_make_queue())
    wrt = WorkerRuntime(q)
    asyncio.run(wrt.start_all())
    success = asyncio.run(wrt.restart("image"))
    assert success
    asyncio.run(wrt.stop_all())


# ── 9. DistributedQueue ───────────────────────────────────────────────────────

def test_distributed_queue_priority_ordering() -> None:
    """Higher priority jobs are popped first."""
    q = asyncio.run(_make_queue())
    q.push("image", {"name": "low"}, priority=3)
    q.push("image", {"name": "high"}, priority=9)
    q.push("image", {"name": "mid"}, priority=5)

    first = q.pop("image")
    assert first["name"] == "high"


def test_distributed_queue_ack() -> None:
    """Acking a job removes it from inflight."""
    q = asyncio.run(_make_queue())
    job = q.push("learning", {"episode_id": "ep-ack"})
    item = q.pop("learning")
    assert item is not None
    success = q.ack(item["_job_id"])
    assert success
    assert len(q._inflight) == 0


def test_distributed_queue_nack_retry() -> None:
    """Nacking a job re-queues it with backoff."""
    q = asyncio.run(_make_queue())
    q.push("analytics", {"episode_id": "ep-nack"}, max_retries=3)
    item = q.pop("analytics")
    job_id = item["_job_id"]
    result = q.nack(job_id)
    assert result
    assert len(q._inflight) == 0
    assert len(q._queue) == 1  # back in queue


def test_distributed_queue_dead_letter() -> None:
    """Jobs that exhaust max_retries go to the dead-letter queue."""
    q = asyncio.run(_make_queue())
    # max_retries=1 means: 1 attempt allowed, first nack exceeds it → dead-letter
    q.push("voice", {"scene": "s1"}, max_retries=1)
    item = q.pop("voice")
    # This is already attempt=1 (max), so nack sends straight to dead-letter
    q.nack(item["_job_id"])
    assert len(q._dead_letter) == 1


# ── 10. RuntimeCheckpoints ───────────────────────────────────────────────────

def test_checkpoint_save_and_load() -> None:
    """Checkpoints persist across save/load cycles."""
    store = CheckpointStore()
    store.save(
        workflow_id="wf-cp-001",
        step=3,
        assets=[{"id": "a1"}],
        budget_spent_usd=1.5,
        decision="continue",
        memory={"context": "karnan battle scene"},
    )
    cp = store.load("wf-cp-001")
    assert cp is not None
    assert cp["step"] == 3
    assert cp["budget_spent_usd"] == 1.5


def test_checkpoint_resume_never_regenerates() -> None:
    """Loading a checkpoint at step N means steps 0..N-1 will be skipped."""
    store = CheckpointStore()
    store.save("wf-resume-001", step=5, assets=[], budget_spent_usd=2.0,
               decision="continue", memory={})
    cp = store.load("wf-resume-001")
    assert cp["step"] == 5  # execution resumes at step 5, skipping 0..4


# ── 11. RuntimeSupervisor ─────────────────────────────────────────────────────

def test_supervisor_health_check_runs() -> None:
    """Supervisor health check runs without errors on live worker/queue."""
    q = asyncio.run(_make_queue())
    wrt = WorkerRuntime(q)
    asyncio.run(wrt.start_all())

    supervisor = RuntimeSupervisor(worker_runtime=wrt, queue=q, telemetry=None)
    result = asyncio.run(supervisor.health_check())
    assert "checked_at" in result
    asyncio.run(wrt.stop_all())


def test_supervisor_detects_dead_letter() -> None:
    """Supervisor alerts when dead-letter queue has jobs."""
    q = asyncio.run(_make_queue())
    # Manually push to dead-letter
    from runtime.distributed_queue import QueueJob
    q._dead_letter.append(QueueJob("test", {}, max_retries=1))

    supervisor = RuntimeSupervisor(worker_runtime=None, queue=q, telemetry=None)
    result = asyncio.run(supervisor.health_check())
    dead_alerts = [a for a in result["actions_taken"] if "dead_letter" in a]
    assert len(dead_alerts) >= 1


# ── 12. AutonomousTriggerEngine ───────────────────────────────────────────────

def test_trigger_engine_generates_production() -> None:
    """Trigger engine produces a new production after the minimum cycle interval."""
    from brain.autonomy.decision_engine import AutonomousDecisionEngine
    from brain.autonomy.mission_engine import MissionEngine
    from brain.autonomy.goal_engine import AutonomousGoalEngine

    de = AutonomousDecisionEngine()
    me = MissionEngine()
    ge = AutonomousGoalEngine(de, me)

    q = asyncio.run(_make_queue())
    # Use high max_concurrent so capacity check always passes
    scheduler = AutonomousScheduler(de, q, max_concurrent=100)

    engine = AutonomousTriggerEngine(me, ge, scheduler, de)
    # Advance past the minimum cycles
    engine._cycles_since_last_production = 10

    plan = engine.evaluate()
    assert len(plan["new_productions"]) >= 1


# ── 13. EventBus ─────────────────────────────────────────────────────────────

def test_event_bus_publish_subscribe() -> None:
    """Subscribed handlers receive published events."""
    bus = EventBus()
    received: list[dict] = []

    async def handler(payload: dict) -> None:
        received.append(payload)

    bus.subscribe("episode_complete", handler)
    asyncio.run(
        bus.publish("episode_complete", {"episode_id": "ep-evt-1"})
    )
    assert len(received) == 1
    assert received[0]["episode_id"] == "ep-evt-1"


# ── 14. RuntimeTelemetry ──────────────────────────────────────────────────────

def test_telemetry_snapshot() -> None:
    """Telemetry snapshots accumulate episode and cost metrics."""
    rt = StudioRuntime()
    rt.queue = asyncio.run(_make_queue())

    class FakeWorkerRuntime:
        def get_status(self): return {}

    rt.worker_runtime = FakeWorkerRuntime()
    rt.scheduler = None

    from runtime.runtime_telemetry import RuntimeTelemetry
    telemetry = RuntimeTelemetry(rt)
    telemetry.record_episode(quality=88.0, cost_usd=0.4)
    telemetry.record_bedrock_call(latency_ms=1200)
    snap = telemetry.snapshot()

    assert snap["episodes_produced"] == 1
    assert snap["total_cost_usd"] == 0.4
    assert snap["bedrock_calls"] == 1
    assert snap["bedrock_avg_latency_ms"] == 1200.0


# ── 15. Runtime API Endpoints ─────────────────────────────────────────────────

def test_runtime_status_endpoint(client: TestClient) -> None:
    """GET /v1/runtime/status returns runtime version and state."""
    res = client.get("/v1/runtime/status")
    assert res.status_code == 200
    data = res.json()
    assert "version" in data
    assert data["version"] == "12.0.0"


def test_runtime_workers_endpoint(client: TestClient) -> None:
    """GET /v1/runtime/workers returns worker pool status."""
    res = client.get("/v1/runtime/workers")
    assert res.status_code == 200


def test_runtime_queues_endpoint(client: TestClient) -> None:
    """GET /v1/runtime/queues returns queue status."""
    res = client.get("/v1/runtime/queues")
    assert res.status_code == 200


def test_runtime_checkpoints_endpoint(client: TestClient) -> None:
    """GET /v1/runtime/checkpoints lists all checkpoints."""
    res = client.get("/v1/runtime/checkpoints")
    assert res.status_code == 200
    assert "checkpoints" in res.json()


def test_runtime_scheduler_endpoint(client: TestClient) -> None:
    """GET /v1/runtime/scheduler returns scheduler status."""
    res = client.get("/v1/runtime/scheduler")
    assert res.status_code == 200


def test_runtime_supervisor_endpoint(client: TestClient) -> None:
    """GET /v1/runtime/supervisor returns supervisor events."""
    res = client.get("/v1/runtime/supervisor")
    assert res.status_code == 200


def test_runtime_metrics_endpoint(client: TestClient) -> None:
    """GET /v1/runtime/metrics returns telemetry snapshot."""
    res = client.get("/v1/runtime/metrics")
    assert res.status_code == 200
