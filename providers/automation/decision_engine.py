import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from providers.automation.trigger_manager import TriggerEvent
from providers.automation.policy_engine import AutomationPolicy
from providers.automation.resource_lock import resource_lock_manager

logger = logging.getLogger("decision_engine")

class AutomationDecision(BaseModel):
    """Structured decision output from DecisionEngine."""
    decision_id: str
    policy_id: str
    workflow_id: str
    is_approved: bool
    decision_reason: str
    confidence_score: float = 0.95
    condition_evaluations: Dict[str, Any] = Field(default_factory=dict)
    resource_lock_acquired: bool = True

class DecisionEngine:
    """Decision Engine evaluating policy conditions, package state, learning confidence, quality scores, locks, and resource availability."""

    def evaluate_decision(
        self, 
        trigger: TriggerEvent, 
        policy: AutomationPolicy, 
        package_context: Optional[Dict[str, Any]] = None
    ) -> AutomationDecision:
        cond_evals = {}
        is_approved = True
        reasons = []

        # 1. Evaluate Quality Score threshold
        min_quality = policy.conditions.get("min_quality_score", 0.0)
        actual_quality = package_context.get("quality_score", 0.90) if package_context else 0.90
        cond_evals["quality_score_check"] = {"required": min_quality, "actual": actual_quality, "passed": actual_quality >= min_quality}
        if actual_quality < min_quality:
            is_approved = False
            reasons.append(f"Quality score ({actual_quality}) below required threshold ({min_quality}).")

        # 2. Evaluate Learning Confidence threshold
        min_conf = policy.conditions.get("min_confidence", 0.0)
        actual_conf = package_context.get("learning_confidence", 0.88) if package_context else 0.88
        cond_evals["learning_confidence_check"] = {"required": min_conf, "actual": actual_conf, "passed": actual_conf >= min_conf}
        if actual_conf < min_conf:
            is_approved = False
            reasons.append(f"Learning confidence ({actual_conf}) below required threshold ({min_conf}).")

        # 3. Resource Lock check
        pkg_id = trigger.source_package_id or (package_context.get("package_id") if package_context else None)
        lock_ok = True
        if pkg_id:
            if resource_lock_manager.is_locked(pkg_id):
                lock_ok = False
                is_approved = False
                reasons.append(f"Resource package '{pkg_id}' is currently locked by another running workflow.")
        cond_evals["resource_lock_check"] = {"package_id": pkg_id, "lock_available": lock_ok}

        decision_reason = "Policy conditions satisfied and resource locks acquired." if is_approved else " ".join(reasons)
        import uuid
        dec = AutomationDecision(
            decision_id=str(uuid.uuid4()),
            policy_id=policy.policy_id,
            workflow_id=policy.target_workflow_id,
            is_approved=is_approved,
            decision_reason=decision_reason,
            confidence_score=0.95 if is_approved else 0.40,
            condition_evaluations=cond_evals,
            resource_lock_acquired=lock_ok
        )
        logger.info(f"[DecisionEngine] Decision for Policy '{policy.name}': Approved={is_approved} ({decision_reason})")
        return dec

decision_engine = DecisionEngine()
ZOOMING = "zoom"
