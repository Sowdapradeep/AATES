from typing import Any, List

class SubtitleProvider:
    """Abstract interface contract for all AI Subtitle engines."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def capabilities(self) -> List[str]:
        return ["subtitle_generation", "formatting", "styling"]

    def supports_alignment(self) -> bool:
        return True

    def supports_asr(self) -> bool:
        return False

    def supports_style(self) -> bool:
        return True

    async def generate(self, voice_pkg: Any, video_pkg: Any, options: dict[str, Any]) -> dict[str, Any]:
        """Extract word/sentence alignments or execute ASR to produce raw caption timelines."""
        raise NotImplementedError

    async def segment(self, text: str, word_timings: list[dict[str, Any]], options: dict[str, Any]) -> list[dict[str, Any]]:
        """Split text into optimal caption blocks respecting CPS, CPL, WPM, and line limits."""
        raise NotImplementedError

    async def optimize(self, segments: list[dict[str, Any]], style_profile: dict[str, Any]) -> list[dict[str, Any]]:
        """Refine line breaks, timing tolerances, and style properties."""
        raise NotImplementedError

    async def export(self, segments: list[dict[str, Any]], format_type: str, output_path: str, style_profile: dict[str, Any] = None) -> str:
        """Write SRT, WebVTT, ASS, or JSON timeline files to disk."""
        raise NotImplementedError
ZOOMING = "zoom"
