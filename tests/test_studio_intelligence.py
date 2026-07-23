import pytest
from fastapi.testclient import TestClient
from brain.production.review import MultiAgentReviewPipeline, AssetReuseEngine, PromptOptimizationEngine


def test_multi_agent_critics_and_revision_loop() -> None:
    """Verifies that the critics review panel calculates scores and runs automatic revisions."""
    # Score below threshold (e.g. threshold = 90.0)
    pipeline = MultiAgentReviewPipeline(threshold=90.0)
    
    import asyncio
    res = asyncio.run(pipeline.evaluate_scene("scene_1", {}))
    
    assert res["passed"] is True
    # The score was boosted to 85.0 after dialogue revision loop triggered
    assert res["overall_score"] == 85.0
    assert len(pipeline.revision_history) == 1
    assert pipeline.revision_history[0]["regenerated_components"] == ["dialogue"]


def test_asset_reuse_engine() -> None:
    """Verifies that identical prompts retrieve registered files from the reuse registry."""
    engine = AssetReuseEngine()
    prompt = "A majestic view of Tirunelveli temple"
    category = "image"
    s3_path = "s3://aates-assets-345307375520/stills/temple.png"
    
    # Not registered yet
    assert engine.find_reusable_asset(prompt, category) is None
    
    # Register and retrieve
    engine.register_asset(prompt, category, s3_path)
    assert engine.find_reusable_asset(prompt, category) == s3_path


def test_prompt_optimization_engine() -> None:
    """Verifies that stylistic quality qualifiers are recommended for low scoring prompt versions."""
    engine = PromptOptimizationEngine()
    prompt_id = "prompt_scene_1"
    original = "Indha mannum, indha makkalum"
    
    # Score high -> no change
    engine.log_prompt_run(prompt_id, "v1.0", 90.0)
    assert engine.recommend_optimized_prompt(prompt_id, original) == original
    
    # Score drops below 80 -> optimized
    engine.log_prompt_run(prompt_id, "v1.1", 72.0)
    optimized = engine.recommend_optimized_prompt(prompt_id, original)
    assert "8k, cinematic lighting" in optimized


def test_quality_validation_api_endpoint(client: TestClient) -> None:
    """Verifies that the new quality validation route reports metrics correctly."""
    res = client.get("/v1/validation/quality")
    assert res.status_code == 200
    assert res.json()["overall_quality_threshold"] == 80.0
    assert "prompt_versions" in res.json()
    assert "model_usage_distribution" in res.json()


def test_model_router_capability_routing() -> None:
    """Verifies that the model router selects correct models per capability."""
    from brain.production.model_router import ModelRouter
    router = ModelRouter()

    # Dialogue -> should pick a text model
    model = router.route(capability="dialogue", quality_tier="premium")
    assert "claude" in model or "titan" in model

    # Image -> should pick titan image model
    model = router.route(capability="image")
    assert "titan" in model or "image" in model


def test_model_router_economy_preference() -> None:
    """Verifies economy routing selects the cheapest eligible model."""
    from brain.production.model_router import ModelRouter
    router = ModelRouter()
    model = router.route(capability="dialogue", prefer_economy=True)
    # Economy routing should not select the premium claude-3-5-sonnet
    assert model != "anthropic.claude-3-sonnet-20240229-v1:0"


def test_model_router_usage_tracking() -> None:
    """Verifies that model routing records usage counters for analytics."""
    from brain.production.model_router import ModelRouter, _usage_counters
    router = ModelRouter()
    before = dict(_usage_counters)
    router.route(capability="story", quality_tier="standard")
    # At least one model should have incremented
    assert sum(_usage_counters.values()) > sum(before.values())


def test_dashboard_quality_endpoint(client: TestClient) -> None:
    """Verifies the quality dashboard route returns critics panel and scores."""
    res = client.get("/v1/operations/dashboard/quality")
    assert res.status_code == 200
    data = res.json()
    assert "critics" in data
    assert len(data["critics"]) == 7
    assert data["passed"] is True
    assert "revision_history" in data


def test_dashboard_cost_endpoint(client: TestClient) -> None:
    """Verifies the cost analytics dashboard route returns budget details."""
    res = client.get("/v1/operations/dashboard/cost")
    assert res.status_code == 200
    data = res.json()
    assert "total_estimated_cost_usd" in data
    assert "asset_reuse_savings_usd" in data
    assert "total_budget_usd" in data


def test_dashboard_prompts_endpoint(client: TestClient) -> None:
    """Verifies the prompt version dashboard route returns tracked prompt data."""
    res = client.get("/v1/operations/dashboard/prompts")
    assert res.status_code == 200
    data = res.json()
    assert "tracked_prompts" in data
    assert len(data["tracked_prompts"]) >= 1
    assert data["tracked_prompts"][0]["optimized"] is True


def test_analytics_feedback_to_ceo(client: TestClient) -> None:
    """Verifies that quality feedback is ingested by the CEO agent and returns adjustments."""
    payload = {
        "overall_score": 72.0,
        "revision_count": 3,
        "episode_id": "ep-001",
    }
    res = client.post("/v1/operations/dashboard/feedback", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "feedback_ingested"
    # Score was below 80, so adjustment should be recommended
    assert len(data["adjustments_applied"]) >= 1


def test_ceo_agent_quality_feedback_loop() -> None:
    """Verifies the CEO agent accumulates feedback and returns summaries."""
    import asyncio
    from brain.ceo.agent import CEOAgent
    ceo = CEOAgent()

    asyncio.run(ceo.ingest_quality_feedback({"overall_score": 85.0, "revision_count": 1}))
    asyncio.run(ceo.ingest_quality_feedback({"overall_score": 92.0, "revision_count": 0}))

    summary = ceo.get_quality_feedback_summary()
    assert summary["total_records"] == 2
    assert summary["avg_score"] == 88.5

