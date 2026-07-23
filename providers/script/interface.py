from typing import Any

class ScriptProvider:
    """Base interface for all Script Generation LLM engine providers."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    async def generate(self, knowledge_package: dict[str, Any], platform: str, language: str) -> dict[str, Any]:
        """Convert a structured knowledge package into a formatted creative script package."""
        raise NotImplementedError

    async def review(self, script_data: dict[str, Any], platform: str) -> dict[str, Any]:
        """Evaluate a generated script against quality metrics and return structured score & feedback."""
        raise NotImplementedError

    async def improve(self, script_data: dict[str, Any], review_report: dict[str, Any], platform: str) -> dict[str, Any]:
        """Optimize targeted weak sections of the script based on review comments."""
        raise NotImplementedError
