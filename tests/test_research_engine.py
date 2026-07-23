import uuid
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from core.database.session import Base
from core.database.models import ResearchJob, ResearchSource, KnowledgePackage, Keyword, Competitor
from brain.operations.research_agent import (
    is_valid_transition,
    is_transient_error,
    recover_orphaned_jobs,
    process_research_job
)
from providers.research.registry import knowledge_registry
from providers.research.google_search import GoogleSearchKnowledgeProvider
from providers.research.wikipedia import WikipediaKnowledgeProvider
from apps.api.v1.research import create_research_job
from contracts.dto.research import ResearchJobCreateDTO


# 1. State Transition Matrix Tests
def test_research_state_transitions():
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
def test_research_error_classification():
    assert is_transient_error("Connection timeout on Bedrock converse endpoint") is True
    assert is_transient_error("HTTP 429: ThrottlingException") is True
    assert is_transient_error("Connection refused for boto3") is True
    assert is_transient_error("ValidationException: Schema is malformed") is False


# 3. Knowledge Provider Layer Tests
@pytest.mark.asyncio
async def test_knowledge_providers():
    topic = "Tamil Literature"
    
    # Google Search Provider
    google = GoogleSearchKnowledgeProvider()
    discovery = await google.discover(topic)
    assert len(discovery) == 3
    assert "Tamil" in discovery[0]["title"] or "Tamil" in discovery[0]["snippet"]
    
    collected = await google.collect(discovery)
    assert len(collected) == 3
    assert "raw_html" in collected[0]
    
    extracted = await google.extract(collected)
    assert len(extracted) == 3
    assert "content" in extracted[0]
    
    ranked = google.rank(extracted, topic)
    assert len(ranked) == 3
    assert ranked[0]["relevance_score"] >= ranked[1]["relevance_score"]

    # Wikipedia Provider
    wiki = WikipediaKnowledgeProvider()
    wiki_disc = await wiki.discover(topic)
    assert len(wiki_disc) == 1
    assert "wikipedia" in wiki_disc[0]["url"]


# 4. Knowledge Registry Tests
def test_knowledge_registry():
    provs = knowledge_registry.get_all_providers()
    assert len(provs) >= 2
    
    names = [p.name for p in provs]
    assert "google_search" in names
    assert "wikipedia" in names
    
    google = knowledge_registry.get_provider("google_search")
    assert isinstance(google, GoogleSearchKnowledgeProvider)


# 5. REST API Router Tests
def test_research_api_endpoints(client: TestClient):
    # Enqueue new job
    payload = {
        "topic": "Autonomous AI Agents",
        "priority": 1,
        "tenant_id": "tenant-xyz"
    }
    
    res = client.post("/v1/research", json=payload)
    assert res.status_code == 200
    job_data = res.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"
    assert job_data["topic"] == "Autonomous AI Agents"
    assert job_data["stage"] == "DISCOVERING"

    # List research jobs
    list_res = client.get("/v1/research")
    assert list_res.status_code == 200
    jobs_list = list_res.json()
    assert len(jobs_list) >= 1
    assert any(j["id"] == job_id for j in jobs_list)

    # Filter metrics
    metrics_res = client.get("/v1/research/metrics")
    assert metrics_res.status_code == 200
    metrics_data = metrics_res.json()
    assert "jobs_queued" in metrics_data
    assert "worker_is_running" in metrics_data

    # Cancel a job
    cancel_res = client.delete(f"/v1/research/{job_id}")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Retry a job
    retry_res = client.post(f"/v1/research/{job_id}/retry")
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "QUEUED"


# 6. Idempotency Check Tests (Direct)
@pytest.mark.asyncio
async def test_research_idempotency_direct(db):
    payload = ResearchJobCreateDTO(
        topic="Bedrock Orchestration",
        priority=2,
        tenant_id="tenant-idemp"
    )
    
    # First creation
    job1 = await create_research_job(payload, db)
    assert job1.status == "QUEUED"

    # Mutate to SUCCESS
    job1.status = "SUCCESS"
    db.add(job1)
    db.commit()

    # Second creation returns existing successful job
    job2 = await create_research_job(payload, db)
    assert job2.id == job1.id
    assert job2.status == "SUCCESS"


# 7. Asynchronous Agent Job Synthesis & Bedrock Tests
@pytest.mark.asyncio
async def test_agent_job_processing(db):
    job = ResearchJob(
        id=uuid.uuid4(),
        topic="Srinivasa Ramanujan",
        status="QUEUED",
        stage="DISCOVERING"
    )
    db.add(job)
    db.commit()

    # Transition to PROCESSING to satisfy state matrix
    job.status = "PROCESSING"
    db.add(job)
    db.commit()

    # Mock the LLM provider invocation
    mock_llm_text = """{
      "topic": "Srinivasa Ramanujan",
      "summary": "Srinivasa Ramanujan was one of India's greatest mathematical geniuses.",
      "keywords": ["Ramanujan", "Mathematics", "Genius", "Number Theory", "Mock"],
      "pain_points": ["Understanding mock equations", "Resolving infinite series"],
      "faqs": [{"q": "Where did he study?", "a": "Cambridge University"}],
      "statistics": ["Discovered nearly 3900 identities"],
      "competitors": [{"name": "Hardy", "summary": "Collaborator", "strengths": ["Formal proofs"], "weaknesses": ["Lack of intuition"]}],
      "story_structure": {
        "hook": "How did a clerk from India solve the world's hardest math?",
        "problem": "Unsolved modular mock equations.",
        "story": "His correspondence with G.H. Hardy in 1913.",
        "solution": "Ramanujan's infinite series breakthroughs.",
        "cta": "Explore the history of mathematics!"
      },
      "visual_ideas": {
        "scene_suggestions": ["Clerk writing on slate chalk boards"],
        "characters": ["Ramanujan in traditional Indian attire"],
        "camera_angles": ["Close up on numbers"],
        "background_ideas": ["Chalk mathematical diagrams"],
        "color_themes": ["Warm vintage sepia"],
        "emotion": "Wonder",
        "style_references": ["Period drama cinematic"]
      },
      "hooks": ["This man saw math in dreams."],
      "titles": ["Ramanujan: The Man Who Knew Infinity"],
      "ctas": ["Subscribe for historical math mysteries."]
    }"""

    with patch("providers.llm.bedrock_llm.BedrockLLMProvider.generate", return_value=mock_llm_text):
        await process_research_job(db, job)

    db.refresh(job)
    assert job.status == "SUCCESS"
    assert job.stage == "COMPLETED"
    assert job.progress == 1.0
    assert len(job.packages) == 1
    
    # Assert package structure matching schema
    pkg = job.packages[0]
    assert pkg.topic == "Srinivasa Ramanujan"
    assert "mathematical geniuses" in pkg.summary
    assert "Cambridge University" in pkg.faqs[0]["q"] or "Cambridge University" in pkg.faqs[0]["a"]
    assert pkg.story_structure["hook"] == "How did a clerk from India solve the world's hardest math?"
    assert pkg.visual_ideas["emotion"] == "Wonder"
    assert "Warm vintage sepia" in pkg.visual_ideas["color_themes"]

    # Verify sources and keywords populated
    assert len(job.sources) >= 1
    assert len(job.keywords) >= 1
    assert len(job.competitors) >= 1
