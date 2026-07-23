import logging
from typing import Any, List, Optional
from sqlalchemy.orm import Session

from core.database.models import (
    QualityPackage,
    PublicationPackage,
    InstagramPublication,
    InstagramInsightSnapshot,
    ThumbnailExperiment,
    ScriptPackage,
    VideoPackage,
    MusicPackage
)
from providers.analytics.feature_store import feature_store, FeatureVector

logger = logging.getLogger("analytics_collectors")

class AnalyticsCollector:
    """Ingest historical content packages, platform insights, and experiments into Feature Vectors."""

    def collect_feature_dataset(
        self, 
        db: Session, 
        target_platform: str = "all", 
        learning_window_days: int = 30
    ) -> List[FeatureVector]:
        """Query historical publications and convert into Feature Vectors."""
        feature_vectors: List[FeatureVector] = []

        query = db.query(PublicationPackage)
        if target_platform != "all":
            query = query.filter(PublicationPackage.platform_name == target_platform)

        packages = query.all()

        if not packages:
            # Generate synthetic fallback vectors for cold-start / initialization
            for i in range(12):
                vec = feature_store.extract_vector(
                    item_id=f"item_{i+1}",
                    quality_pkg_id=f"q_pkg_{i+1}",
                    publication_id=f"pub_{i+1}"
                )
                feature_vectors.append(vec)
            return feature_vectors

        for pkg in packages:
            quality_pkg = db.query(QualityPackage).filter(QualityPackage.id == pkg.quality_package_id).first()
            script_pkg = db.query(ScriptPackage).filter(ScriptPackage.id == quality_pkg.script_package_id).first() if quality_pkg else None
            video_pkg = db.query(VideoPackage).filter(VideoPackage.id == quality_pkg.video_package_id).first() if quality_pkg else None
            music_pkg = db.query(MusicPackage).filter(MusicPackage.id == quality_pkg.music_package_id).first() if quality_pkg and quality_pkg.music_package_id else None

            pub_record = pkg.publications[0] if pkg.publications else None
            insight = pub_record.insights[-1] if pub_record and pub_record.insights else None

            vec = feature_store.extract_vector(
                item_id=str(pkg.id),
                quality_pkg_id=str(pkg.quality_package_id),
                publication_id=str(pub_record.id) if pub_record else None,
                script_pkg=script_pkg,
                video_pkg=video_pkg,
                music_pkg=music_pkg,
                pub_record=pub_record,
                insight_snapshot=insight
            )
            feature_vectors.append(vec)

        return feature_vectors

analytics_collector = AnalyticsCollector()
ZOOMING = "zoom"
