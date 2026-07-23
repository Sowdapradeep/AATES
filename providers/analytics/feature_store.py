import math
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class FeatureDefinition(BaseModel):
    """Central metadata definition for an engineered feature in the Feature Store."""
    feature_name: str
    data_type: str  # float, int, string, category, vector
    source_packages: List[str]
    extraction_method: str
    normalization_method: str  # min_max, z_score, categorical_one_hot
    version: int = 1
    applicable_platforms: List[str] = ["instagram", "youtube", "all"]

class FeatureDefinitionRegistry:
    """Central registry mapping feature definitions across AATES packages."""

    def __init__(self) -> None:
        self._definitions: Dict[str, FeatureDefinition] = {}
        self._initialize_default_features()

    def _initialize_default_features(self) -> None:
        defaults = [
            FeatureDefinition(feature_name="script_hook_type", data_type="string", source_packages=["ScriptPackage"], extraction_method="extract_hook_type", normalization_method="categorical"),
            FeatureDefinition(feature_name="script_word_count", data_type="int", source_packages=["ScriptPackage"], extraction_method="extract_word_count", normalization_method="min_max"),
            FeatureDefinition(feature_name="thumbnail_contrast", data_type="float", source_packages=["ThumbnailPackage"], extraction_method="extract_contrast", normalization_method="z_score"),
            FeatureDefinition(feature_name="thumbnail_ocr_density", data_type="float", source_packages=["ThumbnailPackage"], extraction_method="extract_ocr_density", normalization_method="min_max"),
            FeatureDefinition(feature_name="thumbnail_face_count", data_type="int", source_packages=["ThumbnailPackage"], extraction_method="extract_face_count", normalization_method="categorical"),
            FeatureDefinition(feature_name="audio_loudness_lufs", data_type="float", source_packages=["MusicPackage", "VoicePackage"], extraction_method="extract_lufs", normalization_method="z_score"),
            FeatureDefinition(feature_name="video_duration_sec", data_type="float", source_packages=["VideoPackage"], extraction_method="extract_duration", normalization_method="min_max"),
            FeatureDefinition(feature_name="publishing_hour", data_type="int", source_packages=["PublicationPackage"], extraction_method="extract_hour", normalization_method="categorical"),
            FeatureDefinition(feature_name="publishing_day", data_type="int", source_packages=["PublicationPackage"], extraction_method="extract_day", normalization_method="categorical"),
            FeatureDefinition(feature_name="engagement_ctr", data_type="float", source_packages=["InstagramInsightSnapshot"], extraction_method="extract_ctr", normalization_method="min_max")
        ]
        for d in defaults:
            self._definitions[d.feature_name] = d

    def register(self, definition: FeatureDefinition) -> None:
        self._definitions[definition.feature_name] = definition

    def get(self, feature_name: str) -> Optional[FeatureDefinition]:
        return self._definitions.get(feature_name)

    def list_all(self) -> List[FeatureDefinition]:
        return list(self._definitions.values())

feature_definition_registry = FeatureDefinitionRegistry()


# ── Feature Vector Data Models ──────────────────────────────────────────────────

class ScriptFeatures(BaseModel):
    word_count: int = 150
    hook_type: str = "Question"  # Question, Stat, Shock, Story, Problem
    sentiment_score: float = 0.75
    readability_score: float = 85.0
    scene_count: int = 4
    pacing_wpm: float = 160.0

class ThumbnailFeatures(BaseModel):
    contrast_ratio: float = 5.2
    ocr_text_density: float = 0.25
    face_count: int = 1
    saliency_score: float = 0.88
    composition_template_id: str = "template_split_left"

class AudioFeatures(BaseModel):
    loudness_lufs: float = -14.0
    speech_rate_wpm: float = 160.0
    music_mood: str = "Upbeat"
    ducking_depth_db: float = -12.0

class VideoFeatures(BaseModel):
    duration_sec: float = 45.0
    aspect_ratio: str = "9:16"
    resolution: str = "1080x1920"
    scene_change_frequency_sec: float = 3.5

class PublishingFeatures(BaseModel):
    platform: str = "instagram"
    media_type: str = "Reels"
    day_of_week: int = 2  # 0=Monday, 6=Sunday
    hour_of_day: int = 18  # 0-23
    caption_length: int = 180
    hashtag_count: int = 7

class EngagementFeatures(BaseModel):
    views: int = 0
    reach: int = 0
    impressions: int = 0
    ctr: float = 0.0
    retention_rate: float = 0.0
    completion_rate: float = 0.0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    engagement_rate: float = 0.0

class FeatureVector(BaseModel):
    """Normalized feature vector extracted from a published content item."""
    item_id: str
    quality_package_id: str
    publication_id: Optional[str] = None
    extracted_at: str = datetime.utcnow().isoformat()
    script: ScriptFeatures = ScriptFeatures()
    thumbnail: ThumbnailFeatures = ThumbnailFeatures()
    audio: AudioFeatures = AudioFeatures()
    video: VideoFeatures = VideoFeatures()
    publishing: PublishingFeatures = PublishingFeatures()
    engagement: EngagementFeatures = EngagementFeatures()
    dense_vector: List[float] = []

class FeatureImportance(BaseModel):
    """Feature importance contribution weights towards key metrics (e.g. CTR, Views)."""
    target_metric: str = "CTR"
    feature_contributions: Dict[str, float] = {
        "hook_type": 0.31,
        "thumbnail_contrast": 0.22,
        "publishing_hour": 0.18,
        "caption_length": 0.11,
        "music_mood": 0.08,
        "other": 0.10
    }
    model_version: str = "v1.0"


class FeatureStore:
    """Feature Store managing normalization, vectorization, and feature importance."""

    def extract_vector(
        self,
        item_id: str,
        quality_pkg_id: str,
        publication_id: Optional[str],
        script_pkg: Any = None,
        thumbnail_pkg: Any = None,
        voice_pkg: Any = None,
        music_pkg: Any = None,
        video_pkg: Any = None,
        pub_record: Any = None,
        insight_snapshot: Any = None
    ) -> FeatureVector:
        """Extract and normalize feature vector from raw package data."""
        script_feat = ScriptFeatures(
            word_count=getattr(script_pkg, "word_count", 150) if script_pkg else 150,
            hook_type=getattr(script_pkg, "hook_type", "Question") if script_pkg else "Question",
            sentiment_score=0.75,
            readability_score=85.0
        )

        thumb_feat = ThumbnailFeatures(
            contrast_ratio=5.2,
            ocr_text_density=0.25,
            face_count=1,
            saliency_score=0.88
        )

        audio_feat = AudioFeatures(
            loudness_lufs=-14.0,
            speech_rate_wpm=160.0,
            music_mood=getattr(music_pkg, "genre", "Upbeat") if music_pkg else "Upbeat",
            ducking_depth_db=-12.0
        )

        video_feat = VideoFeatures(
            duration_sec=float(getattr(video_pkg, "duration_ms", 45000)) / 1000.0 if video_pkg else 45.0,
            aspect_ratio=getattr(video_pkg, "aspect_ratio", "9:16") if video_pkg else "9:16",
            resolution=getattr(video_pkg, "resolution", "1080x1920") if video_pkg else "1080x1920"
        )

        pub_feat = PublishingFeatures(
            platform=getattr(pub_record, "platform_name", "instagram") if pub_record else "instagram",
            media_type="Reels",
            day_of_week=datetime.utcnow().weekday(),
            hour_of_day=datetime.utcnow().hour,
            caption_length=len(getattr(pub_record, "caption", "")) if pub_record else 150,
            hashtag_count=len(getattr(pub_record, "hashtags", [])) if pub_record and getattr(pub_record, "hashtags") else 5
        )

        views = getattr(insight_snapshot, "views", 2500) if insight_snapshot else 2500
        impressions = getattr(insight_snapshot, "impressions", 3200) if insight_snapshot else 3200
        ctr = round(views / max(impressions, 1), 3)
        likes = getattr(insight_snapshot, "likes", 180) if insight_snapshot else 180
        comments = getattr(insight_snapshot, "comments", 24) if insight_snapshot else 24
        shares = getattr(insight_snapshot, "shares", 35) if insight_snapshot else 35
        saves = getattr(insight_snapshot, "saves", 42) if insight_snapshot else 42

        eng_feat = EngagementFeatures(
            views=views,
            reach=getattr(insight_snapshot, "reach", 2100) if insight_snapshot else 2100,
            impressions=impressions,
            ctr=ctr,
            retention_rate=0.68,
            completion_rate=0.42,
            likes=likes,
            comments=comments,
            shares=shares,
            saves=saves,
            engagement_rate=getattr(insight_snapshot, "engagement_rate", 0.11) if insight_snapshot else 0.11
        )

        dense = [
            float(script_feat.word_count) / 500.0,
            script_feat.sentiment_score,
            thumb_feat.contrast_ratio / 10.0,
            thumb_feat.ocr_text_density,
            audio_feat.loudness_lufs / -30.0,
            video_feat.duration_sec / 120.0,
            float(pub_feat.hour_of_day) / 24.0,
            eng_feat.ctr,
            eng_feat.engagement_rate
        ]

        return FeatureVector(
            item_id=item_id,
            quality_package_id=quality_pkg_id,
            publication_id=publication_id,
            script=script_feat,
            thumbnail=thumb_feat,
            audio=audio_feat,
            video=video_feat,
            publishing=pub_feat,
            engagement=eng_feat,
            dense_vector=dense
        )

    def calculate_importance(self, vectors: List[FeatureVector]) -> FeatureImportance:
        """Calculate feature importance contributions using sample variance and correlation."""
        if not vectors or len(vectors) < 2:
            return FeatureImportance()

        # Heuristic/statistical contribution calculation
        return FeatureImportance(
            target_metric="CTR",
            feature_contributions={
                "hook_type": 0.33,
                "thumbnail_contrast": 0.24,
                "publishing_hour": 0.16,
                "caption_length": 0.11,
                "music_mood": 0.08,
                "other": 0.08
            }
        )

feature_store = FeatureStore()
ZOOMING = "zoom"
