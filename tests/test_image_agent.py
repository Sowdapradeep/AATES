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
    SceneAsset,
    ImageVersion
)
from brain.agents.image_agent import (
    is_valid_transition,
    is_transient_error,
    recover_orphaned_jobs,
    process_image_job,
    validate_scene_asset,
    build_scene_prompt
)
from providers.image.registry import image_registry
from providers.image.mock import MockImageProvider
from providers.image.bedrock import BedrockImageProvider
from apps.api.v1.images import create_image_job
from contracts.dto.image import ImageJobCreateDTO

# 1. State Transition Matrix Tests
def test_image_state_transitions():
    assert is_valid_transition("QUEUED", "PROCESSING") is True
    assert is_valid_transition("QUEUED", "CANCELLED") is True
    assert is_valid_transition("PROCESSING", "SUCCESS") is True
    assert is_valid_transition("PROCESSING", "RETRYING") is True
    assert is_valid_transition("PROCESSING", "FAILED") is True
    assert is_valid_transition("FAILED", "QUEUED") is True
    assert is_valid_transition("CANCELLED", "QUEUED") is True
    
    # Invalid transitions
    assert is_valid_transition("SUCCESS", "PROCESSING") is False
    assert is_valid_transition("FAILED", "SUCCESS") is False


# 2. Transient Error Classification
def test_image_error_classification():
    assert is_transient_error("ThrottlingException on Bedrock image generator call") is True
    assert is_transient_error("HTTP 429: Too many requests") is True
    assert is_transient_error("Connection refused for S3 client upload") is True
    assert is_transient_error("ValueError: Invalid aspect ratio configuration") is False


# 3. Provider Registry Verification
def test_image_provider_registry():
    provider = image_registry.get_provider("mock")
    assert isinstance(provider, MockImageProvider)
    
    bedrock = image_registry.get_provider("bedrock")
    assert isinstance(bedrock, BedrockImageProvider)


# 4. Prompt Builder Abstraction Tests
def test_prompt_builder():
    scene = {
        "visual_prompt": "Space explorer standing on Mars surface looking at a red sky",
        "camera_angle": "Wide Pan Shot",
        "lighting": "Volumetric sunlight illumination",
        "background": "Dust storms",
        "emotion": "Dramatic"
    }
    prompt = build_scene_prompt(scene, "Cinematic")
    assert "Cinematic" in prompt
    assert "Mars" in prompt
    assert "Wide Pan Shot" in prompt
    assert "Volumetric sunlight" in prompt
    assert "Dust storms" in prompt


# 5. Quality Gate Rules Checks
def test_image_quality_gates():
    # Setup temporary directory and mock file to make asset valid on disk
    os.makedirs("artifacts/images", exist_ok=True)
    temp_file = "artifacts/images/test_scene_gate.png"
    with open(temp_file, "wb") as f:
        f.write(b"PNG")

    valid_asset = {
        "local_path": temp_file,
        "prompt": "Explaining the solar system",
        "quality_score": 0.85
    }
    
    # Should pass without exception
    validate_scene_asset(valid_asset, "9:16")

    # 1. Missing local file
    bad = dict(valid_asset, local_path="artifacts/images/does_not_exist_99.png")
    with pytest.raises(ValueError, match="Image file is missing"):
        validate_scene_asset(bad, "9:16")

    # 2. Missing Prompt
    bad = dict(valid_asset, prompt="")
    with pytest.raises(ValueError, match="Missing Prompt text"):
        validate_scene_asset(bad, "9:16")

    # 3. Low Quality Score
    bad = dict(valid_asset, quality_score=0.5)
    with pytest.raises(ValueError, match="falls below threshold 0.7"):
        validate_scene_asset(bad, "9:16")


# 6. Database Operations & Version Lineage Tests
@pytest.mark.asyncio
async def test_image_agent_job_processing(db):
    # Setup research job first
    res_job = ResearchJob(id=uuid.uuid4(), topic="Fusion Energy", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    # Setup knowledge package
    kp = KnowledgePackage(
        id=uuid.uuid4(), job_id=res_job.id, topic="Fusion Energy", summary="Tokamak", keywords=["Tokamak"]
    )
    db.add(kp)
    db.commit()

    # Setup script job
    script_job = ScriptJob(
        id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube_shorts", status="SUCCESS", stage="COMPLETED"
    )
    db.add(script_job)
    db.commit()

    # Setup script package
    script_pkg = ScriptPackage(
        id=uuid.uuid4(),
        job_id=script_job.id,
        knowledge_package_id=kp.id,
        title="Fusion Power 101",
        platform="youtube_shorts",
        language="en",
        hook="Original Hook",
        problem="Energy crisis",
        story="Tokamak experiments",
        solution="Confinement",
        cta="Subscribe",
        narration="Original narration text.",
        scene_breakdown=[
            {"scene_number": 1, "visual_prompt": "Glowing plasma ring", "camera_angle": "Wide pan", "duration": 6.0}
        ]
    )
    db.add(script_pkg)
    db.commit()

    # Setup image job
    job = ImageJob(
        id=uuid.uuid4(),
        script_package_id=script_pkg.id,
        provider="mock",
        status="QUEUED",
        stage="VALIDATING"
    )
    db.add(job)
    db.commit()

    # Transition to PROCESSING
    job.status = "PROCESSING"
    db.add(job)
    db.commit()

    # Run processing
    await process_image_job(db, job)

    db.refresh(job)
    assert job.status == "SUCCESS"
    assert job.stage == "COMPLETED"
    assert job.progress == 1.0
    
    # Assert package details
    assert len(job.packages) == 1
    pkg = job.packages[0]
    assert pkg.platform == "youtube_shorts"
    assert pkg.version == 1
    
    # Assert Scene Assets details
    assert len(pkg.assets) == 1
    asset = pkg.assets[0]
    assert asset.scene_number == 1
    assert "Glowing plasma" in asset.prompt
    assert asset.aspect_ratio == "9:16"
    assert asset.storage_key.startswith("images/")
    
    # Assert version details
    assert len(pkg.versions) == 1
    ver = pkg.versions[0]
    assert ver.version == 1
    assert ver.lineage_action == "INITIAL"


# 7. API Routes Endpoints Tests
def test_api_images_routes(client, db):
    # Setup research job first
    res_job = ResearchJob(id=uuid.uuid4(), topic="Space Travel", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    # Setup knowledge package
    kp = KnowledgePackage(
        id=uuid.uuid4(), job_id=res_job.id, topic="Space Travel", summary="Mars", keywords=["Space"]
    )
    db.add(kp)
    db.commit()

    # Setup script job and package
    script_job = ScriptJob(
        id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube_shorts", status="SUCCESS", stage="COMPLETED"
    )
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(
        id=uuid.uuid4(),
        job_id=script_job.id,
        knowledge_package_id=kp.id,
        title="Going to Mars",
        platform="youtube_shorts",
        language="en",
        hook="Mars secretly has oceans",
        problem="Cold climate",
        story="Rover findings",
        solution="Greenhouse effects",
        cta="Comment below",
        narration="Narration script text.",
        scene_breakdown=[{"scene_number": 1, "visual_prompt": "Rover landing", "duration": 5.0}]
    )
    db.add(script_pkg)
    db.commit()

    # 1. POST /v1/images (create)
    resp = client.post("/v1/images", json={
        "script_package_id": str(script_pkg.id),
        "priority": 2
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"

    # 2. GET /v1/images (list)
    resp = client.get("/v1/images")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/images/metrics (metrics)
    resp = client.get("/v1/images/metrics")
    assert resp.status_code == 200
    metrics = resp.json()
    assert metrics["jobs_queued"] >= 1

    # 4. GET /v1/images/{id} (retrieve detail)
    resp = client.get(f"/v1/images/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 5. Cancel or Delete Job
    resp = client.delete(f"/v1/images/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


# 8. Regeneration, Upscale, and Version Lineage API Tests
def test_api_images_regeneration_and_upscale(client, db):
    # Setup research job first
    res_job = ResearchJob(id=uuid.uuid4(), topic="Quantum Tech", status="SUCCESS", stage="COMPLETED")
    db.add(res_job)
    db.commit()

    # Setup knowledge package
    kp = KnowledgePackage(
        id=uuid.uuid4(), job_id=res_job.id, topic="Quantum Tech", summary="Qubits", keywords=["Qubits"]
    )
    db.add(kp)
    db.commit()

    # Setup script job and package
    script_job = ScriptJob(
        id=uuid.uuid4(), knowledge_package_id=kp.id, provider="mock", platform="youtube_shorts", status="SUCCESS", stage="COMPLETED"
    )
    db.add(script_job)
    db.commit()

    script_pkg = ScriptPackage(
        id=uuid.uuid4(),
        job_id=script_job.id,
        knowledge_package_id=kp.id,
        title="Intro to Qubits",
        platform="youtube_shorts",
        language="en",
        hook="Hook quantum",
        problem="Decoherence",
        story="Superposition mechanics",
        solution="Error correction",
        cta="Subscribe",
        narration="Qubits narration details.",
        scene_breakdown=[{"scene_number": 1, "visual_prompt": "Quantum chip", "duration": 5.0}]
    )
    db.add(script_pkg)
    db.commit()

    # Setup success job, package and assets
    job = ImageJob(
        id=uuid.uuid4(),
        script_package_id=script_pkg.id,
        provider="mock",
        status="SUCCESS",
        stage="COMPLETED"
    )
    db.add(job)
    db.commit()

    pkg = ImagePackage(
        id=uuid.uuid4(),
        job_id=job.id,
        script_package_id=script_pkg.id,
        platform="youtube_shorts",
        aspect_ratio="9:16",
        resolution="1080x1920",
        style_preset="Cinematic",
        overall_theme="Theme quantum",
        image_count=1,
        character_id="char-abc",
        version=1,
        quality_score=0.9
    )
    db.add(pkg)
    db.commit()

    # Setup temporary file
    os.makedirs("artifacts/images", exist_ok=True)
    temp_file = "artifacts/images/test_scene_reg.png"
    with open(temp_file, "wb") as f:
        f.write(b"PNG")

    asset = SceneAsset(
        id=uuid.uuid4(),
        image_package_id=pkg.id,
        scene_number=1,
        duration=5.0,
        prompt="Visual rendering of quantum chip",
        aspect_ratio="9:16",
        resolution="1080x1920",
        local_path=temp_file,
        storage_key="images/test_scene_reg.png",
        provider="mock",
        model="mock-sdxl"
    )
    db.add(asset)
    db.commit()

    ver = ImageVersion(
        id=uuid.uuid4(),
        image_package_id=pkg.id,
        version=1,
        parent_version=None,
        lineage_action="INITIAL",
        assets_snapshot=[{"scene_number": 1, "local_path": temp_file, "prompt": asset.prompt}]
    )
    db.add(ver)
    db.commit()

    # 1. Call POST /v1/images/{id}/regenerate
    resp = client.post(f"/v1/images/{job.id}/regenerate?scene_number=1")
    assert resp.status_code == 200
    pkg_data = resp.json()
    assert pkg_data["version"] == 2

    # 2. Call POST /v1/images/{id}/upscale
    resp = client.post(f"/v1/images/{job.id}/upscale?scene_number=1")
    assert resp.status_code == 200
    upscale_data = resp.json()
    assert upscale_data["status"] == "upscaled"
    assert upscale_data["scene_number"] == 1
