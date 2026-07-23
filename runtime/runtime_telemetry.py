"""
runtime/runtime_telemetry.py — Live runtime telemetry collection.

Tracks:
  - CPU
  - Memory
  - Queue Depth
  - Workers
  - Provider Latency
  - AWS Costs
  - Bedrock Usage
  - Model Selection
  - Episode Throughput
  - Publishing Rate
  - Quality Trends

Exposed via /v1/runtime/metrics endpoint.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.studio_runtime import StudioRuntime

logger = logging.getLogger("aros.telemetry")


class RuntimeTelemetry:
    """Collects and aggregates runtime metrics at every AROS cycle."""

    def __init__(self, runtime: "StudioRuntime") -> None:
        self.runtime = runtime
        self._snapshots: list[dict[str, Any]] = []
        self._episode_count = 0
        self._publish_count = 0
        self._quality_scores: list[float] = []
        self._bedrock_calls = 0
        self._bedrock_total_latency_ms: float = 0.0
        self._total_cost_usd: float = 0.0

    def record_episode(self, quality: float, cost_usd: float) -> None:
        self._episode_count += 1
        self._quality_scores.append(quality)
        self._total_cost_usd += cost_usd

    def record_publish(self) -> None:
        self._publish_count += 1

    def record_bedrock_call(self, latency_ms: float) -> None:
        self._bedrock_calls += 1
        self._bedrock_total_latency_ms += latency_ms

    def snapshot(self) -> dict[str, Any]:
        """Collect a point-in-time telemetry snapshot."""
        try:
            import psutil  # type: ignore
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
        except ImportError:
            cpu, mem = -1.0, -1.0

        avg_quality = (
            round(sum(self._quality_scores) / len(self._quality_scores), 2)
            if self._quality_scores else 0.0
        )
        avg_bedrock_latency_ms = (
            round(self._bedrock_total_latency_ms / self._bedrock_calls, 1)
            if self._bedrock_calls else 0.0
        )

        snap: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_pct": cpu,
            "memory_pct": mem,
            "queue_depth": self.runtime.queue.depth() if self.runtime.queue else 0,
            "workers": self.runtime.worker_runtime.get_status() if self.runtime.worker_runtime else {},
            "bedrock_calls": self._bedrock_calls,
            "bedrock_avg_latency_ms": avg_bedrock_latency_ms,
            "total_cost_usd": round(self._total_cost_usd, 4),
            "episodes_produced": self._episode_count,
            "publishes_sent": self._publish_count,
            "avg_quality_score": avg_quality,
            "scheduler": self.runtime.scheduler.get_status() if self.runtime.scheduler else {},
        }
        self._snapshots.append(snap)
        if len(self._snapshots) > 200:
            self._snapshots = self._snapshots[-200:]
        return snap

    def get_metrics(self) -> dict[str, Any]:
        return {
            "current": self.snapshot(),
            "history_count": len(self._snapshots),
            "recent": self._snapshots[-5:],
        }
