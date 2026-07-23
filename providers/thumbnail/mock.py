import os
import uuid
from typing import Any, List
from providers.thumbnail.interface import ThumbnailProvider

class MockThumbnailProvider(ThumbnailProvider):
    """Mock Thumbnail Provider generating synthetic thumbnail files and test scores."""

    @property
    def name(self) -> str:
        return "MockThumbnailEngine"

    def __init__(self) -> None:
        self.output_dir = "artifacts/thumbnails"
        os.makedirs(self.output_dir, exist_ok=True)

    async def select_frame(self, video_pkg: Any, image_pkg: Any, scene_data: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "source_type": "mock",
            "scene_number": 1,
            "frame_path": "artifacts/thumbnails/mock_frame.png",
            "quality_weight": 0.90
        }

    async def analyze_frame(self, frame_path: str) -> dict[str, Any]:
        return {
            "blur_score": 0.05,
            "brightness": 0.65,
            "contrast_ratio": 6.2,
            "entropy": 7.4,
            "dominant_colors": ["#000000", "#FFFFFF"],
            "face_count": 1,
            "face_confidence": 0.95,
            "object_regions": [],
            "saliency_map": {},
            "ocr_result": {"text": "MOCK TEXT", "confidence": 0.95},
            "edge_density": 0.45,
            "color_histogram": {}
        }

    async def compose(self, frame_path: str, text_hierarchy: dict[str, Any], layout_type: str, style_profile: dict[str, Any]) -> dict[str, Any]:
        return {
            "layout_type": layout_type,
            "frame_path": frame_path,
            "primary_hook": text_hierarchy.get("primary_hook", "MOCK HOOK"),
            "secondary_hook": text_hierarchy.get("secondary_hook", "Mock Subtitle"),
            "badge_text": "MOCK",
            "brand_label": "AATES"
        }

    async def render(self, composition_spec: dict[str, Any], output_path: str) -> dict[str, Any]:
        with open(output_path, "wb") as f:
            f.write(b"MOCK_THUMBNAIL_DATA")
        return {
            "output_path": output_path,
            "width": 1280,
            "height": 720,
            "format": "png",
            "file_size_bytes": 512
        }

    async def score(self, image_path: str, text_hierarchy: dict[str, Any], style_profile: dict[str, Any]) -> dict[str, Any]:
        return {
            "contrast_score": 0.90,
            "sharpness_score": 0.95,
            "face_visibility_score": 0.90,
            "subject_prominence_score": 0.88,
            "text_readability_score": 0.94,
            "color_harmony_score": 0.91,
            "rule_of_thirds_score": 0.89,
            "emotion_score": 0.87,
            "brand_consistency_score": 0.96,
            "heuristic_score": 0.92,
            "learned_score": 0.94,
            "overall_score": 0.93,
            "ctr_prediction_score": 0.93
        }
ZOOMING = "zoom"
