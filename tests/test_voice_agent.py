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
    VoiceJob,
    VoicePackage,
    SceneVoice,
    VoiceVersion
)
from brain.agents.voice_agent import (
    is_valid_transition,
    is_transient_error,
    recover_orphaned_jobs,
    process_voice_job,
    validate_scene_voice,
    build_ssml_narration
)
from providers.voice.registry import voice_registry
from providers.voice.mock import MockVoiceProvider
from providers.voice.bedrock import BedrockVoiceProvider
from providers.voice.elevenlabs_provider import ElevenLabsVoiceProvider
from apps.api.v1.voices import create_voice_job
from contracts.dto.voice import VoiceJobCreateDTO

# 1. State Transition Matrix Tests
def test_voice_state_transitions():
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
def test_voice_error_classification():
    assert is_transient_error("ThrottlingException on Polly voice synthesis") is True
    assert is_transient_error("HTTP 429: Too many requests") is True
    assert is_transient_error("Connection refused for Polly audio client stream") is True
    assert is_transient_error("ValueError: Invalid voice rate setting") is False


# 3. Provider Registry Verification
def test_voice_provider_registry():
    provider = voice_registry.get_provider("mock")
    assert isinstance(provider, MockVoiceProvider)
    
    bedrock = voice_registry.get_provider("bedrock")
    assert isinstance(bedrock, BedrockVoiceProvider)

    eleven = voice_registry.get_provider("elevenlabs")
    assert isinstance(eleven, ElevenLabsVoiceProvider)


# 4. SSML Builder Abstraction Tests
def test_ssml_builder():
    text = "We are training Tokamak fusion systems."
    dict_map = {"Tokamak": "Toe-kah-mack"}
    ssml = build_ssml_narration(text, speed="1.05x", pitch="+2%", volume="+1dB", dictionary=dict_map)
    assert "<speak>" in ssml
    assert "<prosody" in ssml
    assert "rate='1.05x'" in ssml
    assert "pitch='+2%'" in ssml
    assert "volume='+1dB'" in ssml
    assert "<sub alias='Toe-kah-mack'>Tokamak</sub>" in ssml


# 5. Quality Gate Rules Checks
def test_voice_quality_gates():
    # Setup temporary directory and mock file to make asset valid on disk
    os.makedirs("artifacts/audio", exist_ok=True)
    temp_file = "artifacts/audio/test_scene_gate.mp3"
    with open(temp_file, "wb") as f:
        f.write(b"MP3")

    valid_asset = {
        "local_path": temp_file,
        "word_alignment": [{"word": "Test", "start_time_ms": 0, "end_time_ms": 200}],
        "quality_score": 0.85
    }
    
    # Should pass without exception
    validate_scene_voice(valid_asset)

    # 1. Missing local file
    bad = dict(valid_asset, local_path="artifacts/audio/does_not_exist_99.mp3")
    with pytest.raises(ValueError, match="Audio file is missing"):
        validate_scene_voice(bad)

    # 2. Missing alignment
    bad = dict(valid_asset, word_alignment=[])
    with pytest.raises(ValueError, match="Missing word alignment timings"):
        validate_scene_voice(bad)

    # 3. Low Quality Score
    bad = dict(valid_asset, quality_score=0.5)
    with pytest.raises(ValueError, match="falls below threshold 0.7"):
        validate_scene_voice(bad)


# 6. Database Operations & Version Lineage Tests
@pytest.mark.asyncio
async def test_voice_agent_job_processing(db):
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
            {"scene_number": 1, "narration": "Glowing plasma ring inside Tokamak reactor.", "camera_angle": "Wide pan", "duration": 6.0}
        ]
    )
    db.add(script_pkg)
    db.commit()

    # Setup voice job
    job = VoiceJob(
        id=uuid.uuid4(),
        script_package_id=script_pkg.id,
        provider="mock",
        voice_model="MockSpeech-v2",
        language="en",
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
    await process_voice_job(db, job)

    db.refresh(job)
    assert job.status == "SUCCESS"
    assert job.stage == "COMPLETED"
    assert job.progress == 1.0
    
    # Assert package details
    assert len(job.packages) == 1
    pkg = job.packages[0]
    assert pkg.platform == "youtube_shorts"
    assert pkg.version == 1
    assert pkg.overall_duration_ms > 0
    assert pkg.total_words > 0
    
    # Assert Scene Voices details
    assert len(pkg.assets) == 1
    asset = pkg.assets[0]
    assert asset.scene_number == 1
    assert asset.narration == "Glowing plasma ring inside Tokamak reactor."
    assert asset.storage_key.startswith("audio/")
    assert len(asset.word_alignment) > 0
    
    # Assert version details
    assert len(pkg.versions) == 1
    ver = pkg.versions[0]
    assert ver.version == 1
    assert ver.lineage_action == "INITIAL"


# 7. API Routes Endpoints Tests
def test_api_voices_routes(client, db):
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
        scene_breakdown=[{"scene_number": 1, "narration": "Rover landing", "duration": 5.0}]
    )
    db.add(script_pkg)
    db.commit()

    # 1. POST /v1/voices (create)
    resp = client.post("/v1/voices", json={
        "script_package_id": str(script_pkg.id),
        "language": "en",
        "priority": 2
    })
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"

    # 2. GET /v1/voices (list)
    resp = client.get("/v1/voices")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. GET /v1/voices/metrics (metrics)
    resp = client.get("/v1/voices/metrics")
    assert resp.status_code == 200
    metrics = resp.json()
    assert metrics["jobs_queued"] >= 1

    # 4. GET /v1/voices/{id} (retrieve detail)
    resp = client.get(f"/v1/voices/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id

    # 5. Cancel or Delete Job
    resp = client.delete(f"/v1/voices/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


# 8. Regeneration, Cloned Voices, and Version Lineage API Tests
def test_api_voices_regeneration_and_cloning(client, db):
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
        scene_breakdown=[{"scene_number": 1, "narration": "Qubits narration details.", "duration": 5.0}]
    )
    db.add(script_pkg)
    db.commit()

    # Setup success job, package and assets
    job = VoiceJob(
        id=uuid.uuid4(),
        script_package_id=script_pkg.id,
        provider="mock",
        voice_model="MockSpeech-v2",
        language="en",
        status="SUCCESS",
        stage="COMPLETED"
    )
    db.add(job)
    db.commit()

    pkg = VoicePackage(
        id=uuid.uuid4(),
        job_id=job.id,
        script_package_id=script_pkg.id,
        platform="youtube_shorts",
        language="en",
        voice_profile={"voice_id": "Aditi", "speed": "1.0x", "pitch": "+0%", "volume": "+0dB"},
        speaking_style="Narrative",
        overall_duration_ms=5000,
        total_words=4,
        total_scenes=1,
        audio_format="mp3",
        sample_rate=44100,
        bitrate=192000,
        version=1,
        quality_score=0.9
    )
    db.add(pkg)
    db.commit()

    # Setup temporary file
    os.makedirs("artifacts/audio", exist_ok=True)
    temp_file = "artifacts/audio/test_scene_reg.mp3"
    with open(temp_file, "wb") as f:
        f.write(b"MP3")

    asset = SceneVoice(
        id=uuid.uuid4(),
        voice_package_id=pkg.id,
        scene_number=1,
        duration_ms=5000,
        narration="Qubits narration details.",
        local_path=temp_file,
        storage_key="audio/test_scene_reg.mp3",
        voice_id="Aditi",
        provider="mock",
        model="MockSpeech-v2",
        language="en"
    )
    db.add(asset)
    db.commit()

    ver = VoiceVersion(
        id=uuid.uuid4(),
        voice_package_id=pkg.id,
        version=1,
        parent_version=None,
        lineage_action="INITIAL",
        assets_snapshot=[{"scene_number": 1, "local_path": temp_file, "narration": asset.narration}]
    )
    db.add(ver)
    db.commit()

    # 1. Call POST /v1/voices/{id}/regenerate
    resp = client.post(f"/v1/voices/{job.id}/regenerate?scene_number=1")
    assert resp.status_code == 200
    pkg_data = resp.json()
    assert pkg_data["version"] == 2

    # 2. Call POST /v1/voices/{id}/clone
    resp = client.post(f"/v1/voices/{job.id}/clone?name=DavidCustom")
    assert resp.status_code == 200
    clone_data = resp.json()
    assert clone_data["status"] == "cloned"
    assert clone_data["name"] == "DavidCustom"
    assert "cloned_voice_id" in clone_data["profile"]
