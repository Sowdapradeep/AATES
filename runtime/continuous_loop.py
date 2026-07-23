"""
runtime/continuous_loop.py — Perpetual Observe→Think→Plan→Execute→Learn cycle.

The loop runs forever at a configurable tick rate.  It never terminates unless
the StudioRuntime signals a shutdown.  Each iteration:

  1. Observe  — collect world state, queue depths, analytics
  2. Think    — run the decision engine processing cycle
  3. Plan     — ask trigger engine if new productions should be started
  4. Schedule — push approved work into the scheduler
  5. Execute  — workers pull from the queue (autonomous)
  6. Review   — executive council post-episode reviews
  7. Learn    — learning engine digests completed episodes
  8. Optimize — production / model / prompt optimizers run
  9. Sleep    — wait for next tick (default 60 s)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from runtime.studio_runtime import StudioRuntime

logger = logging.getLogger("aros.continuous_loop")


class ContinuousRuntimeLoop:
    """
    The perpetual execution loop of AROS.

    Never terminates unless StudioRuntime._running is set to False.
    """

    # Seconds between full loop ticks
    DEFAULT_TICK_SEC = 60

    def __init__(self, runtime: "StudioRuntime", tick_sec: int | None = None) -> None:
        self.runtime = runtime
        self.tick_sec = tick_sec or self.DEFAULT_TICK_SEC
        self._cycle_count = 0
        self._cycle_history: list[dict[str, Any]] = []

    async def run(self) -> None:
        """Perpetual execution loop."""
        logger.info("ContinuousRuntimeLoop started — tick=%ds", self.tick_sec)
        while self.runtime._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                logger.info("ContinuousRuntimeLoop cancelled — exiting")
                break
            except Exception as exc:
                logger.error("Loop tick error (continuing): %s", exc, exc_info=True)
            if self.runtime._running:
                await asyncio.sleep(self.tick_sec)

    async def _tick(self) -> None:
        self._cycle_count += 1
        started = datetime.now(timezone.utc)
        logger.info("── AROS Cycle #%d ──────────────────", self._cycle_count)

        state = await self._observe()
        decisions = await self._think(state)
        plan = await self._plan(decisions)
        await self._schedule(plan)
        await self._review()
        await self._learn()
        await self._optimize()

        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        self._cycle_history.append({
            "cycle": self._cycle_count,
            "at": started.isoformat(),
            "elapsed_sec": elapsed,
        })
        # Keep only the last 100 cycles
        if len(self._cycle_history) > 100:
            self._cycle_history = self._cycle_history[-100:]

        logger.info("── Cycle #%d complete in %.2fs ──────", self._cycle_count, elapsed)

    # ── Phase 1 — Observe ─────────────────────────────────────────────────────

    async def _observe(self) -> dict[str, Any]:
        """Collect world state snapshot."""
        state: dict[str, Any] = {}
        try:
            state["world"] = self.runtime.world_model.snapshot()
        except Exception:
            state["world"] = {}
        try:
            state["queue_depth"] = self.runtime.queue.depth()
        except Exception:
            state["queue_depth"] = 0
        try:
            state["worker_status"] = self.runtime.worker_runtime.get_status()
        except Exception:
            state["worker_status"] = {}
        logger.debug("  [Observe] queue_depth=%s", state.get("queue_depth"))
        return state

    # ── Phase 2 — Think ───────────────────────────────────────────────────────

    async def _think(self, state: dict[str, Any]) -> dict[str, Any]:
        """Run the centralized decision engine processing cycle."""
        try:
            result = self.runtime.decision_engine.process_cycle()
            logger.debug("  [Think] committed=%d rejected=%d",
                         result.get("committed", 0), result.get("rejected", 0))
            return result
        except Exception as exc:
            logger.warning("  [Think] decision cycle error: %s", exc)
            return {}

    # ── Phase 3 — Plan ────────────────────────────────────────────────────────

    async def _plan(self, decisions: dict[str, Any]) -> dict[str, Any]:
        """Ask trigger engine whether new productions should start."""
        try:
            return self.runtime.trigger_engine.evaluate()
        except Exception as exc:
            logger.warning("  [Plan] trigger engine error: %s", exc)
            return {"new_productions": []}

    # ── Phase 4 — Schedule ────────────────────────────────────────────────────

    async def _schedule(self, plan: dict[str, Any]) -> None:
        """Push approved work into the scheduler / queue."""
        productions = plan.get("new_productions", [])
        for prod in productions:
            try:
                self.runtime.scheduler.schedule(prod)
                logger.info("  [Schedule] queued production: %s", prod.get("goal_id", "?"))
            except Exception as exc:
                logger.warning("  [Schedule] error: %s", exc)

    # ── Phase 5 — Execute: workers pull from queue autonomously ───────────────
    # (No explicit call needed — workers run as background coroutines)

    # ── Phase 6 — Review ──────────────────────────────────────────────────────

    async def _review(self) -> None:
        """Executive council reviews any episodes completed this cycle."""
        try:
            completed = self.runtime.queue.drain_completed()
            for episode in completed:
                from brain.autonomy.executive_council import AutonomousExecutiveCouncil
                council = AutonomousExecutiveCouncil(self.runtime.decision_engine)
                result = await council.review_episode(episode)
                logger.debug("  [Review] ep=%s action=%s",
                             episode.get("episode_id"), result.get("executive_action"))
        except Exception as exc:
            logger.warning("  [Review] error: %s", exc)

    # ── Phase 7 — Learn ───────────────────────────────────────────────────────

    async def _learn(self) -> None:
        """Learning engine digests recent episodes."""
        try:
            from brain.autonomy.learning_engine import ContinuousLearningEngine
            learner = ContinuousLearningEngine(self.runtime.decision_engine)
            recent = self.runtime.queue.drain_learned()
            for outcome in recent:
                learner.record_episode_outcome(outcome)
        except Exception as exc:
            logger.warning("  [Learn] error: %s", exc)

    # ── Phase 8 — Optimize ────────────────────────────────────────────────────

    async def _optimize(self) -> None:
        """Run optimizers: production, model, prompt."""
        try:
            from brain.autonomy.production_optimizer import ProductionOptimizer
            optimizer = ProductionOptimizer(self.runtime.decision_engine)
            optimizer.optimize_queue(self.runtime.queue.get_status())
        except Exception as exc:
            logger.warning("  [Optimize] production optimizer error: %s", exc)

    # ── Metrics ───────────────────────────────────────────────────────────────

    def get_loop_status(self) -> dict[str, Any]:
        return {
            "cycle_count": self._cycle_count,
            "tick_sec": self.tick_sec,
            "recent_cycles": self._cycle_history[-5:],
        }
