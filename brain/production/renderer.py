import uuid
import hashlib
from typing import Any
from sqlalchemy.orm import Session
from contracts.dto.manifest import RenderManifestDTO, ScenePackageDTO, RenderTimelineEvent
from providers.rendering.mock import MockRenderingProvider
from brain.production.profiles import profile_loader
from brain.production.timing import scene_timing_engine

class RenderManifestCompiler:
    """Core Render Manifest Compiler compiling scene timeline assets specifications under output profiles settings."""
    
    async def compile_manifest(
        self,
        episode_id: str,
        universe_id: str,
        season: int,
        episode: int,
        scene_packages: list[ScenePackageDTO],
        output_profile_name: str = "instagram_reel",
        production_profile_name: str = "cinematic"
    ) -> RenderManifestDTO:
        """Assembles completed scene packages, applying scene pacing timing and target output aspect ratios."""
        # 1. Load output profile configs
        out_prof = profile_loader.load_output_profile(output_profile_name)
        
        # 2. Calculate dynamic paced durations
        scene_durations = scene_timing_engine.calculate_scene_durations(
            scene_count=len(scene_packages),
            output_profile_name=output_profile_name,
            production_profile_name=production_profile_name
        )

        timeline_events = []
        current_offset = out_prof.get("intro_duration", 1.5)
        
        for idx, pkg in enumerate(scene_packages):
            duration = scene_durations[idx] if idx < len(scene_durations) else 4.0
            
            # Video track event
            timeline_events.append(
                RenderTimelineEvent(
                    time_offset=current_offset,
                    duration=duration,
                    asset_id=pkg.video_asset_id,
                    asset_type="video"
                )
            )
            # Voice speech events
            for char_name, voice_id in pkg.voice_asset_ids.items():
                timeline_events.append(
                    RenderTimelineEvent(
                        time_offset=current_offset,
                        duration=duration - 0.5 if duration > 1.0 else duration,
                        asset_id=voice_id,
                        asset_type="voice"
                    )
                )
            # Ambient Music event
            if pkg.music_asset_id:
                timeline_events.append(
                    RenderTimelineEvent(
                        time_offset=current_offset,
                        duration=duration,
                        asset_id=pkg.music_asset_id,
                        asset_type="music",
                        volume=0.3
                    )
                )
            current_offset += duration

        raw_manifest_str = f"manifest-{episode_id}-{len(scene_packages)}-{current_offset}"
        checksum_val = hashlib.sha256(raw_manifest_str.encode()).hexdigest()

        return RenderManifestDTO(
            episode_id=episode_id,
            universe_id=universe_id,
            season=season,
            episode=episode,
            scene_packages=scene_packages,
            timeline_events=timeline_events,
            render_settings={
                "resolution": out_prof.get("resolution", "1080x1920"),
                "fps": out_prof.get("frame_rate", 30),
                "aspect_ratio": out_prof.get("aspect_ratio", "9:16"),
                "audio_loudness": out_prof.get("audio_loudness_target", -14.0)
            },
            output_settings={
                "codec": out_prof.get("video_codec", "h264"),
                "container": "mp4",
                "export_preset": out_prof.get("export_preset", "slow")
            },
            version=1,
            checksum=checksum_val
        )

class FFmpegRenderingEngine:
    """Core FFmpeg Rendering Engine executing audio-video mixes and concatenations under output aspect ratio constraints."""
    
    def __init__(self, provider: Any = None):
        self.provider = provider or MockRenderingProvider()

    async def render_episode(self, manifest: RenderManifestDTO, db: Session = None) -> dict[str, Any]:
        """Mixes scene-level assets and merges them into the final compiled Master Reel."""
        mixed_videos = []
        for pkg in manifest.scene_packages:
            audio_paths = list(pkg.voice_asset_ids.values())
            if pkg.music_asset_id:
                audio_paths.append(pkg.music_asset_id)
                
            mix_res = await self.provider.mix_scene_assets(
                video_location=pkg.video_asset_id,
                audio_locations=audio_paths,
                subtitle_location=pkg.subtitle_asset_id
            )
            mixed_videos.append(mix_res["storage_location"])

        reel_res = await self.provider.concatenate_scenes(
            scene_video_locations=mixed_videos,
            resolution=manifest.render_settings.get("resolution", "1080x1920"),
            aspect_ratio=manifest.render_settings.get("aspect_ratio", "9:16")
        )
        
        # Build Asset metadata row
        from core.database.models import Asset
        e_uuid = uuid.UUID(manifest.episode_id) if isinstance(manifest.episode_id, str) else manifest.episode_id
        u_uuid = uuid.UUID(manifest.universe_id) if isinstance(manifest.universe_id, str) else manifest.universe_id

        master_asset = Asset(
            id=uuid.uuid4(),
            type="master_reel",
            provider=reel_res["provider"],
            model=reel_res["model"],
            prompt_version="1.0.0",
            prompt_hash=manifest.checksum,
            seed=None,
            resolution=manifest.render_settings.get("resolution", "1080x1920"),
            duration=len(manifest.scene_packages) * 4.0,
            storage_location=reel_res["storage_location"],
            episode_id=e_uuid,
            universe_id=u_uuid,
            scene_id="full_episode",
            parent_asset_id=None,
            blueprint_version=manifest.version,
            checksum=reel_res["checksum"],
            cost=reel_res["cost"]
        )

        if db:
            db.add(master_asset)
            db.flush()

        return {
            "master_reel_asset_id": str(master_asset.id),
            "storage_location": master_asset.storage_location,
            "checksum": master_asset.checksum,
            "cost": master_asset.cost,
            "status": "rendered_successfully"
        }

render_manifest_compiler = RenderManifestCompiler()
ffmpeg_rendering_engine = FFmpegRenderingEngine()
