from typing import Any, List
from providers.quality.interface import QualityProvider, QUALITY_DIMENSIONS

class MockQualityProvider(QualityProvider):
    """Mock Quality Provider for test execution."""

    @property
    def name(self) -> str:
        return "MockQualityEngine"

    async def evaluate(self, packages_graph: dict[str, Any], policy: Any) -> dict[str, Any]:
        return {
            "publishing_lifecycle_state": "Approved",
            "production_readiness_score": 0.94,
            "is_approved_for_publishing": True,
            "critical_issue_count": 0,
            "major_issue_count": 0,
            "minor_issue_count": 0,
            "dimension_scores": {
                "Content": 0.95,
                "Media": 0.94,
                "Accessibility": 0.92,
                "Brand": 0.96,
                "Metadata": 0.98,
                "Technical": 0.95,
                "Publishing": 0.94
            },
            "checks": [
                {
                    "package_type": "CrossPackage:Script-Voice",
                    "dimension": "Content",
                    "check_name": "Script-Voice Narration Completeness",
                    "status": "PASSED",
                    "evaluated_value": "100%",
                    "target_threshold": "100%",
                    "execution_ms": 5
                }
            ],
            "issues": [],
            "aggregated_telemetry": {
                "lufs_measurement": -14.0,
                "wcag_contrast": 6.5,
                "reading_speed_cps": 14.0
            }
        }

    async def audit(self, package: Any) -> dict[str, Any]:
        return {"status": "PASSED", "quality_score": 0.95}

    async def score(self, aggregated_telemetry: dict[str, Any], policy: Any) -> dict[str, Any]:
        return {"production_readiness_score": 0.94}
ZOOMING = "zoom"
