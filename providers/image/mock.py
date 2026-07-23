import os
import random
import uuid
from typing import Any
from providers.registry import BaseProvider
from providers.image.interface import ImageProvider

class MockImageProvider(BaseProvider, ImageProvider):
    """Mock Image Provider generating placeholder images and metadata for automated testing."""

    @property
    def name(self) -> str:
        return "MockImage"

    def __init__(self) -> None:
        self.output_dir = "artifacts/images"
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate(self, prompt: str, aspect_ratio: str, options: dict[str, Any]) -> dict[str, Any]:
        filename = f"scene_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(self.output_dir, filename)

        # Write dummy binary PNG signature to make the file real on disk
        with open(filepath, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xff\xa5\x00\x00\x00\x00IEND\xaeB`\x82")

        return {
            "local_path": filepath,
            "prompt": prompt,
            "storage_key": f"images/{filename}",
            "public_url": f"https://cdn.aates.internal/images/{filename}",
            "thumbnail_url": f"https://cdn.aates.internal/thumbnails/{filename}",
            "preview_url": f"https://cdn.aates.internal/previews/{filename}",
            "seed": random.randint(100000, 999999),
            "model": "mock-sdxl-v2",
            "model_version": "2.0.0",
            "prompt_version": "v1.2",
            "generation_duration_sec": 0.45,
            "camera_angle": options.get("camera_angle", "Medium Shot"),
            "lighting": options.get("lighting", "Studio Neon"),
            "background": options.get("background", "Tech Laboratory"),
            "emotion": options.get("emotion", "Excitement"),
            "style": options.get("style", "3D Render"),
            "color_palette": ["#0F172A", "#6366F1", "#EC4899"],
            "quality_score": round(random.uniform(0.75, 0.98), 2)
        }

    async def regenerate(self, prompt: str, aspect_ratio: str, options: dict[str, Any]) -> dict[str, Any]:
        res = await self.generate(prompt, aspect_ratio, options)
        res["quality_score"] = round(random.uniform(0.85, 0.99), 2)
        return res

    async def upscale(self, image_path: str) -> str:
        # Simulate upscaling by returning the same file or copying it
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Source image {image_path} not found for upscaling.")
        return image_path

    async def variation(self, image_path: str) -> str:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Source image {image_path} not found for variation.")
        return image_path
