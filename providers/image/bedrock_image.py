import logging
import random
import os
import json
import base64
import hashlib
from typing import Any, List
from providers.registry import BaseProvider, model_registry
from providers.image.interface import ImageProvider
from core.config.settings import settings

logger = logging.getLogger("bedrock_image")

class BedrockImageProvider(BaseProvider, ImageProvider):
    """Production AWS Bedrock Image Generation Provider (SDXL / Titan Image)."""

    @property
    def name(self) -> str:
        return "BedrockImage"

    @property
    def capabilities(self) -> List[str]:
        return ["image_generation", "seed_tracking", "style_presets"]

    def __init__(self) -> None:
        self.bedrock_client = None
        self.cost_per_image = 0.03
        
        try:
            import boto3
            self.bedrock_client = boto3.client("bedrock-runtime", region_name=settings.ai.bedrock_region)
            logger.info("Bedrock Runtime client for Image generation initialized.")
        except Exception as e:
            logger.warning(f"Bedrock Runtime for Image failed to initialize: {str(e)}. Mock fallback enabled.")

    async def generate_image(self, prompt: str, seed: int | None = None, **kwargs: Any) -> dict[str, Any]:
        """Generate reference frame using Bedrock Image models with mock fallback support."""
        actual_seed = seed if seed is not None else random.randint(1000, 9999)
        model_id = model_registry.select_best_model_for_capability("image_generation")
        if not model_id:
            model_id = "amazon.titan-image-generator-v1"

        if not self.bedrock_client or settings.app.env == "testing":
            logger.info(f"Bedrock: Test environment or client offline. Simulating {model_id} image generation.")
            return {
                "storage_location": f"file:///{os.path.abspath(f'./storage/stills/frame-{actual_seed}.png')}",
                "seed": actual_seed,
                "cost": self.cost_per_image,
                "provider": "BedrockImage",
                "model": model_id,
                "prompt_version": "v1.0.0",
                "checksum": f"sha256-mockimage-{actual_seed}"
            }

        # Live AWS Bedrock Image generation
        try:
            # Build payload depending on model type (stability vs amazon)
            if "stability" in model_id:
                payload = {
                    "text_prompts": [{"text": prompt, "weight": 1.0}],
                    "cfg_scale": kwargs.get("cfg_scale", 7.0),
                    "steps": kwargs.get("steps", 30),
                    "seed": actual_seed
                }
            else:
                # Default to Amazon Titan format
                payload = {
                    "taskType": "TEXT_IMAGE",
                    "textToImageParams": {"text": prompt},
                    "imageGenerationConfig": {
                        "numberOfImages": 1,
                        "quality": "standard",
                        "width": kwargs.get("width", 1024),
                        "height": kwargs.get("height", 1024),
                        "cfgScale": kwargs.get("cfg_scale", 8.0),
                        "seed": actual_seed
                    }
                }

            import asyncio
            loop = asyncio.get_event_loop()
            
            def call_invoke_model():
                return self.bedrock_client.invoke_model(
                    modelId=model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(payload)
                )

            logger.info(f"Bedrock Image: Invoking model {model_id}...")
            response = await loop.run_in_executor(None, call_invoke_model)
            response_body = json.loads(response.get("body").read())
            
            # Extract image base64
            if "stability" in model_id:
                artifacts = response_body.get("artifacts", [])
                if not artifacts:
                    raise ValueError("No image artifacts returned from Stability Bedrock API.")
                img_b64 = artifacts[0].get("base64")
            else:
                images = response_body.get("images", [])
                if not images:
                    raise ValueError("No images returned from Titan Bedrock API.")
                img_b64 = images[0]

            img_bytes = base64.b64decode(img_b64)
            
            # Save file locally
            output_dir = "./storage/stills"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"frame-{actual_seed}.png")
            
            with open(output_path, "wb") as f:
                f.write(img_bytes)
                
            checksum = hashlib.sha256(img_bytes).hexdigest()
            abs_path = os.path.abspath(output_path)
            
            logger.info(f"Bedrock Image: Asset generated and saved to {abs_path}")
            return {
                "storage_location": f"file:///{abs_path}",
                "seed": actual_seed,
                "cost": self.cost_per_image,
                "provider": "BedrockImage",
                "model": model_id,
                "prompt_version": "v1.0.0",
                "checksum": f"sha256-{checksum[:16]}"
            }
            
        except Exception as e:
            logger.error(f"Bedrock Image invocation failed: {str(e)}")
            raise e
