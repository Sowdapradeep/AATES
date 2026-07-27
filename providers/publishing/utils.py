import os
import re
import tempfile
import subprocess
import logging
from urllib.parse import urlparse
from core.config.settings import settings

logger = logging.getLogger("aros.publishing.utils")

def ensure_local_file(path: str) -> tuple[str, bool]:
    """Returns (local_path, is_temp).
    If path starts with s3://, downloads the file from S3 to a temporary local path.
    Otherwise, returns the local path as is.
    """
    if path.startswith("s3://"):
        try:
            import boto3
            parsed = urlparse(path)
            bucket = parsed.netloc
            key = parsed.path.lstrip('/')
            
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            logger.info(f"Downloading S3 file {path} to temp local file {temp_path}...")
            s3_client = boto3.client("s3", region_name=settings.aws.region)
            s3_client.download_file(bucket, key, temp_path)
            return temp_path, True
        except Exception as e:
            logger.error(f"Failed to download S3 file: {e}")
            raise
            
    return path, False

def get_video_duration(local_path: str) -> float:
    """Gets duration of a local video file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", local_path
    ]
    try:
        output = subprocess.check_output(cmd, text=True).strip()
        return float(output)
    except Exception as e:
        logger.error(f"Failed to get video duration via ffprobe: {e}")
        # Return 0.0 if not available or fails
        return 0.0

def split_video_to_chunks(local_path: str, chunk_duration_sec: float = 55.0) -> list[str]:
    """Splits local video into segments of chunk_duration_sec using ffmpeg copy.
    Returns list of paths to temporary chunk files.
    """
    duration = get_video_duration(local_path)
    if duration <= 0.0:
        logger.warning(f"Could not determine video duration. Skipping split for {local_path}.")
        return [local_path]
        
    if duration <= 60.0:
        return [local_path]
        
    num_chunks = int(duration // chunk_duration_sec)
    if duration % chunk_duration_sec > 0:
        num_chunks += 1
        
    chunk_paths = []
    logger.info(f"Splitting video of duration {duration:.2f}s into {num_chunks} chunks of {chunk_duration_sec}s")
    
    for i in range(num_chunks):
        start_time = i * chunk_duration_sec
        dur = min(chunk_duration_sec, duration - start_time)
        
        temp_chunk = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        chunk_path = temp_chunk.name
        temp_chunk.close()
        
        cmd = [
            "ffmpeg", "-y", "-ss", str(start_time), "-t", str(dur),
            "-i", local_path, "-c", "copy", chunk_path
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            chunk_paths.append(chunk_path)
        except Exception as e:
            logger.error(f"Failed to split chunk {i}: {e}")
            for p in chunk_paths:
                if os.path.exists(p) and p != local_path:
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            raise RuntimeError(f"FFmpeg split failed: {e}")
            
    return chunk_paths

def parse_episode_number(text: str) -> int:
    """Parses episode number from title or caption text."""
    match = re.search(r'(?:Episode|Ep|E)\s*(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 1

def clean_title_for_part(title: str) -> str:
    """Removes 'Episode X -' or similar prefixes from title to avoid duplication."""
    clean = re.sub(r'^(?:Episode|Ep|E)\s*\d+\s*[-:]\s*', '', title, flags=re.IGNORECASE).strip()
    return clean
