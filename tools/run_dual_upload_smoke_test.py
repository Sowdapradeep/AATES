import os
import sys
import time
import json
import base64
import logging
import asyncio
import tempfile
from datetime import datetime, timezone
from typing import Any

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.settings import settings
from core.config.secrets import fetch_and_apply_secrets
from providers.publishing.youtube import YouTubePublisher
from providers.publishing.instagram import InstagramPublishingProvider

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("dual_upload_smoke_test")

MINIMAL_MP4_BASE64 = (
    "AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAAr9tZGF0AAACoAYF"
    "//+///AAAAMmF2Y0MBZAAK/+EAGWdkAAqs2V+WXAWyAAADAAIAAAMAYB4kSywBAAZo6+PLIs"
    "AAAAAYc3R0cwAAAAAAAAABAAAAAQAAAgAAAAAcc3RzYwAAAAAAAAABAAAAAQAAAAEAAAAB"
    "AAAAFHN0c3oAAAAAAAACtwAAAAEAAAAUc3RjbwAAAAAAAAABAAAAMAAAAGJ1ZHRhAAAAWm"
    "1ldGEAAAAAAAAAIWhkbHIAAAAAAAAAAG1kaXJhcHBsAAAAAAAAAAAAAAAALWlsc3QAAAAl"
    "qXRvbwAAAB1kYXRhAAAAAQAAAABMYXZmNTQuNjMuMTA0"
)

async def main():
    settings.app.env = "development"
    settings.aws.secrets_manager_enabled = True
    
    logger.info("Initializing AWS credentials and fetching secrets...")
    fetch_and_apply_secrets()
    
    # Check command line flags to delete video or not (default: retain)
    delete_video = "--delete-video" in sys.argv
    
    import cv2
    import numpy as np
    
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        # Generate a valid 3-second black video using OpenCV
        logger.info("Generating a valid 3-second MP4 video using OpenCV...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_path, fourcc, 30.0, (640, 480))
        for i in range(90):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f"AATES Dual Upload Test {i}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            out.write(frame)
        out.release()
        
        logger.info(f"Playable 3-second MP4 video generated at: {temp_path} (Size: {os.path.getsize(temp_path)} bytes)")
        
        # 1. YouTube Upload
        logger.info("---------- YOUTUBE UPLOAD STARTED ----------")
        yt_publisher = YouTubePublisher()
        yt_metadata = {
            "title": f"AATES Dual Upload Test {int(time.time())}",
            "description": "Tamil content dual upload verification.",
            "tags": ["Tamil", "AATES", "SmokeTest", "AI"],
            "categoryId": "24",
            "language": "ta",
            "privacy": "private",
            "safe_production_mode": False
        }
        yt_res = await yt_publisher.upload(temp_path, yt_metadata["description"], yt_metadata)
        yt_video_id = yt_res.get("video_id")
        logger.info(f"YouTube Upload Finished. Video ID: {yt_video_id}")
        logger.info(f"YouTube Video URL: https://www.youtube.com/watch?v={yt_video_id}")
        
        # 2. Instagram Upload
        logger.info("---------- INSTAGRAM UPLOAD STARTED ----------")
        ig_publisher = InstagramPublishingProvider()
        ig_metadata = {
            "dry_run": False,
            "safe_production_mode": False
        }
        ig_res = await ig_publisher.upload(
            master_reel_path=temp_path,
            caption=f"Tamil content dual upload verification. #AATES #AI {int(time.time())}",
            metadata=ig_metadata
        )
        logger.info(f"Instagram Upload Finished. Result: {json.dumps(ig_res, indent=2)}")
        
        if delete_video:
            logger.info("Cleanup requested via --delete-video. Deleting uploaded assets...")
            if yt_video_id:
                await yt_publisher.delete_video(yt_video_id)
                logger.info(f"YouTube Video {yt_video_id} deleted successfully.")
        else:
            logger.info("NO cleanup requested. Videos retained on both platforms.")
            
        logger.info("DUAL UPLOAD SMOKE TEST COMPLETED SUCCESSFULLY.")
        
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info("Temporary local video file cleaned up.")
            except Exception as e:
                logger.warning(f"Could not delete temp local file: {e}")

if __name__ == "__main__":
    asyncio.run(main())
