import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from providers.automation.trigger_manager import TriggerEvent

logger = logging.getLogger("policy_engine")

class AutomationPolicy(BaseModel):
    """Automation Policy definition storing rules, triggers, cooldowns, and actions."""
    policy_id: str
    name: str
    enabled: bool = True
    priority: int = 0
    trigger_types: List[str]  # e.g., ["QUALITY_APPROVED", "SCHEDULE"]
    conditions: Dict[str, Any] = Field(default_factory=dict)  # e.g., {"min_quality_score": 0.85, "platform": "all"}
    target_workflow_id: str = "AUTONOMOUS_PUBLISHING"
    cooldown_sec: int = 60
    retry_rules: Dict[str, Any] = Field(default_factory=lambda: {"max_retries": 3, "backoff_sec": 10})
    platforms: List[str] = Field(default_factory=lambda: ["instagram", "youtube", "all"])
    applicable_agents: List[str] = Field(default_factory=lambda: ["all"])

class PolicyEngine:
    """Policy Engine matching trigger events against configurable Automation Policies."""

    def __init__(self) -> None:
        self._policies: Dict[str, AutomationPolicy] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self) -> None:
        p1 = AutomationPolicy(
            policy_id="pol_auto_publish_quality_approved",
            name="Auto Publish Quality Approved Content",
            enabled=True,
            priority=10,
            trigger_types=["QUALITY_APPROVED", "MANUAL_TRIGGER"],
            conditions={"min_quality_score": 0.85},
            target_workflow_id="AUTONOMOUS_PUBLISHING"
        )

        p2 = AutomationPolicy(
            policy_id="pol_e2e_content_generation",
            name="Scheduled End-to-End Content Pipeline",
            enabled=True,
            priority=5,
            trigger_types=["SCHEDULE", "MANUAL_TRIGGER"],
            conditions={"platform": "all"},
            target_workflow_id="E2E_CONTENT_GENERATION"
        )

        p3 = AutomationPolicy(
            policy_id="pol_quality_remediation",
            name="Automatic Quality Remediation on Gate Warning",
            enabled=True,
            priority=8,
            trigger_types=["PACKAGE_UPDATED", "MANUAL_TRIGGER"],
            conditions={"remediation_required": True},
            target_workflow_id="QUALITY_REMEDIATION"
        )

        p4 = AutomationPolicy(
            policy_id="pol_learning_recommendation_optimization",
            name="Apply High-Confidence Learning Optimizations",
            enabled=True,
            priority=6,
            trigger_types=["LEARNING_RECOMMENDATION", "MANUAL_TRIGGER"],
            conditions={"min_confidence": 0.80},
            target_workflow_id="FEEDBACK_DRIVEN_OPTIMIZATION"
        )

        for p in [p1, p2, p3, p4]:
            self._policies[p.policy_id] = p

    def register_policy(self, policy: AutomationPolicy) -> None:
        self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> Optional[AutomationPolicy]:
        return self._policies.get(policy_id)

    def list_policies(self) -> List[AutomationPolicy]:
        return list(self._policies.values())

    def match_policies(self, trigger: TriggerEvent) -> List[AutomationPolicy]:
        matched: List[AutomationPolicy] = []
        for policy in self._policies.values():
            if not policy.enabled:
                continue

            if trigger.trigger_type in policy.trigger_types or "all" in policy.trigger_types or trigger.trigger_type == "MANUAL_TRIGGER":
                # Check platform match
                if trigger.target_platform != "all" and trigger.target_platform not in policy.platforms and "all" not in policy.platforms:
                    continue

                matched.append(policy)

        # Order by priority descending
        matched.sort(key=lambda p: p.priority, reverse=True)
        return matched

policy_engine = PolicyEngine()
ZOOMING = "zoom"
