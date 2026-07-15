from typing import Any, Sequence
from sqlalchemy.orm import Session
from core.database.session import SessionLocal
from core.database.models import DecisionLog, DecisionReason, DecisionConfidence

class DecisionEngine:
    """Core decision retrieval engine providing auditable logs for agent decisions."""
    
    def get_decisions(self, skip: int = 0, limit: int = 100, db: Session = None) -> list[dict[str, Any]]:
        """Queries historical decisions records, joining confidence levels and reasons details."""
        session = db or SessionLocal()
        try:
            logs = session.query(DecisionLog).order_by(DecisionLog.timestamp.desc()).offset(skip).limit(limit).all()
            result = []
            for log in logs:
                confidence = session.query(DecisionConfidence).filter(DecisionConfidence.decision_id == log.id).first()
                reasons = session.query(DecisionReason).filter(DecisionReason.decision_id == log.id).all()
                result.append({
                    "decision_id": str(log.id),
                    "actor_name": log.actor_name,
                    "decision_type": log.decision_type,
                    "timestamp": log.timestamp.isoformat(),
                    "payload": log.payload,
                    "confidence_score": confidence.confidence_score if confidence else None,
                    "reasons": [r.reason_text for r in reasons]
                })
            return result
        finally:
            if not db:
                session.close()

decision_engine = DecisionEngine()
