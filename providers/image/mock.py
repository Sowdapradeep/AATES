import random
from typing import Any
from providers.image.interface import ImageProvider

class MockImageProvider(ImageProvider):
    """Mock Image Provider simulating frame generations."""
    
    async def generate_image(self, prompt: str, seed: int | None = None, **kwargs: Any) -> dict[str, Any]:
        actual_seed = seed if seed is not None else random.randint(1000, 9999)
        # Return mock S3 mock location path and generation fee cost
        return {
            "storage_location": f"s3://aates-assets/stills/frame-{actual_seed}.png",
            "seed": actual_seed,
            "cost": 0.03,
            "provider": "MockImageAI",
            "model": "Still-Generator-v3",
            "prompt_version": "v1.0.0",
            "checksum": f"sha256-mockimage-{actual_seed}"
        }
