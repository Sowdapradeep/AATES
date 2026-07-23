from typing import Any, List

QUALITY_DIMENSIONS = [
    "Content",
    "Media",
    "Accessibility",
    "Brand",
    "Metadata",
    "Technical",
    "Publishing"
]

class QualityProvider:
    """Abstract interface contract for all AI Quality & Governance engines."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def capabilities(self) -> List[str]:
        return ["policy_evaluation", "cross_package_validation", "evidence_generation", "scoring"]

    def supports_cross_package_validation(self) -> bool:
        return True

    def supports_policy_profiles(self) -> bool:
        return True

    async def evaluate(self, packages_graph: dict[str, Any], policy: Any) -> dict[str, Any]:
        """Execute full cross-package validation matrix against policy profile."""
        raise NotImplementedError

    async def audit(self, package: Any) -> dict[str, Any]:
        """Audit single package telemetry and media integrity."""
        raise NotImplementedError

    async def score(self, aggregated_telemetry: dict[str, Any], policy: Any) -> dict[str, Any]:
        """Compute weighted dimension scores and overall production readiness score."""
        raise NotImplementedError
ZOOMING = "zoom"
