"""
runtime/worker_runtime.py — Long-running worker pool.

Workers remain alive continuously (as asyncio tasks).

Workers:
  - ImageWorker
  - VideoWorker
  - VoiceWorker
  - MusicWorker
  - PublishingWorker
  - AnalyticsWorker
  - LearningWorker

Each worker pulls from the DistributedQueue indefinitely.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("aros.worker_runtime")


class BaseWorker:
    """Abstract long-running worker."""

    WORKER_TYPE = "base"
    SLEEP_SEC = 5

    def __init__(self, queue: Any) -> None:
        self.queue = queue
        self.task: asyncio.Task | None = None
        self._running = False
        self.processed = 0
        self.errors = 0
        self.started_at: datetime | None = None

    async def start(self) -> None:
        self._running = True
        self.started_at = datetime.now(timezone.utc)
        self.task = asyncio.create_task(self._loop(), name=f"worker.{self.WORKER_TYPE}")
        logger.info("Worker started: %s", self.WORKER_TYPE)

    async def stop(self) -> None:
        self._running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Worker stopped: %s", self.WORKER_TYPE)

    async def _loop(self) -> None:
        while self._running:
            try:
                job = self.queue.pop(self.WORKER_TYPE)
                if job:
                    await self.process(job)
                    self.processed += 1
                else:
                    await asyncio.sleep(self.SLEEP_SEC)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.errors += 1
                logger.error("Worker %s error: %s", self.WORKER_TYPE, exc)
                await asyncio.sleep(2)

    async def process(self, job: dict[str, Any]) -> None:
        """Override in subclasses."""
        raise NotImplementedError

    def get_status(self) -> dict[str, Any]:
        return {
            "type": self.WORKER_TYPE,
            "running": self._running,
            "processed": self.processed,
            "errors": self.errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }


class ImageWorker(BaseWorker):
    WORKER_TYPE = "image"

    async def process(self, job: dict[str, Any]) -> None:
        logger.debug("ImageWorker processing: %s", job.get("scene_id"))
        await asyncio.sleep(0)


class VideoWorker(BaseWorker):
    WORKER_TYPE = "video"

    async def process(self, job: dict[str, Any]) -> None:
        logger.debug("VideoWorker processing: %s", job.get("scene_id"))
        await asyncio.sleep(0)


class VoiceWorker(BaseWorker):
    WORKER_TYPE = "voice"

    async def process(self, job: dict[str, Any]) -> None:
        logger.debug("VoiceWorker processing: %s", job.get("scene_id"))
        await asyncio.sleep(0)


class MusicWorker(BaseWorker):
    WORKER_TYPE = "music"

    async def process(self, job: dict[str, Any]) -> None:
        logger.debug("MusicWorker processing: %s", job.get("scene_id"))
        await asyncio.sleep(0)


class PublishingWorker(BaseWorker):
    WORKER_TYPE = "publishing"

    async def process(self, job: dict[str, Any]) -> None:
        logger.debug("PublishingWorker processing: %s", job.get("episode_id"))
        await asyncio.sleep(0)


class AnalyticsWorker(BaseWorker):
    WORKER_TYPE = "analytics"

    async def process(self, job: dict[str, Any]) -> None:
        logger.debug("AnalyticsWorker processing: %s", job.get("episode_id"))
        await asyncio.sleep(0)


class LearningWorker(BaseWorker):
    WORKER_TYPE = "learning"

    async def process(self, job: dict[str, Any]) -> None:
        logger.debug("LearningWorker processing: %s", job.get("episode_id"))
        await asyncio.sleep(0)


class WorkerRuntime:
    """Registry and lifecycle manager for all long-running workers."""

    _WORKER_CLASSES = [
        ImageWorker,
        VideoWorker,
        VoiceWorker,
        MusicWorker,
        PublishingWorker,
        AnalyticsWorker,
        LearningWorker,
    ]

    def __init__(self, queue: Any) -> None:
        self.queue = queue
        self.workers: dict[str, BaseWorker] = {
            cls.WORKER_TYPE: cls(queue) for cls in self._WORKER_CLASSES
        }

    async def start_all(self) -> None:
        for worker in self.workers.values():
            await worker.start()
        logger.info("WorkerRuntime: %d workers started", len(self.workers))

    async def stop_all(self) -> None:
        for worker in self.workers.values():
            await worker.stop()
        logger.info("WorkerRuntime: all workers stopped")

    async def restart(self, worker_type: str) -> bool:
        worker = self.workers.get(worker_type)
        if not worker:
            return False
        await worker.stop()
        await worker.start()
        logger.info("Worker restarted: %s", worker_type)
        return True

    def get_status(self) -> dict[str, Any]:
        return {wt: w.get_status() for wt, w in self.workers.items()}

    def get_worker(self, worker_type: str) -> BaseWorker | None:
        return self.workers.get(worker_type)
