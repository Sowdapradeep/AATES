from abc import ABC, abstractmethod
from typing import Any


class PublishProvider(ABC):
    """Abstract interface for all publishing providers.

    Business logic must never depend directly on any platform-specific SDK.
    Inject a concrete provider to the engines to switch platforms.
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Returns the canonical platform identifier (e.g. 'instagram_reel')."""

    @abstractmethod
    async def upload(
        self,
        master_reel_path: str,
        caption: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Upload a completed Master Reel to the target platform.

        Must return:
        {
            "external_post_id": str,
            "status": "success" | "failed",
            "error_message": str | None,
            "provider": str,
        }
        """

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Return current provider availability metrics.

        Must return:
        {
            "is_available": bool,
            "latency_ms": float,
            "error_rate": float,
            "success_rate": float,
        }
        """
