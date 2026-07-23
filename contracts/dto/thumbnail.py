import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class ThumbnailJobCreateDTO(BaseModel):
    script_package_id: uuid.UUID
    image_package_id: uuid.UUID
    video_package_id: uuid.UUID
    subtitle_package_id: Optional[uuid.UUID] = None
    music_package_id: Optional[uuid.UUID] = None
    provider: Optional[str] = "template"
    priority: Optional[int] = 0

class ThumbnailStyleProfileDTO(BaseModel):
    id: uuid.UUID
    name: str
    platform: str
    font_family: str
    font_size_pt: int
    font_weight: str
    primary_color: str
    accent_color: str
    outline_color: str
    shadow_style: str
    background_style: str
    logo_placement: str
    safe_margins: Optional[dict[str, Any]] = None
    emoji_policy: str
    aspect_ratio: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CompositionTemplateDTO(BaseModel):
    id: uuid.UUID
    name: str
    platform: str
    layout_type: str
    subject_region: Optional[dict[str, Any]] = None
    headline_region: Optional[dict[str, Any]] = None
    secondary_text_region: Optional[dict[str, Any]] = None
    logo_region: Optional[dict[str, Any]] = None
    safe_margins: Optional[dict[str, Any]] = None
    grid_definition: Optional[dict[str, Any]] = None
    aspect_ratio: str
    priority_rules: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ThumbnailAssetDTO(BaseModel):
    id: uuid.UUID
    storage_key: str
    public_url: Optional[str] = None
    preview_url: Optional[str] = None
    width: int
    height: int
    format: str
    compression: str
    file_size_bytes: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ThumbnailScoreDTO(BaseModel):
    id: uuid.UUID
    thumbnail_variant_id: uuid.UUID
    contrast_score: float
    sharpness_score: float
    face_visibility_score: float
    subject_prominence_score: float
    text_readability_score: float
    color_harmony_score: float
    rule_of_thirds_score: float
    emotion_score: float
    brand_consistency_score: float
    heuristic_score: float
    learned_score: float
    overall_score: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ThumbnailVariantDTO(BaseModel):
    id: uuid.UUID
    thumbnail_package_id: uuid.UUID
    thumbnail_asset_id: Optional[uuid.UUID] = None
    composition_template_id: Optional[uuid.UUID] = None
    variant_name: str
    scene_number: int
    source_frame_key: Optional[str] = None
    primary_hook: str
    secondary_hook: Optional[str] = None
    badge_text: Optional[str] = None
    brand_label: Optional[str] = None
    layout_type: str
    contrast_score: float
    readability_score: float
    composition_score: float
    brand_score: float
    ctr_prediction_score: float
    quality_score: float
    is_selected: bool
    created_at: datetime
    asset: Optional[ThumbnailAssetDTO] = None
    template: Optional[CompositionTemplateDTO] = None
    score: Optional[ThumbnailScoreDTO] = None
    model_config = ConfigDict(from_attributes=True)

class ThumbnailAnalysisDTO(BaseModel):
    id: uuid.UUID
    thumbnail_package_id: uuid.UUID
    blur_score: float
    brightness: float
    contrast_ratio: float
    entropy: float
    dominant_colors: Optional[list[str]] = None
    face_count: int
    face_confidence: float
    object_regions: Optional[list[dict[str, Any]]] = None
    saliency_map: Optional[dict[str, Any]] = None
    ocr_result: Optional[dict[str, Any]] = None
    edge_density: float
    color_histogram: Optional[dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ThumbnailVersionDTO(BaseModel):
    id: uuid.UUID
    thumbnail_package_id: uuid.UUID
    version: int
    parent_version: Optional[int] = None
    lineage_action: str
    assets_snapshot: list[dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ThumbnailExperimentDTO(BaseModel):
    id: uuid.UUID
    thumbnail_package_id: uuid.UUID
    variant_a_id: uuid.UUID
    variant_b_id: uuid.UUID
    platform: str
    status: str
    evaluation_window_hours: int
    statistical_significance: float
    algorithm_version: Optional[str] = None
    published_at: Optional[datetime] = None
    impressions: int
    clicks: int
    ctr: float
    winner_variant_id: Optional[uuid.UUID] = None
    winning_confidence: Optional[float] = None
    recommendation: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ThumbnailPackageDTO(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    script_package_id: uuid.UUID
    image_package_id: uuid.UUID
    video_package_id: uuid.UUID
    subtitle_package_id: Optional[uuid.UUID] = None
    music_package_id: Optional[uuid.UUID] = None
    thumbnail_style_profile_id: Optional[uuid.UUID] = None
    primary_thumbnail_id: Optional[uuid.UUID] = None
    selected_variant_id: Optional[uuid.UUID] = None
    variant_count: int
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
    
    variants: Optional[list[ThumbnailVariantDTO]] = None
    analysis: Optional[ThumbnailAnalysisDTO] = None
    versions: Optional[list[ThumbnailVersionDTO]] = None
    experiments: Optional[list[ThumbnailExperimentDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class ThumbnailJobResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: Optional[str] = None
    script_package_id: uuid.UUID
    image_package_id: uuid.UUID
    video_package_id: uuid.UUID
    subtitle_package_id: Optional[uuid.UUID] = None
    music_package_id: Optional[uuid.UUID] = None
    thumbnail_style_profile_id: Optional[uuid.UUID] = None
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
    
    style_profile: Optional[ThumbnailStyleProfileDTO] = None
    packages: Optional[list[ThumbnailPackageDTO]] = None
    model_config = ConfigDict(from_attributes=True)

class ThumbnailMetricsDTO(BaseModel):
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
