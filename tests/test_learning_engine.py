import os
import uuid
import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient

from core.database.session import Base
from core.database.models import (
    ResearchJob,
    KnowledgePackage,
    ScriptJob,
    ScriptPackage,
    ImageJob,
    ImagePackage,
    VoiceJob,
    VoicePackage,
    VideoJob,
    VideoPackage,
    QualityJob,
    QualityPackage,
    InstagramPublishJob,
    PublicationPackage,
    InstagramPublication,
    InstagramInsightSnapshot,
    LearningJob,
    LearningDataset,
    LearningPackage,
    PerformanceSnapshot,
    LearningSignal,
    LearningRecommendation,
    RecommendationFeedback,
    ExperimentResult,
    LearningVersion
)
from providers.analytics.feature_store import feature_store, feature_definition_registry, FeatureVector
from providers.analytics.collectors import analytics_collector
from providers.analytics.engine import analytics_engine, confidence_engine, correlation_engine, recommendation_engine
from brain.agents.learning_agent import process_learning_job


# 1. Feature Store & FeatureDefinition Registry Tests
def test_feature_store_registry():
    definitions = feature_definition_registry.list_all()
    assert len(definitions) >= 5

    def_hook = feature_definition_registry.get("script_hook_type")
    assert def_hook is not None
    assert "ScriptPackage" in def_hook.source_packages

    vec = feature_store.extract_vector(
        item_id="item_test",
        quality_pkg_id=str(uuid.uuid4()),
        publication_id=str(uuid.uuid4())
    )
    assert vec.script.word_count > 0
    assert len(vec.dense_vector) > 0

    importance = feature_store.calculate_importance([vec, vec])
    assert "hook_type" in importance.feature_contributions
    assert sum(importance.feature_contributions.values()) >= 0.95


# 2. Analytics Engine & Confidence Engine Tests
def test_confidence_and_correlation_engine():
    conf_score = confidence_engine.calculate_confidence(
        sample_size=25,
        variance=0.10,
        consistency_score=0.90,
        platform_coverage=2,
        has_experiment_support=True
    )
    assert conf_score >= 0.85

    vectors = [feature_store.extract_vector(f"i_{idx}", str(uuid.uuid4()), None) for idx in range(5)]
    signals = correlation_engine.evaluate_correlations(vectors)
    assert len(signals) >= 3

    recs = recommendation_engine.generate_recommendations(signals, feature_store.calculate_importance(vectors))
    assert len(recs) >= 3
    target_agents = [r["target_agent"] for r in recs]
    assert "ScriptAgent text" not in target_agents
    assert "ScriptAgent" in target_agents


# 3. Background Learning Agent Job Processing Test
@pytest.mark.asyncio
async def test_learning_agent_job_processing(db):
    res_job = ResearchJob(id=uuid.uuid4(), topic="Learning Test", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    kp = KnowledgePackage(id=uuid.uuid4(), job_id=res_job.id, topic="Learning Test", summary="Summary")
    db.add(kp)
    db.commit()

    script_job = ScriptJob(id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube", status="SUCCESS")
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(id=uuid.uuid4(), job_id=script_job.id, knowledge_package_id=kp.id, title="Title", platform="youtube", language="en", hook="H", problem="P", story="S", solution="Sol", cta="C", narration="N.", scene_breakdown=[{"scene_number": 1, "duration": 4.0}])
    db.add(script_pkg)
    db.commit()

    img_job = ImageJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", status="SUCCESS")
    db.add(img_job)
    db.commit()

    img_pkg = ImagePackage(id=uuid.uuid4(), job_id=img_job.id, script_package_id=script_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", style_preset="Photorealistic", quality_score=0.9)
    db.add(img_pkg)
    db.commit()

    voice_job = VoiceJob(id=uuid.uuid4(), script_package_id=script_pkg.id, provider="mock", voice_model="MockSpeech", language="en", status="SUCCESS")
    db.add(voice_job)
    db.commit()

    voice_pkg = VoicePackage(id=uuid.uuid4(), job_id=voice_job.id, script_package_id=script_pkg.id, platform="youtube", language="en", total_scenes=1, overall_duration_ms=4000, quality_score=0.9)
    db.add(voice_pkg)
    db.commit()

    video_job = VideoJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, renderer="mock", status="SUCCESS")
    db.add(video_job)
    db.commit()

    video_pkg = VideoPackage(id=uuid.uuid4(), job_id=video_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, platform="youtube", resolution="1920x1080", aspect_ratio="16:9", duration_ms=4000, storage_key="video/outputs/output_1.mp4", version=1, quality_score=0.9)
    db.add(video_pkg)
    db.commit()

    quality_job = QualityJob(id=uuid.uuid4(), script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id, provider="policy_engine", status="SUCCESS")
    db.add(quality_job)
    db.commit()

    approved_pkg = QualityPackage(
        id=uuid.uuid4(), job_id=quality_job.id, script_package_id=script_pkg.id, image_package_id=img_pkg.id, voice_package_id=voice_pkg.id, video_package_id=video_pkg.id,
        production_readiness_score=0.94, is_approved_for_publishing=True, publishing_lifecycle_state="Approved", quality_score=0.94
    )
    db.add(approved_pkg)
    db.commit()

    ig_job = InstagramPublishJob(id=uuid.uuid4(), quality_package_id=approved_pkg.id, platform_media_type="Reels", status="SUCCESS")
    db.add(ig_job)
    db.commit()

    pub_pkg = PublicationPackage(
        id=uuid.uuid4(), job_id=ig_job.id, quality_package_id=approved_pkg.id, publishing_lifecycle_state="Published", platform_name="instagram", platform_profile_id="instagram_reels", quality_score=0.94
    )
    db.add(pub_pkg)
    db.commit()

    pub = InstagramPublication(
        id=uuid.uuid4(), publication_package_id=pub_pkg.id, instagram_media_id="1802999", permalink="https://instagram.com/p/123", caption="Test"
    )
    db.add(pub)
    db.commit()

    snapshot = InstagramInsightSnapshot(
        id=uuid.uuid4(), publication_id=pub.id, views=3200, reach=2500, impressions=4000, likes=210, comments=35, shares=45, saves=50, engagement_rate=0.12
    )
    db.add(snapshot)
    db.commit()

    learning_job = LearningJob(id=uuid.uuid4(), target_platform="all", learning_window_days=30, learning_mode="batch", status="PROCESSING", stage="COLLECTING")
    db.add(learning_job)
    db.commit()

    await process_learning_job(db, learning_job)

    db.refresh(learning_job)
    assert learning_job.status == "SUCCESS"
    assert learning_job.stage == "COMPLETED"

    # Assert LearningPackage & Dataset
    assert len(learning_job.packages) == 1
    l_pkg = learning_job.packages[0]
    assert l_pkg.target_platform == "all"
    assert l_pkg.learning_confidence >= 0.70

    # Assert LearningSignals, Recommendations, Experiments, Versions
    assert len(l_pkg.signals) >= 3
    assert len(l_pkg.recommendations) >= 3
    assert len(l_pkg.experiments) >= 1
    assert len(l_pkg.versions) == 1


# 4. REST API Endpoints & Feedback Loop Tests
def test_api_learning_routes(client, db):
    # 1. POST /v1/learning (create)
    resp = client.post("/v1/learning", json={
        "target_platform": "all",
        "learning_window_days": 30,
        "learning_mode": "batch",
        "priority": 1
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"

    # 2. GET /v1/learning (list)
    resp = client.get("/v1/learning")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/learning/metrics (metrics)
    resp = client.get("/v1/learning/metrics")
    assert resp.status_code == 200
    assert resp.json()["jobs_queued"] >= 1

    # 4. GET /v1/learning/signals (signals)
    resp = client.get("/v1/learning/signals")
    assert resp.status_code == 200

    # 5. GET /v1/learning/recommendations (recommendations)
    resp = client.get("/v1/learning/recommendations")
    assert resp.status_code == 200

    # 6. GET /v1/learning/{id} (detail)
    resp = client.get(f"/v1/learning/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 7. POST /v1/learning/{id}/refresh (refresh)
    resp = client.post(f"/v1/learning/{job_id}/refresh")
    assert resp.status_code == 200
    assert resp.json()["learning_mode"] == "incremental"
