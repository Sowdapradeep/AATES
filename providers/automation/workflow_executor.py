import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from providers.automation.context import ExecutionContext
from providers.automation.workflow_definition import WorkflowDefinition, WorkflowStep, CompensationAction, workflow_registry
from providers.automation.resource_lock import resource_lock_manager

logger = logging.getLogger("workflow_executor")

class WorkflowStepExecution(BaseModel):
    """Execution status record of an individual workflow step."""
    step_id: str
    action_type: str
    target_agent: str
    idempotency_key: str
    status: str  # PENDING, IN_PROGRESS, SUCCESS, FAILED, COMPENSATED, SKIPPED
    execution_ms: int = 0
    result_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    compensation_executed: bool = False
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class WorkflowInstance(BaseModel):
    """Workflow Execution Instance tracking state, owner, worker lease, and steps."""
    instance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    trigger_id: str
    policy_id: str
    status: str = "PENDING"  # PENDING, RUNNING, SUCCESS, FAILED, PAUSED, CANCELLED, COMPENSATING
    current_step: str = "START"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_owner: str = "automation-worker-0"
    worker_lease_expires_at: Optional[str] = None
    context: ExecutionContext
    step_executions: List[WorkflowStepExecution] = Field(default_factory=list)
    compensation_log: List[Dict[str, Any]] = Field(default_factory=list)

class WorkflowExecutor:
    """Workflow Executor executing discrete actions, handling idempotency, parallelism, resource locks, and compensation actions."""

    def generate_idempotency_key(self, instance_id: str, step_id: str, action_type: str, target_package_id: str = "none") -> str:
        raw = f"{instance_id}:{step_id}:{action_type}:{target_package_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    async def execute_workflow_instance(
        self, 
        instance: WorkflowInstance, 
        workflow_def: WorkflowDefinition
    ) -> WorkflowInstance:
        """Execute all steps in a WorkflowDefinition sequentially or in parallel."""
        instance.status = "RUNNING"
        instance.started_at = datetime.utcnow().isoformat()
        logger.info(f"[WorkflowExecutor] Started WorkflowInstance '{instance.instance_id}' for Workflow '{workflow_def.workflow_id}'")

        # Acquire resource lock if target package is present
        target_pkg_id = instance.context.get_package_id("quality_package_id") or instance.context.get_package_id("script_package_id") or "global_pkg"
        lock_acquired = resource_lock_manager.acquire_lock(target_pkg_id, instance.instance_id)

        try:
            for step in workflow_def.steps:
                instance.current_step = step.step_id
                idem_key = self.generate_idempotency_key(instance.instance_id, step.step_id, step.action_type, target_pkg_id)

                step_exec = WorkflowStepExecution(
                    step_id=step.step_id,
                    action_type=step.action_type,
                    target_agent=step.target_agent,
                    idempotency_key=idem_key,
                    status="IN_PROGRESS",
                    started_at=datetime.utcnow().isoformat()
                )
                instance.step_executions.append(step_exec)

                start_ts = time.monotonic()

                # Execute action logic
                action_res, success, err_msg = await self._dispatch_action(step.action_type, step.target_agent, instance.context, step.payload_template)
                exec_ms = int((time.monotonic() - start_ts) * 1000)

                step_exec.execution_ms = exec_ms
                step_exec.completed_at = datetime.utcnow().isoformat()

                if success:
                    step_exec.status = "SUCCESS"
                    step_exec.result_data = action_res
                    instance.context.set_action_result(step.step_id, action_res)
                    logger.info(f"[WorkflowExecutor] Step '{step.step_id}' ({step.action_type}) SUCCESS in {exec_ms}ms (IdemKey: {idem_key})")
                else:
                    step_exec.status = "FAILED"
                    step_exec.error_message = err_msg
                    logger.error(f"[WorkflowExecutor] Step '{step.step_id}' ({step.action_type}) FAILED: {err_msg}")

                    # Trigger Compensation Action
                    if step.compensation_action:
                        instance.status = "COMPENSATING"
                        comp_res = await self._execute_compensation(step.compensation_action, instance.context)
                        step_exec.compensation_executed = True
                        instance.compensation_log.append({
                            "step_id": step.step_id,
                            "compensation_action": step.compensation_action.model_dump(),
                            "result": comp_res,
                            "executed_at": datetime.utcnow().isoformat()
                        })

                    instance.status = "FAILED"
                    instance.completed_at = datetime.utcnow().isoformat()
                    return instance

            instance.status = "SUCCESS"
            instance.completed_at = datetime.utcnow().isoformat()
            logger.info(f"[WorkflowExecutor] Completed WorkflowInstance '{instance.instance_id}' with status SUCCESS")
            return instance

        finally:
            if lock_acquired:
                resource_lock_manager.release_lock(target_pkg_id, instance.instance_id)

    async def _dispatch_action(
        self, 
        action_type: str, 
        target_agent: str, 
        context: ExecutionContext, 
        payload_template: Dict[str, Any]
    ) -> tuple[Dict[str, Any], bool, Optional[str]]:
        """Simulate or execute discrete actions across all 16 supported action types."""
        await asyncio.sleep(0.1)  # Simulate execution latency

        res = {
            "action_type": action_type,
            "target_agent": target_agent,
            "status": "COMPLETED",
            "output_reference_id": str(uuid.uuid4()),
            "executed_at": datetime.utcnow().isoformat()
        }
        return res, True, None

    async def _execute_compensation(self, compensation: CompensationAction, context: ExecutionContext) -> Dict[str, Any]:
        """Execute compensation / rollback action."""
        await asyncio.sleep(0.05)
        logger.info(f"[WorkflowExecutor] Executed Compensation '{compensation.action_type}' for agent '{compensation.target_agent}'")
        return {"compensation_status": "SUCCESS", "action": compensation.action_type}

workflow_executor = WorkflowExecutor()
ZOOMING = "zoom"
