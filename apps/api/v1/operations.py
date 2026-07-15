from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any
from core.database.session import get_db
from contracts.dto.operations import (
    PublishRequestDTO, AnalyticsSnapshotDTO, RecommendationDTO
)
from brain.operations.queue import publishing_queue_manager, publishing_scheduler
from brain.operations.monitoring import monitoring_engine
from brain.operations.analytics import analytics_ingestor
from brain.operations.learning import learning_engine
from core.database.models import AnalyticsSnapshot, Recommendation, DistributionHistory, OperationsTimeline
import uuid, datetime

router = APIRouter(prefix="/v1/operations", tags=["operations"])


@router.post("/campaigns", status_code=201)
async def create_campaign(payload: dict, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Create a publishing campaign grouping one or more episodes."""
    from core.database.models import Campaign
    campaign_id = str(uuid.uuid4())
    campaign = Campaign(
        id=campaign_id,
        name=payload["name"],
        description=payload.get("description"),
        universe_id=payload["universe_id"],
        season=payload.get("season", 1),
        start_date=datetime.datetime.fromisoformat(payload.get("start_date", datetime.datetime.utcnow().isoformat())),
        end_date=datetime.datetime.fromisoformat(payload.get("end_date", datetime.datetime.utcnow().isoformat())),
        status=payload.get("status", "draft"),
        priority=payload.get("priority", 0),
        platforms=payload.get("platforms", {})
    )
    db.add(campaign)
    db.commit()
    return {"campaign_id": campaign_id, "status": payload.get("status", "draft")}


@router.post("/publish/enqueue")
async def enqueue_publish(req: PublishRequestDTO, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Add a Master Reel to the publishing queue for target platforms."""
    entries = await publishing_queue_manager.enqueue(
        db=db,
        episode_id=req.episode_id,
        universe_id=req.universe_id,
        platforms=req.platforms,
        master_reel_path=req.master_reel_path,
        campaign_id=req.campaign_id,
        priority=req.priority
    )
    db.commit()
    return {"queued": len(entries), "platforms": req.platforms}


@router.post("/publish/execute")
async def execute_publish(payload: dict, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Execute all queued publishing workflows for an episode."""
    results = await publishing_queue_manager.publish_all(
        db=db,
        episode_id=payload["episode_id"],
        master_reel_path=payload["master_reel_path"],
        caption=payload.get("caption", "")
    )
    db.commit()
    return results


@router.post("/schedule/check")
async def check_schedule_window(payload: dict) -> dict[str, Any]:
    """Check if a publishing datetime falls within an allowed scheduling window."""
    from datetime import datetime as dt
    scheduled_at = dt.fromisoformat(payload["scheduled_at"])
    in_window = publishing_scheduler.is_in_window(scheduled_at)
    next_slot = publishing_scheduler.next_valid_slot(scheduled_at)
    return {
        "scheduled_at": scheduled_at.isoformat(),
        "in_window": in_window,
        "next_valid_slot": next_slot.isoformat()
    }


@router.post("/monitoring/probe")
async def probe_providers(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Probe all registered publishing providers and persist health metrics."""
    results = await monitoring_engine.probe_all_providers(db)
    db.commit()
    return results


@router.post("/analytics/record")
async def record_analytics(snap: AnalyticsSnapshotDTO, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Record an immutable analytics snapshot for a published episode."""
    snapshot = await analytics_ingestor.record_snapshot(
        db=db,
        episode_id=snap.episode_id,
        platform=snap.platform,
        views=snap.views,
        watch_time=snap.watch_time,
        likes=snap.likes,
        comments=snap.comments,
        shares=snap.shares,
        follower_growth=snap.follower_growth
    )
    # Compute score while session is still active (before commit expiry)
    score = analytics_ingestor.compute_performance_score(snapshot)
    snapshot_id = str(snapshot.id)
    db.commit()
    return {"snapshot_id": snapshot_id, "performance_score": score}


@router.post("/learning/recommend")
async def generate_recommendations(payload: dict, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Generate learning recommendations from the most recent analytics snapshot."""
    snapshot = db.query(AnalyticsSnapshot).filter(
        AnalyticsSnapshot.episode_id == payload["episode_id"]
    ).order_by(AnalyticsSnapshot.recorded_at.desc()).first()

    if not snapshot:
        return []

    recs = learning_engine.generate_recommendations(db, payload["episode_id"], snapshot)
    db.commit()
    return [{"id": r.id, "category": r.category, "text": r.recommendation_text, "confidence": r.confidence} for r in recs]


@router.post("/learning/review")
async def ceo_review(payload: dict, db: Session = Depends(get_db)) -> dict[str, Any]:
    """CEO approves or rejects a learning recommendation and logs the decision."""
    rec = learning_engine.ceo_review(
        db=db,
        recommendation_id=payload["recommendation_id"],
        approved=payload["approved"],
        decision_text=payload.get("decision_text", "")
    )
    db.commit()
    return {"recommendation_id": str(rec.id), "status": rec.status}


@router.get("/timeline/{episode_id}")
async def get_timeline(episode_id: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Retrieve the complete operations timeline for an episode."""
    events = db.query(OperationsTimeline).order_by(OperationsTimeline.timestamp.asc()).all()
    return [{"event_type": e.event_type, "payload": e.payload, "timestamp": e.timestamp.isoformat()} for e in events]


@router.get("/distribution/{episode_id}")
async def get_distribution(episode_id: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return the full publishing distribution history for an episode."""
    history = db.query(DistributionHistory).filter(
        DistributionHistory.episode_id == episode_id
    ).all()
    return [
        {"platform": h.platform, "status": h.status, "retry_count": h.retry_count,
         "publish_time": h.publish_time.isoformat() if h.publish_time else None}
        for h in history
    ]
