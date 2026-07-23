"""
YouTube Provider — Live YouTube Publishing.

Communicates with YouTube Data API v3 using httpx.
"""
from __future__ import annotations

import os
import json
import logging
import time
from typing import Any
import httpx

from core.config.settings import settings
from providers.publishing.interface import PublishProvider

logger = logging.getLogger("aros.publishing.youtube")


class YouTubePublisher(PublishProvider):
    """Production YouTube Publisher with OAuth 2.0 and Resumable Upload."""
    
    _is_available: bool = True
    _validation_error: str | None = None

    @property
    def platform_name(self) -> str:
        return "youtube_short"

    async def _get_access_token(self) -> str:
        client_id = None
        client_secret = None
        refresh_token = None
        secret_exists = False

        try:
            import boto3
            session = boto3.Session()
            sm_client = session.client("secretsmanager", region_name=settings.aws.region)
            # Check if the secret exists
            sm_client.describe_secret(SecretId=settings.aws.secret_name)
            secret_exists = True
            
            # Fetch the secret
            resp = sm_client.get_secret_value(SecretId=settings.aws.secret_name)
            payload = json.loads(resp["SecretString"])
            client_id = payload.get("youtube_client_id")
            client_secret = payload.get("youtube_client_secret")
            refresh_token = payload.get("youtube_refresh_token")
        except Exception as e:
            logger.warning(f"Could not check Secrets Manager for YouTube credentials: {e}")

        if secret_exists:
            # If the secret exists, we must obtain credentials exclusively from it.
            # Do not silently fall back if required fields are missing.
            if not (client_id and client_secret and refresh_token):
                raise ValueError("YouTube credentials missing in AWS Secrets Manager secret 'aates-production-secrets'")
        else:
            # Fallback to local settings only when Secrets Manager is unavailable
            client_id = settings.publishing.youtube_client_id
            client_secret = settings.publishing.youtube_client_secret
            refresh_token = settings.publishing.youtube_refresh_token

        if not (client_id and client_secret and refresh_token):
            raise ValueError("Required YouTube credentials (client_id, client_secret, refresh_token) are missing")

        # Request new access token from Google (real exchange)
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=15.0
            )
            if res.status_code != 200:
                raise ValueError(f"Failed to refresh YouTube access token: {res.text}")
            return res.json()["access_token"]

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] = None,
        json_data: dict[str, Any] = None,
        content: bytes | Any = None,
        files: dict[str, Any] = None,
        timeout: float = 30.0,
        max_retries: int = 4,
        initial_backoff: float = 2.0
    ) -> httpx.Response:
        """Execute HTTP request to YouTube API with retry on network and transient errors, and token refresh on 401."""
        backoff = initial_backoff
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    if method.upper() == "POST":
                        res = await client.post(url, headers=headers, params=params, json=json_data, files=files, content=content, timeout=timeout)
                    elif method.upper() == "PUT":
                        res = await client.put(url, headers=headers, params=params, json=json_data, content=content, timeout=timeout)
                    elif method.upper() == "GET":
                        res = await client.get(url, headers=headers, params=params, timeout=timeout)
                    elif method.upper() == "DELETE":
                        res = await client.delete(url, headers=headers, params=params, timeout=timeout)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                # Handle expired access token (401)
                if res.status_code == 401:
                    logger.warning("YouTube API returned 401 (Unauthorized). Refreshing access token and retrying...")
                    new_token = await self._get_access_token()
                    headers["Authorization"] = f"Bearer {new_token}"
                    # Retry exactly once immediately
                    continue

                # Handle transient errors (429, 500, 502, 503, 504)
                if res.status_code in (429, 500, 502, 503, 504):
                    if attempt == max_retries - 1:
                        return res
                    logger.warning(f"YouTube API returned transient status {res.status_code}. Retrying in {backoff:.2f}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue

                return res

            except (httpx.TimeoutException, httpx.NetworkError) as err:
                if attempt == max_retries - 1:
                    raise err
                logger.warning(f"YouTube API network error ({type(err).__name__}). Retrying in {backoff:.2f}s... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(backoff)
                backoff *= 2.0

        raise RuntimeError("YouTube API request failed after maximum retries")

    async def upload(
        self,
        master_reel_path: str,
        caption: str,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Upload video to YouTube."""
        # 1. Check dry run
        if metadata.get("dry_run") or os.getenv("AATES_DRY_RUN") == "True":
            logger.info("Dry-run upload to YouTube requested.")
            return {
                "external_post_id": "dry_run_yt_id",
                "status": "success",
                "error_message": None,
                "provider": "YouTubePublisher",
                "upload_id": "dry_run_upload_id",
                "video_id": "dry_run_video_id",
                "url": "https://www.youtube.com/watch?v=dry_run_video_id",
                "processing_status": "dry_run"
            }

        if not os.path.exists(master_reel_path):
            raise FileNotFoundError(f"Video file not found at: {master_reel_path}")

        file_size = os.path.getsize(master_reel_path)
        logger.info(f"Upload Started: File={os.path.basename(master_reel_path)}, size={file_size} bytes")
        start_time = time.monotonic()

        token = await self._get_access_token()

        title = metadata.get("title", f"AATES Production {int(time.time())}")
        title = title[:100]  # YouTube shorts title max 100 chars

        description = caption or metadata.get("description", "Produced by AATES autonomous studio.")
        tags = metadata.get("tags", ["Tamil", "AATES", "AI"])
        category_id = metadata.get("categoryId", "22")  # People & Blogs
        language = metadata.get("language", "ta")

        # Privacy status
        privacy = metadata.get("privacy", "private")
        if metadata.get("safe_production_mode", True) or os.getenv("AATES_SAFE_MODE") == "True":
            privacy = "private"  # Override to private in safe mode

        # Schedule publishing if requested
        publish_at = metadata.get("publish_at")

        # Define snippet & status
        snippet = {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": language,
            "defaultAudioLanguage": language
        }
        status = {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }

        if publish_at:
            status["publishAt"] = publish_at
            status["privacyStatus"] = "private"

        body = {
            "snippet": snippet,
            "status": status
        }

        # 2. Initiate Resumable Upload Session
        init_res = await self._request_with_retry(
            "POST",
            "https://www.googleapis.com/upload/youtube/v3/videos",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Length": str(file_size),
                "X-Upload-Content-Type": "video/*"
            },
            params={"uploadType": "resumable", "part": "snippet,status"},
            json_data=body,
            timeout=30.0
        )

        if init_res.status_code != 200:
            raise ValueError(f"Failed to initiate resumable upload session: {init_res.text}")

        upload_url = init_res.headers.get("Location")
        if not upload_url:
            raise ValueError("Location header missing in resumable upload initiation response")

        # 3. Stream Video Content
        with open(master_reel_path, "rb") as f:
            video_bytes = f.read()

        upload_res = await self._request_with_retry(
            "PUT",
            upload_url,
            headers={
                "Content-Length": str(file_size),
                "Content-Type": "video/*"
            },
            content=video_bytes,
            timeout=600.0  # 10 minute timeout
        )

        if upload_res.status_code not in (200, 201):
            raise ValueError(f"Failed to upload video content: {upload_res.text}")

        video_data = upload_res.json()
        video_id = video_data.get("id")

        upload_duration = time.monotonic() - start_time
        logger.info(f"Upload Finished. Video ID: {video_id}")
        logger.info(f"Upload Duration: {upload_duration:.2f} seconds")

        # 4. Upload Thumbnail if provided
        thumbnail_path = metadata.get("thumbnail_path")
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                with open(thumbnail_path, "rb") as thumb_f:
                    thumb_data = thumb_f.read()
                await self._request_with_retry(
                    "POST",
                    "https://www.googleapis.com/upload/youtube/v3/thumbnails/set",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "image/jpeg"
                    },
                    params={"videoId": video_id},
                    content=thumb_data,
                    timeout=60.0
                )
                logger.info(f"Successfully set thumbnail for video {video_id}")
            except Exception as thumb_err:
                logger.warning(f"Failed to upload thumbnail: {thumb_err}")

        # 5. Upload Subtitles if provided
        srt_path = metadata.get("srt_path")
        if srt_path and os.path.exists(srt_path):
            try:
                with open(srt_path, "rb") as srt_f:
                    srt_data = srt_f.read()
                
                caption_metadata = {
                    "snippet": {
                        "videoId": video_id,
                        "language": language,
                        "name": "Tamil Subtitles",
                        "isDraft": False
                    }
                }
                
                files = {
                    "metadata": (None, json.dumps(caption_metadata), "application/json"),
                    "media": ("subtitles.srt", srt_data, "application/octet-stream")
                }
                
                await self._request_with_retry(
                    "POST",
                    "https://www.googleapis.com/upload/youtube/v3/captions",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"part": "snippet"},
                    files=files,
                    timeout=60.0
                )
                logger.info(f"Successfully uploaded subtitles for video {video_id}")
            except Exception as srt_err:
                logger.warning(f"Failed to upload subtitles: {srt_err}")

        return {
            "external_post_id": video_id,
            "status": "success",
            "error_message": None,
            "provider": "YouTubePublisher",
            "upload_id": upload_url,
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "processing_status": "uploaded"
        }

    async def health_check(self) -> dict[str, Any]:
        """Verify YouTube API availability."""
        t0 = time.monotonic()
        if not self._is_available:
            return {
                "is_available": False,
                "latency_ms": 0.0,
                "error_rate": 1.0,
                "success_rate": 0.0,
                "error": self._validation_error or "Startup verification failed"
            }
        try:
            token = await self._get_access_token()
            channel_id = settings.publishing.youtube_channel_id
            
            if channel_id:
                res = await self._request_with_retry(
                    "GET",
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "id", "id": channel_id},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
            else:
                res = await self._request_with_retry(
                    "GET",
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "id", "mine": "true"},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
            
            if res.status_code == 200:
                latency = (time.monotonic() - t0) * 1000
                return {
                    "is_available": True,
                    "latency_ms": round(latency, 2),
                    "error_rate": 0.0,
                    "success_rate": 1.0
                }
            else:
                raise ValueError(f"HTTP error {res.status_code}: {res.text}")
        except Exception as e:
            latency = (time.monotonic() - t0) * 1000
            logger.error(f"YouTube health check failed: {e}")
            return {
                "is_available": False,
                "latency_ms": round(latency, 2),
                "error_rate": 1.0,
                "success_rate": 0.0
            }

    async def get_analytics(self, video_id: str) -> dict[str, Any]:
        """Fetch views, watch time, likes, comments for a video."""
        try:
            token = await self._get_access_token()
            res = await self._request_with_retry(
                "GET",
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "statistics", "id": video_id},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            if res.status_code == 200:
                items = res.json().get("items", [])
                if items:
                    stats = items[0]["statistics"]
                    return {
                        "views": int(stats.get("viewCount", 0)),
                        "likes": int(stats.get("likeCount", 0)),
                        "comments": int(stats.get("commentCount", 0)),
                        "shares": 0,  # YouTube API doesn't expose shares on public video resource
                        "watch_time_sec": 0,  # YouTube Analytics API required for watch time
                        "retention_pct": 0.0,
                        "completion_pct": 0.0
                    }
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch YouTube analytics for video {video_id}: {e}")
            return {}

    async def get_video_details(self, video_id: str) -> dict[str, Any]:
        """Fetch complete video details including snippet, status, contentDetails."""
        try:
            token = await self._get_access_token()
            res = await self._request_with_retry(
                "GET",
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "snippet,status,contentDetails,statistics", "id": video_id},
                headers={"Authorization": f"Bearer {token}"},
                timeout=15.0
            )
            if res.status_code == 200:
                items = res.json().get("items", [])
                if items:
                    return items[0]
            logger.warning(f"Video details not found for {video_id}: {res.text}")
            return {}
        except Exception as e:
            logger.error(f"Failed to fetch YouTube video details for {video_id}: {e}")
            return {}

    async def delete_video(self, video_id: str) -> bool:
        """Delete a YouTube video by ID."""
        try:
            token = await self._get_access_token()
            res = await self._request_with_retry(
                "DELETE",
                "https://www.googleapis.com/youtube/v3/videos",
                params={"id": video_id},
                headers={"Authorization": f"Bearer {token}"},
                timeout=15.0
            )
            # YouTube API delete endpoint returns 204 No Content on success
            if res.status_code in (200, 204):
                logger.info(f"Successfully deleted YouTube video: {video_id}")
                return True
            logger.error(f"Failed to delete YouTube video {video_id}: {res.status_code} - {res.text}")
            return False
        except Exception as e:
            logger.error(f"Error deleting YouTube video {video_id}: {e}")
            return False


async def verify_youtube_startup() -> None:
    """Validate YouTube credentials and attempt a real token exchange at startup if enabled."""
    if not settings.publishing.youtube_enabled:
        return
        
    logger.info("Running YouTube startup validation...")
    try:
        publisher = YouTubePublisher()
        # Attempt token refresh (real exchange) to check client id / secret / refresh token
        await publisher._get_access_token()
        YouTubePublisher._is_available = True
        YouTubePublisher._validation_error = None
        logger.info("✓ YouTube startup validation passed.")
    except Exception as e:
        error_msg = f"YouTube startup validation failed: {e}"
        logger.error(error_msg)
        # Mark as unavailable but keep running
        YouTubePublisher._is_available = False
        YouTubePublisher._validation_error = str(e)

