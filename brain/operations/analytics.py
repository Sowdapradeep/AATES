import uuid
import datetime
from typing import Any
from sqlalchemy.orm import Session
from core.database.models import AnalyticsSnapshot, OperationsTimeline


class AnalyticsIngestor:
    """Ingests platform analytics as immutable snapshots — never overwrites history."""

    async def record_snapshot(
        self,
        db: Session,
        episode_id: str,
        platform: str,
        views: int,
        watch_time: float,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        follower_growth: int = 0
    ) -> AnalyticsSnapshot:
        """Insert a new immutable analytics row preserving all historical values."""
        snapshot_id = str(uuid.uuid4())
        snapshot = AnalyticsSnapshot(
            id=snapshot_id,
            episode_id=episode_id,
            platform=platform,
            views=views,
            watch_time=watch_time,
            likes=likes,
            comments=comments,
            shares=shares,
            follower_growth=follower_growth,
            recorded_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        )
        db.add(snapshot)

        # Audit trail entry
        db.add(OperationsTimeline(
            id=str(uuid.uuid4()),
            event_type="analytics_snapshot_recorded",
            payload={
                "episode_id": episode_id,
                "platform": platform,
                "views": views,
                "watch_time": watch_time
            },
            timestamp=datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        ))
        db.flush()
        return snapshot

    def compute_performance_score(self, snapshot: AnalyticsSnapshot) -> float:
        """Compute a normalized performance score for use by the learning engine."""
        if snapshot.views == 0:
            return 0.0
        avg_watch = snapshot.watch_time / snapshot.views
        engagement = (snapshot.likes + snapshot.comments * 2 + snapshot.shares * 3) / max(snapshot.views, 1)
        return round(min((avg_watch * 0.6) + (engagement * 100 * 0.4), 100.0), 2)


analytics_ingestor = AnalyticsIngestor()
