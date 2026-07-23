import uuid
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from core.database.session import Base
from core.database.models import ScriptJob, ScriptPackage, ScriptVersion, KnowledgePackage, WorkerHeartbeat, ResearchJob
from brain.agents.script_agent import (
    is_valid_transition,
    is_transient_error,
    recover_orphaned_jobs,
    process_script_job,
    validate_script_quality
)
from providers.script.registry import script_registry
from providers.script.mock import MockScriptProvider
from providers.script.bedrock import BedrockScriptProvider
from apps.api.v1.scripts import create_script_job
from contracts.dto.script import ScriptJobCreateDTO

# 1. State Transition Matrix Tests
def test_script_state_transitions():
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
def test_script_error_classification():
    assert is_transient_error("ThrottlingException on Bedrock converse call") is True
    assert is_transient_error("HTTP 429: Rate limit exceeded") is True
    assert is_transient_error("Connection refused by botocore") is True
    assert is_transient_error("ValueError: Invalid json schema") is False


# 3. Provider Registry Verification
def test_script_provider_registry():
    provider = script_registry.get_provider("mock")
    assert isinstance(provider, MockScriptProvider)
    
    bedrock = script_registry.get_provider("bedrock")
    assert isinstance(bedrock, BedrockScriptProvider)


# 4. Mock Provider Action Tests
@pytest.mark.asyncio
async def test_mock_provider_generation():
    provider = MockScriptProvider()
    kp_data = {
        "topic": "Space Travel",
        "summary": "Exploration of Mars and beyond",
        "keywords": ["Mars", "Space", "SpaceX"],
        "audience": ["General public"],
        "references": ["https://mars.nasa.gov"]
    }
    
    # Generate
    script = await provider.generate(kp_data, "youtube_shorts", "en")
    assert script["title"] == "The Ultimate Guide to Space Travel"
    assert script["hook"].startswith("Did you know")
    assert len(script["scene_breakdown"]) == 3
    assert script["scene_breakdown"][0]["scene_number"] == 1
    assert "Mars" in script["scene_breakdown"][0]["narration"]
    
    # Review
    review = await provider.review(script, "youtube_shorts")
    assert review["overall_score"] == 0.85
    assert len(review["suggestions"]) > 0
    
    # Improve
    improved = await provider.improve(script, review, "youtube_shorts")
    assert improved["hook"].startswith("[IMPROVED]")
    assert improved["scene_breakdown"][1]["narration"].startswith("[IMPROVED NARRATION]")


# 5. Quality Gate Rules Checks
def test_script_quality_gates():
    valid_script = {
        "hook": "Attention grabber!",
        "cta": "Click here now!",
        "scene_breakdown": [
            {
                "scene_number": 1,
                "visual_prompt": "Cinematic shot",
                "narration": "Narration text"
            }
        ],
        "thumbnail_prompt": "Thumbnail concept text"
    }
    
    valid_review = {"overall_score": 0.8}
    
    # Should pass without exception
    validate_script_quality(valid_script, valid_review)

    # 1. Missing Hook
    bad = dict(valid_script, hook="")
    with pytest.raises(ValueError, match="Missing Hook"):
        validate_script_quality(bad, valid_review)

    # 2. Missing CTA
    bad = dict(valid_script, cta=" ")
    with pytest.raises(ValueError, match="Missing CTA"):
        validate_script_quality(bad, valid_review)

    # 3. Missing Scene breakdown
    bad = dict(valid_script, scene_breakdown=[])
    with pytest.raises(ValueError, match="Missing Scene List"):
        validate_script_quality(bad, valid_review)

    # 4. Scene with empty visual prompt
    bad = dict(valid_script, scene_breakdown=[{"scene_number": 1, "visual_prompt": "", "narration": "Text"}])
    with pytest.raises(ValueError, match="empty visual prompt"):
        validate_script_quality(bad, valid_review)

    # 5. Scene with empty narration
    bad = dict(valid_script, scene_breakdown=[{"scene_number": 1, "visual_prompt": "Shot", "narration": ""}])
    with pytest.raises(ValueError, match="empty narration"):
        validate_script_quality(bad, valid_review)

    # 6. Missing Thumbnail prompt
    bad = dict(valid_script, thumbnail_prompt=None)
    with pytest.raises(ValueError, match="Missing Thumbnail Prompt"):
        validate_script_quality(bad, valid_review)

    # 7. Low Score Gate
    with pytest.raises(ValueError, match="falls below minimum threshold"):
        validate_script_quality(valid_script, {"overall_score": 0.5})


# 6. Database Operations & Lineage Tests
@pytest.mark.asyncio
async def test_agent_job_processing(db):
    # Setup research job first
    res_job = ResearchJob(
        id=uuid.uuid4(),
        topic="Srinivasa Ramanujan",
        status="SUCCESS",
        stage="COMPLETED"
    )
    db.add(res_job)
    db.commit()

    # Setup knowledge package
    kp = KnowledgePackage(
        id=uuid.uuid4(),
        job_id=res_job.id,
        topic="Srinivasa Ramanujan",
        summary="Indian mathematical genius",
        keywords=["Ramanujan", "Mathematics"],
        audience=["Math enthusiasts"],
        pain_points=["Proofs"],
        statistics=["3900 equations"],
        story_structure={"hook": "Clerk to genius"},
        visual_ideas={"scene_suggestions": ["Slate chalk"]}
    )
    db.add(kp)
    db.commit()

    # Setup script job
    job = ScriptJob(
        id=uuid.uuid4(),
        knowledge_package_id=kp.id,
        provider="mock",
        platform="youtube_shorts",
        language="ta",
        status="QUEUED",
        stage="VALIDATING"
    )
    db.add(job)
    db.commit()

    # Move to PROCESSING
    job.status = "PROCESSING"
    db.add(job)
    db.commit()

    # Process job using mock provider
    await process_script_job(db, job)

    db.refresh(job)
    assert job.status == "SUCCESS"
    assert job.stage == "COMPLETED"
    assert job.progress == 1.0
    
    # Assert package details
    assert len(job.packages) == 1
    pkg = job.packages[0]
    assert pkg.title == "The Ultimate Guide to Srinivasa Ramanujan"
    assert pkg.version == 1
    assert pkg.quality_score == 0.85
    assert len(pkg.scene_breakdown) == 3
    
    # Assert versions details
    assert len(pkg.versions) == 1
    ver = pkg.versions[0]
    assert ver.version == 1
    assert ver.parent_version is None
    assert ver.lineage_action == "INITIAL"


# 7. API Routes Endpoints Tests
def test_api_scripts_routes(client, db):
    # Setup research job first
    res_job = ResearchJob(
        id=uuid.uuid4(),
        topic="Quantum Computing",
        status="SUCCESS",
        stage="COMPLETED"
    )
    db.add(res_job)
    db.commit()

    # Setup knowledge package
    kp = KnowledgePackage(
        id=uuid.uuid4(),
        job_id=res_job.id,
        topic="Quantum Computing",
        summary="Introduction to Qubits",
        keywords=["Qubit", "Quantum"],
        audience=["Tech people"],
        pain_points=["Math difficulty"],
        statistics=["1000 physical qubits"],
        story_structure={"hook": "Quantum supremacy"},
        visual_ideas={"scene_suggestions": ["Cool laser chips"]}
    )
    db.add(kp)
    db.commit()

    # 1. POST /v1/scripts (create)
    resp = client.post("/v1/scripts", json={
        "knowledge_package_id": str(kp.id),
        "platform": "youtube_shorts",
        "language": "en",
        "priority": 1
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"
    assert job_data["platform"] == "youtube_shorts"

    # 2. GET /v1/scripts (list)
    resp = client.get("/v1/scripts")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/scripts/metrics (metrics)
    resp = client.get("/v1/scripts/metrics")
    assert resp.status_code == 200
    metrics = resp.json()
    assert metrics["jobs_queued"] >= 1

    # 4. GET /v1/scripts/{id} (retrieve detail)
    resp = client.get(f"/v1/scripts/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 5. Delete or Cancel Job
    resp = client.delete(f"/v1/scripts/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


# 8. Regeneration and Version Lineage API Tests
def test_api_scripts_regeneration(client, db):
    # Setup research job first
    res_job = ResearchJob(
        id=uuid.uuid4(),
        topic="Fusion Energy",
        status="SUCCESS",
        stage="COMPLETED"
    )
    db.add(res_job)
    db.commit()

    # Setup knowledge package
    kp = KnowledgePackage(
        id=uuid.uuid4(),
        job_id=res_job.id,
        topic="Fusion Energy",
        summary="Tokamak experiments",
        keywords=["Tokamak", "Fusion"],
        audience=["Scientists"],
        pain_points=["Net gain"],
        statistics=["Q factor of 1.5"],
        story_structure={"hook": "Star power on Earth"},
        visual_ideas={"scene_suggestions": ["Glowing plasma ring"]}
    )
    db.add(kp)
    db.commit()

    # Setup success job and package
    job = ScriptJob(
        id=uuid.uuid4(),
        knowledge_package_id=kp.id,
        provider="mock",
        platform="youtube_shorts",
        language="en",
        status="SUCCESS",
        stage="COMPLETED"
    )
    db.add(job)
    db.commit()

    pkg = ScriptPackage(
        id=uuid.uuid4(),
        job_id=job.id,
        knowledge_package_id=kp.id,
        title="Fusion Power 101",
        platform="youtube_shorts",
        language="en",
        hook="Original Hook",
        problem="Energy crisis",
        story="Tokamak experiments history",
        solution="Magnetic confinement",
        cta="Subscribe",
        narration="Original narration text content.",
        scene_breakdown=[{"scene_number": 1, "visual_prompt": "Plasma", "narration": "Narration"}],
        version=1,
        quality_score=0.8,
        review_report={"overall_score": 0.8}
    )
    db.add(pkg)
    db.commit()

    ver = ScriptVersion(
        id=uuid.uuid4(),
        script_package_id=pkg.id,
        version=1,
        parent_version=None,
        lineage_action="INITIAL",
        title=pkg.title,
        hook=pkg.hook,
        problem=pkg.problem,
        story=pkg.story,
        solution=pkg.solution,
        cta=pkg.cta,
        narration=pkg.narration,
        scene_breakdown=pkg.scene_breakdown,
        quality_score=pkg.quality_score,
        review_report=pkg.review_report
    )
    db.add(ver)
    db.commit()

    # Call POST /v1/scripts/{id}/regenerate
    resp = client.post(f"/v1/scripts/{job.id}/regenerate")
    assert resp.status_code == 200
    pkg_data = resp.json()
    assert pkg_data["version"] == 2
    assert isinstance(pkg_data["hook"], str)
    
    # Retrieve detail to verify versions array is present
    resp = client.get(f"/v1/scripts/{job.id}")
    job_detail = resp.json()
    assert len(job_detail["packages"][0]["versions"]) == 2
