import uuid
import pytest
import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from core.database.session import Base
from core.database.models import PublishingJob, WorkerHeartbeat
from brain.operations.publishing_worker import (
    is_valid_transition,
    is_transient_error,
    recover_orphaned_jobs,
    process_job,
    worker_poll_loop,
    update_heartbeat
)
from brain.operations.queue import _PROVIDER_REGISTRY
from apps.api.v1.publishing import create_publishing_job
from contracts.dto.publishing import PublishingJobCreateDTO
import httpx


# 1. State Transition Matrix Tests
def test_state_transitions():
    assert is_valid_transition("QUEUED", "PROCESSING") is True
    assert is_valid_transition("QUEUED", "CANCELLED") is True
    assert is_valid_transition("QUEUED", "SUCCESS") is False
    
    assert is_valid_transition("PROCESSING", "SUCCESS") is True
    assert is_valid_transition("PROCESSING", "RETRYING") is True
    assert is_valid_transition("PROCESSING", "FAILED") is True
    assert is_valid_transition("PROCESSING", "CANCELLED") is True
    assert is_valid_transition("PROCESSING", "QUEUED") is False

    assert is_valid_transition("SUCCESS", "PROCESSING") is False
    assert is_valid_transition("FAILED", "QUEUED") is True
    assert is_valid_transition("CANCELLED", "QUEUED") is True


# 2. Transient Error Classification Tests
def test_transient_error_classification():
    # HTTPX exceptions
    assert is_transient_error(httpx.TimeoutException("timeout")) is True
    assert is_transient_error(httpx.NetworkError("network fail")) is True
    
    # Custom class with status_code
    class CustomHTTPError(Exception):
        def __init__(self, status_code):
            self.status_code = status_code

    assert is_transient_error(CustomHTTPError(500)) is True
    assert is_transient_error(CustomHTTPError(429)) is True
    assert is_transient_error(CustomHTTPError(400)) is False
    assert is_transient_error(CustomHTTPError(403)) is False

    # Status codes in exception strings
    assert is_transient_error(Exception("HTTP status 503 Service Unavailable")) is True
    assert is_transient_error(Exception("Some other standard error")) is False


# 3. Crash Recovery Tests
@pytest.mark.asyncio
async def test_crash_recovery(db):
    job1 = PublishingJob(
        id=uuid.uuid4(),
        content_id="c-1",
        provider="youtube_short",
        status="PROCESSING",
        attempts=1
    )
    job2 = PublishingJob(
        id=uuid.uuid4(),
        content_id="c-2",
        provider="youtube_short",
        status="SUCCESS",
        attempts=1
    )
    db.add(job1)
    db.add(job2)
    db.commit()

    # Recover jobs
    recovered = await recover_orphaned_jobs(db)

    assert recovered == 1
    db.refresh(job1)
    db.refresh(job2)
    assert job1.status == "QUEUED"
    assert job1.started_at is None
    assert job2.status == "SUCCESS"



# 4. Queue Prioritization & Scheduled Timing Tests
def test_queue_fetching_order(db):
    now = datetime.now(UTC).replace(tzinfo=None)
    
    # 1. Standard low priority job
    job_low = PublishingJob(
        id=uuid.uuid4(),
        content_id="low-priority",
        provider="youtube_short",
        status="QUEUED",
        priority=0,
        created_at=now
    )
    # 2. High priority job
    job_high = PublishingJob(
        id=uuid.uuid4(),
        content_id="high-priority",
        provider="youtube_short",
        status="QUEUED",
        priority=10,
        created_at=now + timedelta(seconds=1)
    )
    # 3. Scheduled in future
    job_future = PublishingJob(
        id=uuid.uuid4(),
        content_id="future-scheduled",
        provider="youtube_short",
        status="QUEUED",
        priority=100,
        scheduled_at=now + timedelta(hours=1),
        created_at=now
    )
    # 4. Scheduled in past
    job_past = PublishingJob(
        id=uuid.uuid4(),
        content_id="past-scheduled",
        provider="youtube_short",
        status="QUEUED",
        priority=5,
        scheduled_at=now - timedelta(minutes=5),
        created_at=now
    )

    db.add(job_low)
    db.add(job_high)
    db.add(job_future)
    db.add(job_past)
    db.commit()

    # Query next job
    query = db.query(PublishingJob).filter(
        PublishingJob.status.in_(["QUEUED", "RETRYING"]),
        (PublishingJob.scheduled_at == None) | (PublishingJob.scheduled_at <= now)
    ).order_by(
        PublishingJob.priority.desc(),
        PublishingJob.scheduled_at.asc(),
        PublishingJob.created_at.asc()
    )
    
    # The order should be:
    # 1. job_high (priority=10, scheduled=None)
    # 2. job_past (priority=5, scheduled in past)
    # 3. job_low (priority=0, scheduled=None)
    # job_future is skipped because scheduled_at > now
    jobs = query.all()
    assert len(jobs) == 3
    assert jobs[0].content_id == "high-priority"
    assert jobs[1].content_id == "past-scheduled"
    assert jobs[2].content_id == "low-priority"


# 5. Worker Heartbeat Logging Tests
def test_worker_heartbeat(db):
    worker_id = "test-worker-99"
    update_heartbeat(db, worker_id)

    hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_id == worker_id).first()
    assert hb is not None
    assert hb.worker_id == worker_id
    assert (datetime.now(UTC).replace(tzinfo=None) - hb.last_heartbeat_at).total_seconds() < 5


# 6. REST API Endpoint Operations Tests
def test_api_jobs_crud_operations(client: TestClient):
    # Enqueue a job
    payload = {
        "tenant_id": "tenant-abc",
        "content_id": "episode-101",
        "provider": "youtube_short",
        "priority": 2,
        "payload": {
            "master_reel_path": "/var/test.mp4",
            "caption": "Tamil video!"
        }
    }
    
    res = client.post("/v1/publishing/jobs", json=payload)
    assert res.status_code == 200
    job_data = res.json()
    job_id = job_data["id"]
    assert job_data["status"] == "QUEUED"
    assert job_data["content_id"] == "episode-101"

    # Cancel a queued job (create new queued one first)
    new_job = client.post("/v1/publishing/jobs", json={
        "content_id": "episode-102",
        "provider": "youtube_short",
        "payload": {}
    }).json()
    new_id = new_job["id"]

    cancel_res = client.post(f"/v1/publishing/jobs/{new_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Retry a cancelled job
    retry_res = client.post(f"/v1/publishing/jobs/{new_id}/retry")
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "QUEUED"

    # List jobs filter
    list_res = client.get("/v1/publishing/jobs?status=QUEUED")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Metrics endpoint
    metrics_res = client.get("/v1/publishing/metrics")
    assert metrics_res.status_code == 200
    metrics_data = metrics_res.json()
    assert "jobs_queued" in metrics_data
    assert "current_worker_count" in metrics_data


@pytest.mark.asyncio
async def test_api_idempotency_direct(db):
    payload = PublishingJobCreateDTO(
        tenant_id="tenant-idemp",
        content_id="episode-idemp",
        provider="youtube_short",
        priority=1,
        payload={"master_reel_path": "test.mp4"}
    )
    
    # 1. First direct creation
    job1 = await create_publishing_job(payload, db)
    assert job1.status == "QUEUED"

    # 2. Mutate state to SUCCESS
    job1.status = "SUCCESS"
    db.add(job1)
    db.commit()

    # 3. Second direct creation should trigger idempotency check and return the SUCCESS job
    job2 = await create_publishing_job(payload, db)
    assert job2.id == job1.id
    assert job2.status == "SUCCESS"


# 7. Asynchronous Worker Execution Tests (Mocks)
@pytest.mark.asyncio
async def test_worker_job_processing(db):
    job = PublishingJob(
        id=uuid.uuid4(),
        content_id="content-async-test",
        provider="youtube_short",
        status="QUEUED",
        payload={"master_reel_path": "fake.mp4", "caption": "Test"}
    )
    db.add(job)
    db.commit()

    mock_provider = AsyncMock()
    mock_provider.upload.return_value = {"status": "success", "video_id": "test-vid-888"}

    with patch.dict(_PROVIDER_REGISTRY, {"youtube_short": mock_provider}):
        await process_job(db, job)

    db.refresh(job)
    assert job.status == "SUCCESS"
    assert job.video_id == "test-vid-888"
    assert job.completed_at is not None
    assert job.error_code is None
