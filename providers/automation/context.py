from datetime import UTC, datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class ExecutionContext(BaseModel):
    """Canonical execution context passed between workflow steps."""
    workflow_instance_id: str
    trigger_data: Dict[str, Any] = Field(default_factory=dict)
    package_references: Dict[str, str] = Field(default_factory=dict)  # e.g. {"script_package_id": "...", "quality_package_id": "..."}
    decision_outputs: Dict[str, Any] = Field(default_factory=dict)
    shared_variables: Dict[str, Any] = Field(default_factory=dict)
    action_results: Dict[str, Any] = Field(default_factory=dict)
    telemetry: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None).isoformat())

    def get_package_id(self, package_type: str) -> Optional[str]:
        return self.package_references.get(package_type)

    def set_package_id(self, package_type: str, pkg_id: str) -> None:
        self.package_references[package_type] = pkg_id

    def set_action_result(self, action_name: str, result: Dict[str, Any]) -> None:
        self.action_results[action_name] = result
ZOOMING = "zoom"
