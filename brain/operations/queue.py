import uuid
import datetime
from typing import Any
from sqlalchemy.orm import Session
from core.database.models import DistributionHistory, OperationsTimeline
from providers.publishing.interface import PublishProvider
from providers.publishing.mock import MockInstagramPublisher, MockYouTubePublisher
from providers.publishing.youtube import YouTubePublisher
from providers.publishing.instagram import InstagramPublisher
from core.config.settings import settings

class DynamicProviderRegistry(dict):
    def get(self, key, default=None):
        if key in self:
            return self[key]
        if key == "youtube_short":
            if settings.publishing.youtube_enabled and settings.publishing.youtube_refresh_token:
                return YouTubePublisher()
            return MockYouTubePublisher()
        elif key == "instagram_reel":
            if settings.publishing.instagram_enabled and settings.publishing.instagram_access_token:
                return InstagramPublisher()
            return MockInstagramPublisher()
        return super().get(key, default)

_PROVIDER_REGISTRY = DynamicProviderRegistry()

MAX_RETRIES = 3


class PublishingQueueManager:
    """Manages prioritized, retryable publishing workflows with duplicate prevention."""

    async def enqueue(
        self,
        db: Session,
        episode_id: str,
        universe_id: str,
        platforms: list[str],
        master_reel_path: str,
        campaign_id: str | None = None,
        priority: int = 0
    ) -> list[DistributionHistory]:
        """Create distribution history entries for each target platform."""
        entries = []
        for platform in platforms:
            # Duplicate prevention: skip if already successfully published
            existing = db.query(DistributionHistory).filter(
                DistributionHistory.episode_id == episode_id,
                DistributionHistory.platform == platform,
                DistributionHistory.status == "success"
            ).first()
            if existing:
                continue

            entry = DistributionHistory(
                id=str(uuid.uuid4()),
                campaign_id=campaign_id,
                universe_id=universe_id,
                episode_id=episode_id,
                platform=platform,
                status="queued",
                retry_count=0
            )
            db.add(entry)
            entries.append(entry)

        db.flush()
        return entries

    async def publish_all(
        self,
        db: Session,
        episode_id: str,
        master_reel_path: str,
        caption: str = ""
    ) -> list[dict[str, Any]]:
        """Execute all queued distribution jobs for an episode, with auto-retry logic."""
        queued = db.query(DistributionHistory).filter(
            DistributionHistory.episode_id == episode_id,
            DistributionHistory.status.in_(["queued", "failed"])
        ).all()

        results = []
        for entry in queued:
            if entry.retry_count >= MAX_RETRIES:
                entry.status = "abandoned"
                db.flush()
                results.append({"platform": entry.platform, "status": "abandoned"})
                continue

            provider = _PROVIDER_REGISTRY.get(entry.platform)
            if not provider:
                entry.status = "failed"
                db.flush()
                results.append({"platform": entry.platform, "status": "failed", "error": "No provider registered"})
                continue

            try:
                res = await provider.upload(master_reel_path, caption, {"episode_id": episode_id})
                entry.status = res["status"]
                entry.publish_time = datetime.datetime.utcnow()
                db.flush()

                # Log to operations timeline
                _log_timeline_event(db, "publish_success", {
                    "episode_id": episode_id,
                    "platform": entry.platform,
                    "external_post_id": res.get("external_post_id")
                })

                results.append({"platform": entry.platform, "status": "success",
                                "external_post_id": res.get("external_post_id")})
            except Exception as e:
                entry.status = "failed"
                entry.retry_count += 1
                db.flush()
                results.append({"platform": entry.platform, "status": "failed", "error": str(e)})

        return results


class PublishingScheduler:
    """Evaluates configurable publishing windows and blackout periods."""

    def __init__(self) -> None:
        self.blackout_hours: list[int] = [0, 1, 2, 3]  # 0am-3am blocked

    def is_in_window(self, scheduled_at: datetime.datetime) -> bool:
        """Check if the publishing time falls within an allowed window."""
        return scheduled_at.hour not in self.blackout_hours

    def next_valid_slot(self, from_dt: datetime.datetime) -> datetime.datetime:
        """Advance the time past any blackout period to the next valid window."""
        candidate = from_dt
        while candidate.hour in self.blackout_hours:
            candidate = candidate + datetime.timedelta(hours=1)
        return candidate


def _log_timeline_event(db: Session, event_type: str, payload: dict[str, Any]) -> None:
    db.add(OperationsTimeline(
        id=str(uuid.uuid4()),
        event_type=event_type,
        payload=payload,
        timestamp=datetime.datetime.utcnow()
    ))
    db.flush()


publishing_queue_manager = PublishingQueueManager()
publishing_scheduler = PublishingScheduler()
