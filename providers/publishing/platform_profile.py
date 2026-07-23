from typing import Any, List, Optional
from pydantic import BaseModel

class PlatformCapabilities(BaseModel):
    """Immutable capabilities for a social media publishing platform."""
    platform_name: str
    supports_video: bool = True
    supports_images: bool = True
    supports_carousel: bool = False
    supports_scheduling: bool = True
    supports_alt_text: bool = True
    supports_insights: bool = True
    supports_cover_image: bool = True
    supports_hashtags: bool = True
    supports_mentions: bool = True

class PlatformProfile(BaseModel):
    """Configurable publishing specification profile for target platform media types."""
    profile_id: str
    platform_name: str
    media_type: str  # Reels, Feed, Shorts, Longform
    aspect_ratios: List[str]  # e.g., ["9:16"], ["1:1", "4:5"]
    min_resolution: str = "600x600"
    max_resolution: str = "1920x1080"
    max_duration_sec: float
    min_duration_sec: float = 1.0
    max_file_size_mb: int = 500
    supported_codecs: List[str] = ["h264", "hevc"]
    supported_containers: List[str] = ["mp4", "mov"]
    max_caption_length: int = 2200
    max_hashtags: int = 30
    cover_image_required: bool = False
    supported_metrics: List[str] = ["views", "reach", "impressions", "likes", "comments", "shares", "saves", "profile_visits"]

# Predefined Platform Capabilities
INSTAGRAM_CAPABILITIES = PlatformCapabilities(
    platform_name="instagram",
    supports_carousel=True,
    supports_alt_text=True,
    supports_cover_image=True
)

YOUTUBE_CAPABILITIES = PlatformCapabilities(
    platform_name="youtube",
    supports_carousel=False,
    supports_alt_text=False,
    supports_cover_image=True
)

# Predefined Platform Profiles
INSTAGRAM_REELS_PROFILE = PlatformProfile(
    profile_id="instagram_reels",
    platform_name="instagram",
    media_type="Reels",
    aspect_ratios=["9:16"],
    max_resolution="1080x1920",
    max_duration_sec=90.0,
    max_caption_length=2200,
    max_hashtags=30,
    cover_image_required=True
)

INSTAGRAM_FEED_PROFILE = PlatformProfile(
    profile_id="instagram_feed",
    platform_name="instagram",
    media_type="Feed",
    aspect_ratios=["1:1", "4:5"],
    max_resolution="1080x1350",
    max_duration_sec=60.0,
    max_caption_length=2200,
    max_hashtags=30,
    cover_image_required=False
)

YOUTUBE_SHORTS_PROFILE = PlatformProfile(
    profile_id="youtube_shorts",
    platform_name="youtube",
    media_type="Shorts",
    aspect_ratios=["9:16"],
    max_resolution="1080x1920",
    max_duration_sec=60.0,
    max_caption_length=100,
    max_hashtags=15,
    cover_image_required=False
)

YOUTUBE_LONGFORM_PROFILE = PlatformProfile(
    profile_id="youtube_longform",
    platform_name="youtube",
    media_type="Longform",
    aspect_ratios=["16:9"],
    max_resolution="3840x2160",
    max_duration_sec=43200.0,
    max_caption_length=5000,
    max_hashtags=15,
    cover_image_required=True
)

class PlatformRegistry:
    """Central registry mapping platform capabilities and configurable profiles."""

    def __init__(self) -> None:
        self._capabilities = {
            "instagram": INSTAGRAM_CAPABILITIES,
            "youtube": YOUTUBE_CAPABILITIES
        }
        self._profiles = {
            "instagram_reels": INSTAGRAM_REELS_PROFILE,
            "instagram_feed": INSTAGRAM_FEED_PROFILE,
            "youtube_shorts": YOUTUBE_SHORTS_PROFILE,
            "youtube_longform": YOUTUBE_LONGFORM_PROFILE
        }

    def get_capabilities(self, platform_name: str) -> PlatformCapabilities | None:
        return self._capabilities.get(platform_name.lower())

    def get_profile(self, profile_id: str) -> PlatformProfile | None:
        return self._profiles.get(profile_id.lower())

    def register_profile(self, profile: PlatformProfile) -> None:
        self._profiles[profile.profile_id.lower()] = profile

    def list_profiles_for_platform(self, platform_name: str) -> List[PlatformProfile]:
        return [p for p in self._profiles.values() if p.platform_name.lower() == platform_name.lower()]

platform_registry = PlatformRegistry()
ZOOMING = "zoom"
