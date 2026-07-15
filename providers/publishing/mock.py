import random
from typing import Any
from providers.publishing.interface import PublishProvider


class MockInstagramPublisher(PublishProvider):
    """Mock Instagram Reels publisher simulating API upload lifecycle."""

    @property
    def platform_name(self) -> str:
        return "instagram_reel"

    async def upload(self, master_reel_path: str, caption: str, metadata: dict[str, Any]) -> dict[str, Any]:
        post_id = f"ig_post_{random.randint(10000, 99999)}"
        return {
            "external_post_id": post_id,
            "status": "success",
            "error_message": None,
            "provider": "MockInstagramPublisher",
            "url": f"https://www.instagram.com/reels/{post_id}/"
        }

    async def health_check(self) -> dict[str, Any]:
        return {
            "is_available": True,
            "latency_ms": round(random.uniform(80, 250), 2),
            "error_rate": 0.01,
            "success_rate": 0.99
        }


class MockYouTubePublisher(PublishProvider):
    """Mock YouTube Shorts publisher simulating API upload lifecycle."""

    @property
    def platform_name(self) -> str:
        return "youtube_short"

    async def upload(self, master_reel_path: str, caption: str, metadata: dict[str, Any]) -> dict[str, Any]:
        video_id = f"yt_{random.randint(10000, 99999)}"
        return {
            "external_post_id": video_id,
            "status": "success",
            "error_message": None,
            "provider": "MockYouTubePublisher",
            "url": f"https://www.youtube.com/shorts/{video_id}"
        }

    async def health_check(self) -> dict[str, Any]:
        return {
            "is_available": True,
            "latency_ms": round(random.uniform(120, 400), 2),
            "error_rate": 0.02,
            "success_rate": 0.98
        }
