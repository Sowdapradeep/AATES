from typing import Any, List

class ThumbnailProvider:
    """Abstract interface contract for all AI Thumbnail engines."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def capabilities(self) -> List[str]:
        return ["frame_selection", "layout_composition", "text_rendering", "quality_scoring"]

    def supports_frame_extraction(self) -> bool:
        return True

    def supports_generative_composition(self) -> bool:
        return False

    def supports_scoring(self) -> bool:
        return True

    async def select_frame(self, video_pkg: Any, image_pkg: Any, scene_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Weighted selection of keyframes/high-res assets based on motion, resolution, and emotional peaks."""
        raise NotImplementedError

    async def analyze_frame(self, frame_path: str) -> dict[str, Any]:
        """Extract blur score, contrast ratio, face count/confidence, OCR result, saliency map, and color histogram."""
        raise NotImplementedError

    async def compose(self, frame_path: str, text_hierarchy: dict[str, Any], layout_type: str, style_profile: dict[str, Any]) -> dict[str, Any]:
        """Compose thumbnail variant spec combining frame, text hierarchy, logo, and layout grid."""
        raise NotImplementedError

    async def render(self, composition_spec: dict[str, Any], output_path: str) -> dict[str, Any]:
        """Render final high-resolution thumbnail asset file."""
        raise NotImplementedError

    async def score(self, image_path: str, text_hierarchy: dict[str, Any], style_profile: dict[str, Any]) -> dict[str, Any]:
        """Compute visual clarity, contrast, readability, rule-of-thirds, heuristic and learned CTR prediction scores."""
        raise NotImplementedError
ZOOMING = "zoom"
