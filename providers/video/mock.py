import os
import random
import uuid
from typing import Any, List
from providers.video.interface import VideoProvider

class MockVideoProvider(VideoProvider):
    """Mock Video Provider writing dummy MP4 assets and returning simulated timeline SceneGraph metadata."""

    @property
    def name(self) -> str:
        return "MockVideoRenderer"

    def supports_gpu(self) -> bool:
        return True

    def __init__(self) -> None:
        self.output_dir = "artifacts/video"
        os.makedirs(self.output_dir, exist_ok=True)

    async def build_timeline(self, script_pkg: Any, image_pkg: Any, voice_pkg: Any) -> list[dict[str, Any]]:
        timeline = []
        current_time_ms = 0
        
        scenes = getattr(script_pkg, "scene_breakdown", []) or []
        image_assets = {getattr(a, "scene_number", i+1): a for i, a in enumerate(getattr(image_pkg, "assets", []))}
        voice_assets = {getattr(a, "scene_number", i+1): a for i, a in enumerate(getattr(voice_pkg, "assets", []))}

        for i, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", i + 1)
            duration_ms = getattr(voice_assets.get(scene_num), "duration_ms", 5000)
            
            img_id = getattr(image_assets.get(scene_num), "id", None)
            v_id = getattr(voice_assets.get(scene_num), "id", None)
            node = {
                "scene_number": scene_num,
                "timeline_start_ms": current_time_ms,
                "timeline_end_ms": current_time_ms + duration_ms,
                "duration_ms": duration_ms,
                "image_asset_id": str(img_id) if img_id else None,
                "voice_asset_id": str(v_id) if v_id else None,
                "motion_preset": scene.get("motion_preset", "Zoom In"),
                "transition_preset": scene.get("transition_preset", "Cross Dissolve"),
                "narration": scene.get("narration", ""),
                "image_path": getattr(image_assets.get(scene_num), "local_path", ""),
                "voice_path": getattr(voice_assets.get(scene_num), "local_path", "")
            }
            timeline.append(node)
            current_time_ms += duration_ms

        return timeline

    async def render_scene(self, scene_data: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
        filename = f"clip_{scene_data['scene_number']}_{uuid.uuid4().hex[:6]}.mp4"
        filepath = os.path.join(self.output_dir, filename)
        
        # Write dummy binary
        with open(filepath, "wb") as f:
            f.write(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"VIDEO_MOCK_DATA" * 50)

        return {
            "local_path": filepath,
            "storage_key": f"video/clips/{filename}",
            "preview_url": f"https://cdn.aates.internal/video/clips/{filename}",
            "duration_ms": scene_data["duration_ms"],
            "quality_score": round(random.uniform(0.78, 0.98), 2),
            "render_metadata": {
                "scene_graph_node": scene_data,
                "codec": options.get("codec", "h264"),
                "preset": options.get("preset", "medium")
            }
        }

    async def render_video(self, scenes: list[dict[str, Any]], options: dict[str, Any]) -> dict[str, Any]:
        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"FULL_VIDEO_MOCK_DATA" * 200)

        total_duration_ms = sum(s["duration_ms"] for s in scenes)
        
        # Downstream Subtitle & Thumbnail metadata
        metadata_artifacts = {
            "keyframes": [s["timeline_start_ms"] for s in scenes],
            "scene_boundaries": [{"scene": s["scene_number"], "start_ms": s["timeline_start_ms"], "end_ms": s["timeline_end_ms"]} for s in scenes],
            "safe_title_regions": "80% safety window center",
            "caption_safe_regions": "bottom 20% vertical space offset",
            "representative_frame_indices": [round(s["timeline_start_ms"] / 1000 * options.get("fps", 30)) for s in scenes],
            "render_telemetry": {
                "timeline_build_time_ms": 12,
                "scene_render_time_ms": 120 * len(scenes),
                "final_render_time_ms": 280,
                "encoding_time_ms": 150,
                "cpu_usage_pct": 32.5,
                "gpu_usage_pct": 14.8,
                "peak_memory_mb": 185.2,
                "output_file_size_bytes": os.path.getsize(filepath)
            }
        }

        return {
            "local_path": filepath,
            "storage_key": f"video/outputs/{filename}",
            "preview_video": filepath,
            "thumbnail_frame": f"artifacts/video/thumb_{filename.replace('.mp4', '.jpg')}",
            "duration_ms": total_duration_ms,
            "quality_score": round(random.uniform(0.85, 0.99), 2),
            "metadata_artifacts": metadata_artifacts
        }

    async def render_preview(self, video_path: str) -> str:
        preview_path = video_path.replace(".mp4", "_preview.mp4")
        if os.path.dirname(preview_path):
            os.makedirs(os.path.dirname(preview_path), exist_ok=True)
        with open(preview_path, "wb") as f:
            f.write(b"PREVIEW_MOCK_DATA")
        return preview_path
ZOOMING = "zoom"
