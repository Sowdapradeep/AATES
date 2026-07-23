import logging
import base64
import random
import os
from typing import Any, List
import httpx
from providers.registry import BaseProvider
from providers.image.interface import ImageProvider
from core.config.settings import settings

logger = logging.getLogger("stability_image")

class StabilityImageProvider(BaseProvider, ImageProvider):
    """Production Stability AI Image Provider with base64 decoder and local storage saver."""

    @property
    def name(self) -> str:
        return "StabilityAI"

    @property
    def capabilities(self) -> List[str]:
        return ["image_generation", "negative_prompts", "seed_tracking", "style_presets"]

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.ai.stability_api_key
        self.cost_per_generation = 0.03 # SDXL average cost per image

    async def generate_image(self, prompt: str, seed: int | None = None, **kwargs: Any) -> dict[str, Any]:
        """Triggers Stability AI image generation with mock fallback."""
        actual_seed = seed if seed is not None else random.randint(1000, 9999)
        
        if settings.app.env == "testing" or self.api_key == "mock":
            logger.info("Stability AI in testing mode or key set to mock. Returning Mock Image asset.")
            return {
                "storage_location": f"file:///{os.path.abspath(f'./storage/stills/frame-{actual_seed}.png')}",
                "seed": actual_seed,
                "cost": self.cost_per_generation,
                "provider": "StabilityAI",
                "model": "SDXL-1.0-Mock",
                "prompt_version": "v1.0.0",
                "checksum": f"sha256-mockimage-{actual_seed}"
            }

        # Live Stability AI API call
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [
                {"text": prompt, "weight": 1.0}
            ],
            "cfg_scale": kwargs.get("cfg_scale", 7.0),
            "height": kwargs.get("height", 1024),
            "width": kwargs.get("width", 1024),
            "samples": 1,
            "steps": kwargs.get("steps", 30),
            "seed": actual_seed
        }
        
        # Support negative prompts if provided
        if "negative_prompt" in kwargs:
            payload["text_prompts"].append({"text": kwargs["negative_prompt"], "weight": -1.0})

        timeout = httpx.Timeout(45.0, connect=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Decode generated image and save to disk
            artifacts = data.get("artifacts", [])
            if not artifacts:
                raise ValueError("No image artifacts returned from Stability API.")
                
            img_b64 = artifacts[0].get("base64")
            img_bytes = base64.b64decode(img_b64)
            
            # Save file locally in storage directory
            output_dir = "./storage/stills"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"frame-{actual_seed}.png")
            
            with open(output_path, "wb") as f:
                f.write(img_bytes)
                
            import hashlib
            checksum = hashlib.sha256(img_bytes).hexdigest()
            abs_path = os.path.abspath(output_path)
            
            logger.info(f"Stability AI image generated and saved to {abs_path}")
            return {
                "storage_location": f"file:///{abs_path}",
                "seed": actual_seed,
                "cost": self.cost_per_generation,
                "provider": "StabilityAI",
                "model": "stable-diffusion-xl-1024-v1-0",
                "prompt_version": "v1.0.0",
                "checksum": f"sha256-{checksum[:16]}"
            }
