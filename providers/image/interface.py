from typing import Any, List

class ImageProvider:
    """Base interface for all AI Image Generation engines."""

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def capabilities(self) -> List[str]:
        return ["image_generation"]

    async def generate(self, prompt: str, aspect_ratio: str, options: dict[str, Any]) -> dict[str, Any]:
        """Generate a single scene visual asset from a prompt."""
        raise NotImplementedError

    async def regenerate(self, prompt: str, aspect_ratio: str, options: dict[str, Any]) -> dict[str, Any]:
        """Regenerate a specific scene visual asset with new configurations or seeds."""
        raise NotImplementedError

    async def upscale(self, image_path: str) -> str:
        """Upscale an existing generated image and return the upscaled file path."""
        raise NotImplementedError

    async def variation(self, image_path: str) -> str:
        """Generate a variation of the given image path."""
        raise NotImplementedError
