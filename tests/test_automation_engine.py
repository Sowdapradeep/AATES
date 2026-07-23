import os
import uuid
import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient

from core.database.session import Base
from core.database.models import (
    ResearchJob,
    KnowledgePackage,
    ScriptJob,
    ScriptPackage,
    ImageJob,
    ImagePackage,
    VoiceJob,
    VoicePackage,
    VideoJob,
    VideoPackage,
    QualityJob,
    QualityPackage,
    AutomationJob,
    AutomationPackage,
    AutomationPolicyModel,
    AutomationTrigger,
    AutomationDecision,
    AutomationWorkflowInstance,
    AutomationWorkflowStepExecution,
    ResourceLockModel
)
from providers.automation.event_bus import event_bus, EventMessage
from providers.automation.context import ExecutionContext
from providers.automation.resource_lock import resource_lock_manager
from providers.automation.workflow_definition import workflow_registry, WorkflowDefinition, WorkflowStep, CompensationAction
from providers.automation.trigger_manager import trigger_manager, TriggerEvent
from providers.automation.policy_engine import policy_engine, AutomationPolicy
from providers.automation.decision_engine import decision_engine
from providers.automation.workflow_executor import workflow_executor, WorkflowInstance
from brain.agents.automation_agent import process_automation_job


# 1. EventBus, ResourceLock, and WorkflowDefinition Tests
def test_event_bus_and_locks():
    received = []

    def handler(msg: EventMessage):
        received.append(msg)

    event_bus.subscribe("TEST_EVENT", handler)

    msg = EventMessage(
        event_id="e_001",
        event_type="TEST_EVENT",
        source="UnitTest",
        payload={"pkg": "123"}
    )
    asyncio.run(event_bus.publish(msg))

    assert len(received) == 1
    assert received[0].event_id == "e_001"

    # Test Resource Lock
    lock_ok = resource_lock_manager.acquire_lock("pkg_999", "inst_1")
    assert lock_ok is True
    assert resource_lock_manager.is_locked("pkg_999") is True

    lock_fail = resource_lock_manager.acquire_lock("pkg_999", "inst_2")
    assert lock_fail is False

    rel_ok = resource_lock_manager.release_lock("pkg_999", "inst_1")
    assert rel_ok is True
    assert resource_lock_manager.is_locked("pkg_999") is False


# 2. TriggerManager, PolicyEngine, and DecisionEngine Tests
def test_trigger_policy_decision_engines():
    trig = TriggerEvent(
        trigger_id="trig_001",
        trigger_type="QUALITY_APPROVED",
        source_component="QualityAgent",
        source_package_id=str(uuid.uuid4()),
        target_platform="all"
    )

    matched = policy_engine.match_policies(trig)
    assert len(matched) >= 1
    sel_policy = matched[0]

    dec = decision_engine.evaluate_decision(
        trigger=trig,
        policy=sel_policy,
        package_context={"quality_score": 0.94, "learning_confidence": 0.90}
    )
    assert dec.is_approved is True
    assert dec.confidence_score >= 0.90


# 3. WorkflowExecutor Execution Test
@pytest.mark.asyncio
async def test_workflow_executor():
    wf_def = workflow_registry.get("AUTONOMOUS_PUBLISHING")
    assert wf_def is not None

    context = ExecutionContext(
        workflow_instance_id=str(uuid.uuid4()),
        trigger_data={"trigger": "manual"},
        package_references={"quality_package_id": str(uuid.uuid4())}
    )

    instance = WorkflowInstance(
        instance_id=context.workflow_instance_id,
        workflow_id=wf_def.workflow_id,
        trigger_id="trig_manual",
        policy_id="pol_auto_publish_quality_approved",
        context=context
    )

    updated_instance = await workflow_executor.execute_workflow_instance(instance, wf_def)
    assert updated_instance.status == "SUCCESS"
    assert len(updated_instance.step_executions) == len(wf_def.steps)
    assert updated_instance.step_executions[0].idempotency_key != ""


# 4. Background Automation Agent Worker Job Processing Test
@pytest.mark.asyncio
async def test_automation_agent_job_processing(db):
    auto_job = AutomationJob(
        id=uuid.uuid4(),
        status="PROCESSING",
        stage="WAITING",
        trigger_type="MANUAL_TRIGGER",
        target_platform="all"
    )
    db.add(auto_job)
    db.commit()

    await process_automation_job(db, auto_job)

    db.refresh(auto_job)
    assert auto_job.status == "SUCCESS"
    assert auto_job.stage == "COMPLETED"

    # Assert AutomationPackage creation
    assert len(auto_job.packages) == 1
    pkg = auto_job.packages[0]
    assert pkg.execution_confidence >= 0.90
    assert pkg.executed_actions_count >= 1
    assert pkg.package_manifest["package_type"] == "AutomationPackage"


# 5. REST API Endpoints & Policies CRUD Tests
def test_api_automation_routes(client, db):
    # 1. POST /v1/automation (create)
    resp = client.post("/v1/automation", json={
        "trigger_type": "MANUAL_TRIGGER",
        "target_platform": "all",
        "priority": 1
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"

    # 2. GET /v1/automation (list)
    resp = client.get("/v1/automation")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/automation/metrics (metrics)
    resp = client.get("/v1/automation/metrics")
    assert resp.status_code == 200
    assert resp.json()["jobs_queued"] >= 1

    # 4. GET /v1/automation/policies (policies)
    resp = client.get("/v1/automation/policies")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 5. POST /v1/automation/policies (create policy)
    resp = client.post("/v1/automation/policies", json={
        "policy_id": "pol_custom_test",
        "name": "Custom Test Policy",
        "enabled": True,
        "priority": 5,
        "trigger_types": ["SCHEDULE"],
        "conditions": {"min_quality_score": 0.80},
        "target_workflow_id": "E2E_CONTENT_GENERATION",
        "cooldown_sec": 30
    })
    assert resp.status_code == 200
    assert resp.json()["policy_id"] == "pol_custom_test"

    # 6. GET /v1/automation/{id} (detail)
    resp = client.get(f"/v1/automation/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 7. POST /v1/automation/{id}/execute (execute)
    resp = client.post(f"/v1/automation/{job_id}/execute")
    assert resp.status_code == 200
    assert resp.json()["status"] == "QUEUED"

    # 8. Enable/Disable policy
    resp = client.post("/v1/automation/pol_custom_test/disable")
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
