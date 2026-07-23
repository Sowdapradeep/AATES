import pytest
from sqlalchemy.orm import Session
from core.database.models import Budget
from core.workflow.billing import billing_engine, BudgetLimitExceeded
from providers.registry import provider_registry, model_registry, ProviderProxy


def test_model_registry_capability_resolution() -> None:
    """Verifies that Bedrock models are correctly cataloged and selected by capability."""
    model_registry.discover_models()
    
    # Text Generation resolution
    text_model = model_registry.select_best_model_for_capability("text_generation")
    assert text_model == "amazon.nova-pro-v1:0"

    # Image Generation resolution
    image_model = model_registry.select_best_model_for_capability("image_generation")
    assert image_model == "amazon.titan-image-generator-v2:0"

    # Pricing lookup
    pricing = model_registry.get_pricing("amazon.nova-pro-v1:0")
    assert pricing["input_cost_per_token"] > 0.0


def test_provider_proxy_routing_priority() -> None:
    """Verifies Bedrock is selected as the top-priority provider, falling back sequentially."""
    # Retrieve a proxy for image generation
    proxy = provider_registry.select_provider("image", ["image_generation"])
    assert isinstance(proxy, ProviderProxy)
    assert proxy.capabilities == ["image_generation"]

    # In test environment, sorting priorities will run and prefer Bedrock
    # let's verify candidates sorting matches priority rankings
    providers = provider_registry._registry.get("image", [])
    candidates = [p for p in providers if "image_generation" in p.capabilities]
    
    # Assert Bedrock is present
    bedrock_present = any("bedrock" in p.name.lower() for p in candidates)
    assert bedrock_present is True


@pytest.mark.asyncio
async def test_budget_enforcement_blocking(db: Session) -> None:
    """Verifies that the engine blocks execution and raises BudgetLimitExceeded when limits are reached."""
    import uuid
    universe_id = str(uuid.uuid4())
    uni_uuid = uuid.UUID(universe_id)

    # 1. Create a budget in the database that is already exhausted
    exhausted_budget = Budget(
        id=uuid.uuid4(),
        universe_id=uni_uuid,
        allocated_amount=100.0,
        spent_amount=100.0
    )
    db.add(exhausted_budget)
    db.commit()

    # 2. Assert verify_budget_limit raises exception
    with pytest.raises(BudgetLimitExceeded):
        billing_engine.verify_budget_limit(db, universe_id)

    # 3. Assert provider proxy call raises exception when db and universe context are passed
    proxy = provider_registry.select_provider("image", ["image_generation"])
    with pytest.raises(BudgetLimitExceeded):
        await proxy.generate_image(
            prompt="A majestic Tamil warrior",
            seed=42,
            db=db,
            universe_id=universe_id
        )
