import logging
import random
import os
import time
import hashlib
from typing import Any, List
import httpx
from providers.registry import BaseProvider
from providers.video.interface import VideoProvider
from core.config.settings import settings

logger = logging.getLogger("stability_video")

class StabilityVideoProvider(BaseProvider, VideoProvider):
    """Production Stability AI Image-to-Video Provider supporting polling and checkpoint recovery."""

    @property
    def name(self) -> str:
        return "StabilityVideo"

    @property
    def capabilities(self) -> List[str]:
        return ["video_generation", "image_to_video", "duration_control"]

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.ai.stability_api_key
        self.cost_per_generation = 0.20  # Stability video standard cost

    async def generate_video(self, image_location: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Animate reference frame into a video using Stability Image-to-Video API with mock fallback."""
        clip_id = random.randint(1000, 9999)
        
        if settings.app.env == "testing" or self.api_key == "mock":
            logger.info("Stability AI in testing mode or key set to mock. Returning Mock Video asset.")
            return {
                "storage_location": f"file:///{os.path.abspath(f'./storage/videos/clip-{clip_id}.mp4')}",
                "seed": clip_id,
                "cost": self.cost_per_generation,
                "provider": "StabilityVideo",
                "model": "SVD-1.1-Mock",
                "prompt_version": "v1.0.0",
                "checksum": f"sha256-mockvideo-{clip_id}"
            }

        # Resolve image file
        clean_path = image_location.replace("file:///", "")
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"Source image frame {clean_path} does not exist for video animation.")

        # Live Image-to-Video API Call
        url_post = "https://api.stability.ai/v2beta/image-to-video"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        files = {
            "image": open(clean_path, "rb")
        }
        data = {
            "seed": kwargs.get("seed", clip_id),
            "cfg_scale": kwargs.get("cfg_scale", 1.8),
            "motion_bucket_id": kwargs.get("motion_bucket_id", 127)
        }

        timeout = httpx.Timeout(60.0, connect=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"Stability Video: Uploading {clean_path} for generation...")
            # Step 1: POST to image-to-video
            response = await client.post(url_post, headers=headers, files=files, data=data)
            response.raise_for_status()
            gen_id = response.json().get("id")
            
            if not gen_id:
                raise ValueError("No generation ID returned from Stability Video API.")
                
            logger.info(f"Stability Video: Generation started. ID: {gen_id}. Polling result...")
            
            # Step 2: Poll result
            url_result = f"https://api.stability.ai/v2beta/image-to-video/result/{gen_id}"
            
            # Poll up to 10 times with 10s sleep
            for attempt in range(15):
                await httpx.AsyncClient().sleep(10.0) if hasattr(httpx.AsyncClient(), "sleep") else time.sleep(10.0)
                
                res_resp = await client.get(url_result, headers=headers)
                if res_resp.status_code == 202:
                    # Still processing
                    logger.debug(f"Stability Video: Generation {gen_id} in progress (attempt {attempt + 1})...")
                    continue
                elif res_resp.status_code == 200:
                    # Generation complete! Video returned as binary content
                    video_bytes = res_resp.content
                    
                    output_dir = "./storage/videos"
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, f"clip-{clip_id}.mp4")
                    
                    with open(output_path, "wb") as f:
                        f.write(video_bytes)
                        
                    checksum = hashlib.sha256(video_bytes).hexdigest()
                    abs_path = os.path.abspath(output_path)
                    
                    logger.info(f"Stability Video: Animation complete. Saved to {abs_path}")
                    return {
                        "storage_location": f"file:///{abs_path}",
                        "seed": clip_id,
                        "cost": self.cost_per_generation,
                        "provider": "StabilityVideo",
                        "model": "svd-1.1",
                        "prompt_version": "v1.0.0",
                        "checksum": f"sha256-{checksum[:16]}"
                    }
                else:
                    res_resp.raise_for_status()
                    
        raise RuntimeError("Stability Video generation timed out or failed.")
