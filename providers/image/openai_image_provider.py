import logging
import base64
import random
import os
import hashlib
from typing import Any, List
import httpx
from providers.registry import BaseProvider
from providers.image.interface import ImageProvider
from core.config.settings import settings

logger = logging.getLogger("openai_image")

class OpenAIImageProvider(BaseProvider, ImageProvider):
    """Production OpenAI DALL-E 3 Image Provider with base64 decoder and local storage saver."""

    @property
    def name(self) -> str:
        return "OpenAIImages"

    @property
    def capabilities(self) -> List[str]:
        return ["image_generation", "dalle_3", "high_resolution"]

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.ai.openai_api_key
        self.cost_per_generation = 0.04  # DALL-E 3 standard cost per image

    async def generate_image(self, prompt: str, seed: int | None = None, **kwargs: Any) -> dict[str, Any]:
        """Triggers OpenAI DALL-E 3 image generation with mock fallback."""
        actual_seed = seed if seed is not None else random.randint(1000, 9999)
        
        if not self.api_key or self.api_key == "mock" or settings.app.env == "testing":
            logger.info("OpenAI API Key not configured. Returning Mock Image asset.")
            return {
                "storage_location": f"file:///{os.path.abspath(f'./storage/stills/frame-{actual_seed}.png')}",
                "seed": actual_seed,
                "cost": self.cost_per_generation,
                "provider": "OpenAIImages",
                "model": "DALL-E-3-Mock",
                "prompt_version": "v1.0.0",
                "checksum": f"sha256-mockimage-{actual_seed}"
            }

        # Live DALL-E 3 API call
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": kwargs.get("size", "1024x1024"),
            "response_format": "b64_json"
        }

        timeout = httpx.Timeout(60.0, connect=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            img_data = data.get("data", [])
            if not img_data:
                raise ValueError("No image data returned from OpenAI API.")
                
            img_b64 = img_data[0].get("b64_json")
            img_bytes = base64.b64decode(img_b64)
            
            # Save file locally
            output_dir = "./storage/stills"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"frame-{actual_seed}.png")
            
            with open(output_path, "wb") as f:
                f.write(img_bytes)
                
            checksum = hashlib.sha256(img_bytes).hexdigest()
            abs_path = os.path.abspath(output_path)
            
            logger.info(f"OpenAI DALL-E 3 image generated and saved to {abs_path}")
            return {
                "storage_location": f"file:///{abs_path}",
                "seed": actual_seed,
                "cost": self.cost_per_generation,
                "provider": "OpenAIImages",
                "model": "dall-e-3",
                "prompt_version": "v1.0.0",
                "checksum": f"sha256-{checksum[:16]}"
            }
