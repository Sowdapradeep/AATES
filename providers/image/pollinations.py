import logging
import os
import uuid
import time
import urllib.parse
from typing import Any, List
import httpx
from providers.registry import BaseProvider
from providers.image.interface import ImageProvider

logger = logging.getLogger("pollinations_image")

# Aspect ratio to width/height mapping
ASPECT_RATIO_MAP = {
    "16:9":  (1280, 720),
    "9:16":  (720, 1280),
    "1:1":   (1024, 1024),
    "4:3":   (1024, 768),
    "3:4":   (768, 1024),
    "21:9":  (1920, 816),
}


class PollinationsImageProvider(BaseProvider, ImageProvider):
    """
    Free, keyless image generation using Pollinations.AI (FLUX-based model).
    No API key required. Simple GET request — returns a JPEG image directly.
    """

    @property
    def name(self) -> str:
        return "PollinationsImage"

    @property
    def capabilities(self) -> List[str]:
        return ["image_generation", "seed_tracking", "style_presets"]

    def __init__(self) -> None:
        self.output_dir = "artifacts/images"
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_url = "https://image.pollinations.ai/prompt"

    async def generate(self, prompt: str, aspect_ratio: str, options: dict[str, Any]) -> dict[str, Any]:
        """Generate a cinematic scene still via Pollinations.AI (free FLUX model)."""
        seed = options.get("seed", int(time.time()) % 100000)
        width, height = ASPECT_RATIO_MAP.get(aspect_ratio, (1280, 720))

        # Build a rich, cinematic prompt by injecting style metadata
        camera_angle = options.get("camera_angle", "Medium Wide Shot")
        lighting = options.get("lighting", "Natural Cinematic")
        style = options.get("style", "Realistic")
        emotion = options.get("emotion", "Neutral")

        enhanced_prompt = (
            f"{prompt}, {camera_angle}, {lighting} lighting, {style} style, "
            f"cinematic, photorealistic, 8k ultra HD, film grain"
        )

        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        url = (
            f"{self.base_url}/{encoded_prompt}"
            f"?width={width}&height={height}"
            f"&seed={seed}&model=flux&nologo=true&enhance=true"
        )

        start = time.monotonic()
        try:
            timeout = httpx.Timeout(60.0, connect=15.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)

            if response.status_code != 200:
                raise RuntimeError(
                    f"Pollinations API error (status {response.status_code}): {response.text[:300]}"
                )

            duration = time.monotonic() - start
            image_bytes = response.content

            if len(image_bytes) < 1000:
                raise ValueError(f"Pollinations returned suspiciously small response ({len(image_bytes)} bytes)")

            filename = f"pollinations_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(image_bytes)

            logger.info(
                f"Pollinations image generated: {filename} ({len(image_bytes):,} bytes, {duration:.2f}s)"
            )

            return {
                "local_path": filepath,
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "storage_key": f"images/{filename}",
                "public_url": f"https://cdn.aates.internal/images/{filename}",
                "thumbnail_url": f"https://cdn.aates.internal/thumbnails/{filename}",
                "preview_url": f"https://cdn.aates.internal/previews/{filename}",
                "seed": seed,
                "model": "flux",
                "model_version": "1.0",
                "prompt_version": "v1.0",
                "generation_duration_sec": duration,
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "camera_angle": camera_angle,
                "lighting": lighting,
                "background": options.get("background", "Outdoor"),
                "emotion": emotion,
                "style": style,
                "color_palette": ["#111827", "#3B82F6"],
                "quality_score": 0.85,
            }

        except Exception as e:
            logger.error(f"Pollinations image generation failed: {str(e)}")
            raise

    async def regenerate(self, prompt: str, aspect_ratio: str, options: dict[str, Any]) -> dict[str, Any]:
        """Regenerate with a new random seed."""
        new_options = {**options, "seed": int(time.time()) % 100000}
        return await self.generate(prompt, aspect_ratio, new_options)

    async def upscale(self, image_path: str) -> str:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Source image {image_path} not found.")
        return image_path

    async def variation(self, image_path: str) -> str:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Source image {image_path} not found.")
        return image_path
