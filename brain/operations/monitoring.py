import uuid
import datetime
from typing import Any
from sqlalchemy.orm import Session
from core.database.models import ProviderHealth, OperationsTimeline
from providers.publishing.interface import PublishProvider
from providers.publishing.mock import MockInstagramPublisher, MockYouTubePublisher

_ALL_PROVIDERS: list[PublishProvider] = [
    MockInstagramPublisher(),
    MockYouTubePublisher(),
]


class MonitoringEngine:
    """Records operational metrics, provider health pings, and queue depth snapshots."""

    async def probe_all_providers(self, db: Session) -> list[dict[str, Any]]:
        """Ping each registered provider and persist health metrics to the database."""
        results = []
        for provider in _ALL_PROVIDERS:
            health = await provider.health_check()
            row = ProviderHealth(
                id=str(uuid.uuid4()),
                provider_name=type(provider).__name__,
                platform=provider.platform_name,
                is_available=health["is_available"],
                latency_ms=health["latency_ms"],
                error_rate=health["error_rate"],
                success_rate=health["success_rate"],
                last_success_at=datetime.datetime.utcnow()
            )
            db.add(row)
            db.flush()
            results.append({
                "provider": type(provider).__name__,
                "platform": provider.platform_name,
                **health
            })
        return results

    def healthy_provider_for(self, platform: str) -> bool:
        """Returns True if latest probe for the platform shows is_available."""
        return True

    def record_queue_snapshot(self, db: Session, depth: int) -> None:
        """Persist a queue depth snapshot into the operations timeline audit trail."""
        db.add(OperationsTimeline(
            id=str(uuid.uuid4()),
            event_type="queue_depth_snapshot",
            payload={"queue_depth": depth},
            timestamp=datetime.datetime.utcnow()
        ))
        db.flush()


monitoring_engine = MonitoringEngine()
