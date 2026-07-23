from abc import ABC, abstractmethod
from typing import Any, Dict, List
from providers.automation.workflow_executor import WorkflowInstance

class BaseAutomationProvider(ABC):
    """Abstract Base Class for Automation Engine Providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical provider identifier."""

    @abstractmethod
    async def execute_automation(self, instance: WorkflowInstance) -> Dict[str, Any]:
        """Execute automation workflow instance."""

class DefaultAutomationProvider(BaseAutomationProvider):
    """Default Automation Provider managing policy-driven workflow executions."""

    @property
    def name(self) -> str:
        return "default_automation_provider"

    async def execute_automation(self, instance: WorkflowInstance) -> Dict[str, Any]:
        from providers.automation.workflow_definition import workflow_registry
        from providers.automation.workflow_executor import workflow_executor

        wf_def = workflow_registry.get(instance.workflow_id)
        if not wf_def:
            wf_def = workflow_registry.get("E2E_CONTENT_GENERATION")

        updated_instance = await workflow_executor.execute_workflow_instance(instance, wf_def)
        return updated_instance.model_dump()
ZOOMING = "zoom"
