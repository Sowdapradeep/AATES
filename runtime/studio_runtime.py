"""
runtime/studio_runtime.py — AROS Operating Kernel

StudioRuntime is the single boot point for the entire AATES platform.
It initialises every subsystem in the correct dependency order, then
hands off to the ContinuousRuntimeLoop which runs perpetually.

Boot sequence:
  1. Configuration
  2. Logging
  3. Memory (strategic / lifelong / world-model)
  4. Autonomous modules (decision engine, mission, goal engine)
  5. Providers
  6. Scheduler
  7. Workers
  8. Event bus
  9. Monitoring / telemetry
  10. API (if run in-process)
  11. Continuous loop
"""
from __future__ import annotations

import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("aros.studio_runtime")


class StudioRuntime:
    """
    AROS Operating Kernel.

    Usage (programmatic)::

        runtime = StudioRuntime()
        asyncio.run(runtime.boot())
    """

    VERSION = "12.0.0"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = config or {}
        self.started_at: datetime | None = None
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Sub-system handles (populated during boot)
        self.scheduler: Any = None
        self.goal_dispatcher: Any = None
        self.workflow_runtime: Any = None
        self.worker_runtime: Any = None
        self.queue: Any = None
        self.supervisor: Any = None
        self.trigger_engine: Any = None
        self.telemetry: Any = None
        self.loop_task: asyncio.Task | None = None

    # ── Boot ──────────────────────────────────────────────────────────────────

    async def boot(self) -> None:
        """Full platform boot. Blocks until shutdown is signalled."""
        logger.info("AROS v%s — boot sequence initiated", self.VERSION)
        self.started_at = datetime.now(timezone.utc)

        await self._init_config()
        await self._init_memory()
        await self._init_autonomy()
        await self._init_providers()
        await self._init_queue()
        await self._init_workers()
        await self._init_scheduler()
        await self._init_event_bus()
        await self._init_telemetry()
        await self._init_supervisor()
        await self._init_trigger_engine()

        self._running = True
        self._register_signals()
        logger.info("AROS boot complete — runtime is live")

        # Start the continuous loop
        from runtime.continuous_loop import ContinuousRuntimeLoop
        loop = ContinuousRuntimeLoop(self)
        self.loop_task = asyncio.create_task(loop.run(), name="aros.continuous_loop")

        await self._shutdown_event.wait()
        await self._shutdown()

    # ── Initialisation steps ──────────────────────────────────────────────────

    async def _init_config(self) -> None:
        logger.info("[1/11] Loading configuration")
        try:
            from core.config import settings
            self.config.setdefault("app_name", settings.app.name)
        except Exception:
            self.config.setdefault("app_name", "AATES")
        logger.info("  app_name=%s", self.config["app_name"])

    async def _init_memory(self) -> None:
        logger.info("[2/11] Initialising memory subsystems")
        from brain.autonomy.world_model import world_model
        from brain.autonomy.strategic_memory import strategic_memory
        from brain.autonomy.lifelong_memory import lifelong_memory
        self.world_model = world_model
        self.strategic_memory = strategic_memory
        self.lifelong_memory = lifelong_memory
        logger.info("  WorldModel / StrategicMemory / LifelongMemory — ready")

    async def _init_autonomy(self) -> None:
        logger.info("[3/11] Initialising autonomous decision layer")
        from brain.autonomy.decision_engine import autonomous_decision_engine
        from brain.autonomy.mission_engine import mission_engine
        from brain.autonomy.goal_engine import AutonomousGoalEngine
        self.decision_engine = autonomous_decision_engine
        self.mission_engine = mission_engine
        self.goal_engine = AutonomousGoalEngine(autonomous_decision_engine, mission_engine)
        logger.info("  DecisionEngine / MissionEngine / GoalEngine — ready")

    async def _init_providers(self) -> None:
        logger.info("[4/11] Warming provider connections")
        try:
            from providers.bedrock.client import get_bedrock_client
            get_bedrock_client()
            logger.info("  Amazon Bedrock — connected")
        except Exception as exc:
            logger.warning("  Amazon Bedrock warm-up skipped: %s", exc)

    async def _init_queue(self) -> None:
        logger.info("[5/11] Initialising distributed queue")
        from runtime.distributed_queue import DistributedQueue
        self.queue = DistributedQueue()
        await self.queue.connect()
        logger.info("  DistributedQueue — ready (backend=%s)", self.queue.backend)

    async def _init_workers(self) -> None:
        logger.info("[6/11] Starting worker runtime")
        from runtime.worker_runtime import WorkerRuntime
        self.worker_runtime = WorkerRuntime(self.queue)
        await self.worker_runtime.start_all()
        logger.info("  WorkerRuntime — %d workers active", len(self.worker_runtime.workers))

    async def _init_scheduler(self) -> None:
        logger.info("[7/11] Initialising autonomous scheduler")
        from runtime.autonomous_scheduler import AutonomousScheduler
        self.scheduler = AutonomousScheduler(
            decision_engine=self.decision_engine,
            queue=self.queue,
        )
        logger.info("  AutonomousScheduler — ready")

    async def _init_event_bus(self) -> None:
        logger.info("[8/11] Initialising event bus")
        from runtime.event_bus import EventBus
        self.event_bus = EventBus()
        logger.info("  EventBus — ready")

    async def _init_telemetry(self) -> None:
        logger.info("[9/11] Initialising runtime telemetry")
        from runtime.runtime_telemetry import RuntimeTelemetry
        self.telemetry = RuntimeTelemetry(self)
        logger.info("  RuntimeTelemetry — ready")

    async def _init_supervisor(self) -> None:
        logger.info("[10/11] Starting runtime supervisor")
        from runtime.runtime_supervisor import RuntimeSupervisor
        self.supervisor = RuntimeSupervisor(
            worker_runtime=self.worker_runtime,
            queue=self.queue,
            telemetry=self.telemetry,
        )
        logger.info("  RuntimeSupervisor — ready")

    async def _init_trigger_engine(self) -> None:
        logger.info("[11/11] Starting autonomous trigger engine")
        from runtime.autonomous_trigger_engine import AutonomousTriggerEngine
        self.trigger_engine = AutonomousTriggerEngine(
            mission_engine=self.mission_engine,
            goal_engine=self.goal_engine,
            scheduler=self.scheduler,
            decision_engine=self.decision_engine,
        )
        logger.info("  AutonomousTriggerEngine — ready")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _register_signals(self) -> None:
        """Register SIGINT / SIGTERM for graceful shutdown."""
        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self._request_shutdown)

    def _request_shutdown(self) -> None:
        logger.info("AROS shutdown requested")
        self._shutdown_event.set()

    async def _shutdown(self) -> None:
        self._running = False
        logger.info("AROS graceful shutdown initiated")
        if self.loop_task and not self.loop_task.done():
            self.loop_task.cancel()
        if self.worker_runtime:
            await self.worker_runtime.stop_all()
        logger.info("AROS shutdown complete")

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        uptime_sec: float | None = None
        if self.started_at:
            uptime_sec = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        return {
            "version": self.VERSION,
            "running": self._running,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "uptime_sec": uptime_sec,
            "workers": self.worker_runtime.get_status() if self.worker_runtime else {},
            "queue": self.queue.get_status() if self.queue else {},
            "scheduler": self.scheduler.get_status() if self.scheduler else {},
        }


# Module-level singleton — import this anywhere in the platform
studio_runtime = StudioRuntime()
