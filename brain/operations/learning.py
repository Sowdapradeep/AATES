import uuid
import datetime
from typing import Any
from sqlalchemy.orm import Session
from core.database.models import Recommendation, OperationsTimeline, AnalyticsSnapshot
from brain.operations.analytics import AnalyticsIngestor


class LearningEngine:
    """Generates strategic recommendations from analytics and feeds them to the CEO agent."""

    SCORE_THRESHOLDS = {
        "poor": 30.0,
        "average": 55.0,
        "good": 75.0
    }

    def generate_recommendations(
        self,
        db: Session,
        episode_id: str,
        snapshot: AnalyticsSnapshot
    ) -> list[Recommendation]:
        """Analyze performance snapshot and generate an auditable recommendation list."""
        ingestor = AnalyticsIngestor()
        score = ingestor.compute_performance_score(snapshot)

        recs: list[Recommendation] = []

        if score < self.SCORE_THRESHOLDS["poor"]:
            recs.append(self._build_rec(
                db, episode_id, "hook",
                "Improve the opening hook within the first 3 seconds.",
                snapshot, score,
                reason="Very low average watch time indicates viewers drop off immediately.",
                impact="Increasing hook strength typically improves retention by 20-35%.",
                confidence=0.9
            ))
            recs.append(self._build_rec(
                db, episode_id, "duration",
                "Reduce episode duration by 10-15 seconds.",
                snapshot, score,
                reason="Low completion rate suggests the content is too long for the platform.",
                impact="Shorter content typically lifts completion rate significantly on Reels.",
                confidence=0.85
            ))

        elif score < self.SCORE_THRESHOLDS["average"]:
            recs.append(self._build_rec(
                db, episode_id, "pacing",
                "Increase cut frequency — use faster editing rhythm.",
                snapshot, score,
                reason="Mid-range score suggests pacing is losing viewer attention mid-episode.",
                impact="Faster pacing lifts average view duration on short-form content.",
                confidence=0.78
            ))

        elif score >= self.SCORE_THRESHOLDS["good"]:
            recs.append(self._build_rec(
                db, episode_id, "character",
                "Introduce a recurring companion character to build serialized loyalty.",
                snapshot, score,
                reason="Strong engagement signals — audience is ready for deeper story investment.",
                impact="Recurring characters lift follower growth rates on series content.",
                confidence=0.72
            ))

        db.flush()
        return recs

    def _build_rec(
        self,
        db: Session,
        episode_id: str,
        category: str,
        text: str,
        snapshot: AnalyticsSnapshot,
        score: float,
        reason: str,
        impact: str,
        confidence: float
    ) -> Recommendation:
        rec = Recommendation(
            id=str(uuid.uuid4()),
            episode_id=episode_id,
            category=category,
            recommendation_text=text,
            source_metrics={
                "views": snapshot.views,
                "watch_time": snapshot.watch_time,
                "performance_score": score
            },
            reason=reason,
            expected_impact=impact,
            confidence=confidence,
            status="pending",
            created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        )
        db.add(rec)

        # Timeline audit event
        db.add(OperationsTimeline(
            id=str(uuid.uuid4()),
            event_type="recommendation_generated",
            payload={"episode_id": episode_id, "category": category, "confidence": confidence},
            timestamp=datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        ))
        return rec

    def ceo_review(
        self,
        db: Session,
        recommendation_id: str,
        approved: bool,
        decision_text: str
    ) -> Recommendation:
        """CEO approves or rejects a recommendation. Approved recs trigger Story Bible updates."""
        rec = db.query(Recommendation).filter(
            Recommendation.id == recommendation_id
        ).first()

        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        rec.status = "approved" if approved else "rejected"
        rec.ceo_decision_text = decision_text

        db.add(OperationsTimeline(
            id=str(uuid.uuid4()),
            event_type="ceo_decision",
            payload={
                "recommendation_id": recommendation_id,
                "approved": approved,
                "decision_text": decision_text
            },
            timestamp=datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        ))
        db.flush()
        return rec


learning_engine = LearningEngine()
