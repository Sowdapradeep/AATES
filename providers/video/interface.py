from typing import Any, List

class VideoProvider:
    """Abstract interface contract for all downstream Video composition renderers."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def capabilities(self) -> List[str]:
        return ["video_generation"]

    def supports_motion(self) -> bool:
        return True

    def supports_transitions(self) -> bool:
        return True

    def supports_gpu(self) -> bool:
        return False

    def supports_preview(self) -> bool:
        return True

    def supports_subtitles(self) -> bool:
        return False

    async def build_timeline(self, script_pkg: Any, image_pkg: Any, voice_pkg: Any) -> list[dict[str, Any]]:
        """Construct a sequential SceneGraph and timeline markers list from script, image, and voice packages."""
        raise NotImplementedError

    async def render_scene(self, scene_data: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
        """Synthesize scene video clip applying Ken Burns motion presets and transition parameters."""
        raise NotImplementedError

    async def render_video(self, scenes: list[dict[str, Any]], options: dict[str, Any]) -> dict[str, Any]:
        """Merge/Concat individual scene clips and voice narration tracks into the final MP4 container."""
        raise NotImplementedError

    async def render_preview(self, video_path: str) -> str:
        """Create a low-resolution lightweight preview copy of the rendered final video."""
        raise NotImplementedError
ZOOMING = "zoom"
