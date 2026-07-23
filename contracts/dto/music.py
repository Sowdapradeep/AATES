import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class MusicJobCreateDTO(BaseModel):
    script_package_id: uuid.UUID
    voice_package_id: uuid.UUID
    video_package_id: uuid.UUID
    subtitle_package_id: Optional[uuid.UUID] = None
    provider: Optional[str] = "library"
    priority: Optional[int] = 0

class AudioMixProfileDTO(BaseModel):
    id: uuid.UUID
    name: str
    target_platform: str
    music_volume_db: float
    narration_volume_db: float
    ducking_level_db: float
    fade_duration_ms: int
    crossfade_duration_ms: int
    target_lufs: float
    true_peak_db: float
    sample_rate: int
    channels: int
    normalization_mode: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MusicAssetDTO(BaseModel):
    id: uuid.UUID
    provider: str
    license_type: str
    copyright_info: Optional[str] = None
    storage_key: str
    fingerprint: Optional[str] = None
    isrc: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MusicTrackDTO(BaseModel):
    id: uuid.UUID
    asset_id: Optional[uuid.UUID] = None
    track_title: str
    artist: Optional[str] = None
    genre: str
    mood: str
    energy_level: str
    tempo_bpm: int
    musical_key: str
    duration_ms: int
    sample_rate: int
    channels: int
    is_loopable: bool
    is_generated: bool
    is_licensed: bool
    created_at: datetime
    asset: Optional[MusicAssetDTO] = None
    model_config = ConfigDict(from_attributes=True)

class MusicCueDTO(BaseModel):
    id: uuid.UUID
    music_track_id: Optional[uuid.UUID] = None
    scene_music_id: Optional[uuid.UUID] = None
    cue_name: str
    cue_purpose: str
    source_start_ms: int
    source_end_ms: int
    trim_start_ms: int
    trim_end_ms: int
    loop_start_ms: int
    loop_end_ms: int
    fade_in_ms: int
    fade_out_ms: int
    gain_db: float
    emotion_score: float
    transition_compatibility: float
    loop_confidence: float
    crossfade_recommendation: int
    beat_alignment_offset_ms: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SceneMusicDTO(BaseModel):
    id: uuid.UUID
    music_package_id: uuid.UUID
    scene_number: int
    track_name: str
    genre: str
    mood: str
    energy: str
    tempo_bpm: int
    musical_key: str
    start_time_ms: int
    end_time_ms: int
    fade_in_ms: int
    fade_out_ms: int
    loop_points: Optional[dict[str, Any]] = None
    music_volume_db: float
    narration_ducking_db: float
    quality_score: float
    created_at: datetime
    cues: Optional[list[MusicCueDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class AudioTimelineEventDTO(BaseModel):
    id: uuid.UUID
    music_package_id: uuid.UUID
    cue_id: Optional[uuid.UUID] = None
    scene_number: int
    start_time_ms: int
    end_time_ms: int
    gain_db: float
    pan: float
    fade_in_ms: int
    fade_out_ms: int
    ducking_state: str
    automation_points: Optional[list[dict[str, Any]]] = None
    cue: Optional[MusicCueDTO] = None
    model_config = ConfigDict(from_attributes=True)

class AudioAnalysisDTO(BaseModel):
    id: uuid.UUID
    music_package_id: uuid.UUID
    peak_db: float
    lufs: float
    dynamic_range_db: float
    rms_db: float
    tempo_bpm: int
    musical_key: str
    silence_regions: Optional[list[dict[str, Any]]] = None
    speech_regions: Optional[list[dict[str, Any]]] = None
    waveform_data: Optional[list[float]] = None
    spectrum_data: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MusicVersionDTO(BaseModel):
    id: uuid.UUID
    music_package_id: uuid.UUID
    version: int
    parent_version: Optional[int] = None
    lineage_action: str
    assets_snapshot: list[dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MusicPackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    script_package_id: uuid.UUID
    voice_package_id: uuid.UUID
    video_package_id: uuid.UUID
    subtitle_package_id: Optional[uuid.UUID] = None
    audio_mix_profile_id: Optional[uuid.UUID] = None
    storage_key: str
    separated_music_track: Optional[str] = None
    narration_track: Optional[str] = None
    ambient_stem_track: Optional[str] = None
    sfx_stem_track: Optional[str] = None
    scene_count: int
    duration_ms: int
    waveform_metadata: Optional[dict[str, Any]] = None
    package_manifest: Optional[dict[str, Any]] = None
    
    # Mixin fields
    version: int
    parent_package_id: Optional[uuid.UUID] = None
    source_agent: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt_version: Optional[str] = None
    quality_score: float
    telemetry_metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    
    scene_musics: Optional[list[SceneMusicDTO]] = None
    timeline_events: Optional[list[AudioTimelineEventDTO]] = None
    analysis: Optional[AudioAnalysisDTO] = None
    versions: Optional[list[MusicVersionDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class MusicJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    script_package_id: uuid.UUID
    voice_package_id: uuid.UUID
    video_package_id: uuid.UUID
    subtitle_package_id: Optional[uuid.UUID] = None
    audio_mix_profile_id: Optional[uuid.UUID] = None
    provider: str
    status: str
    stage: str
    progress: float
    attempts: int
    max_attempts: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    duration_sec: float
    worker_id: Optional[str] = None
    priority: int
    scheduled_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    profile: Optional[AudioMixProfileDTO] = None
    packages: Optional[list[MusicPackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class MusicMetricsDTO(BaseModel):
    jobs_queued: int
    jobs_processing: int
    jobs_succeeded: int
    jobs_failed: int
    jobs_retrying: int
    jobs_cancelled: int
    average_duration_sec: float
    current_worker_count: int
    worker_uptime: str
    worker_is_running: bool
    worker_heartbeats: list[dict[str, Any]]
