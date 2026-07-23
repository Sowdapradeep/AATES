import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from core.config.settings import settings
from providers.registry import provider_registry, model_registry
from providers.llm.bedrock_llm import BedrockLLMProvider
from providers.llm.gemini_provider import GeminiProvider
from providers.llm.groq_provider import GroqLLMProvider


def test_provider_registry_registrations() -> None:
    """Verifies Bedrock, Gemini, and Groq LLM providers are registered."""
    provider_registry._ensure_default_providers()
    bedrock = provider_registry.get_provider("llm", "BedrockLLM")
    gemini = provider_registry.get_provider("llm", "Gemini")
    groq = provider_registry.get_provider("llm", "Groq")
    
    assert isinstance(bedrock, BedrockLLMProvider)
    assert isinstance(gemini, GeminiProvider)
    assert isinstance(groq, GroqLLMProvider)


def test_model_registry_nova_registrations() -> None:
    """Verifies Nova and Titan models are registered in ModelRegistry."""
    model_registry.discover_models()
    assert "amazon.nova-pro-v1:0" in model_registry._models
    assert "amazon.nova-lite-v1:0" in model_registry._models
    assert "amazon.titan-embed-text-v2" in model_registry._models
    assert "amazon.titan-image-generator-v2:0" in model_registry._models


def test_provider_initialization_and_shutdown() -> None:
    """Verifies standardize methods initialize, shutdown, health_check exist."""
    bedrock = BedrockLLMProvider()
    gemini = GeminiProvider(api_key="mock")
    groq = GroqLLMProvider(api_key="mock")
    
    bedrock.initialize()
    gemini.initialize()
    groq.initialize()
    
    bedrock.shutdown()
    gemini.shutdown()
    groq.shutdown()
    
    assert bedrock.name == "BedrockLLM"
    assert gemini.name == "Gemini"
    assert groq.name == "Groq"


@pytest.mark.asyncio
async def test_titan_embeddings_generation() -> None:
    """Verifies Titan embeddings generation routing."""
    bedrock = BedrockLLMProvider()
    emb = await bedrock.embeddings("Hello AATES")
    assert len(emb) == 1536
    assert emb[0] == 0.1


@pytest.mark.asyncio
async def test_bedrock_to_gemini_failover() -> None:
    """Verifies that Bedrock failures fall back to Gemini."""
    # Reset/ensure failover setting is true
    settings.ai.allow_external_failover = True
    settings.ai.gemini_enabled = True
    
    # Mock Bedrock generate to fail, but let Gemini generate succeed
    with patch("providers.llm.bedrock_llm.BedrockLLMProvider.generate", side_effect=RuntimeError("Bedrock connection timeout")), \
         patch("providers.llm.gemini_provider.GeminiProvider.generate", return_value="[Gemini Mock Response] success"):
         
        proxy = provider_registry.select_provider("llm", required_capabilities=["text_generation"])
        res = await proxy.generate(system_prompt="sys", user_prompt="usr", capability="story")
        assert "Gemini Mock Response" in res


@pytest.mark.asyncio
async def test_gemini_to_groq_failover() -> None:
    """Verifies that Bedrock and Gemini failures fall back to Groq."""
    settings.ai.allow_external_failover = True
    settings.ai.gemini_enabled = True
    settings.ai.groq_enabled = True
    
    with patch("providers.llm.bedrock_llm.BedrockLLMProvider.generate", side_effect=RuntimeError("Bedrock error")), \
         patch("providers.llm.gemini_provider.GeminiProvider.generate", side_effect=RuntimeError("Gemini error")), \
         patch("providers.llm.groq_provider.GroqLLMProvider.generate", return_value="[Groq Mock Response] success"):
         
        proxy = provider_registry.select_provider("llm", required_capabilities=["text_generation"])
        res = await proxy.generate(system_prompt="sys", user_prompt="usr", capability="story")
        assert "Groq Mock Response" in res


@pytest.mark.asyncio
async def test_all_providers_unavailable() -> None:
    """Verifies error handling when all LLM providers fail."""
    settings.ai.allow_external_failover = True
    
    with patch("providers.llm.bedrock_llm.BedrockLLMProvider.generate", side_effect=RuntimeError("Bedrock error")), \
         patch("providers.llm.gemini_provider.GeminiProvider.generate", side_effect=RuntimeError("Gemini error")), \
         patch("providers.llm.groq_provider.GroqLLMProvider.generate", side_effect=RuntimeError("Groq error")):
         
        proxy = provider_registry.select_provider("llm", required_capabilities=["text_generation"])
        with pytest.raises(RuntimeError) as exc_info:
            await proxy.generate(system_prompt="sys", user_prompt="usr", capability="story")
        assert "All matching providers" in str(exc_info.value)


@pytest.mark.asyncio
async def test_failover_disabled() -> None:
    """Verifies that external failover is blocked when allow_external_failover is false."""
    settings.ai.allow_external_failover = False
    
    with patch("providers.llm.bedrock_llm.BedrockLLMProvider.generate", side_effect=RuntimeError("Bedrock error")), \
         patch("providers.llm.gemini_provider.GeminiProvider.generate", return_value="Gemini response"):
         
        proxy = provider_registry.select_provider("llm", required_capabilities=["text_generation"])
        with pytest.raises(RuntimeError) as exc_info:
            await proxy.generate(system_prompt="sys", user_prompt="usr", capability="story")
        assert "External failover is disabled" in str(exc_info.value)


def test_health_endpoint_schema(client: TestClient) -> None:
    """Verifies that the /health endpoint returns the exact required JSON schema."""
    settings.ai.allow_external_failover = True
    settings.ai.provider = "bedrock"
    
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "bedrock" in data
    assert "gemini" in data
    assert "groq" in data
    assert data["bedrock"]["reasoning_model"] == "amazon.nova-pro-v1:0"
    assert data["bedrock"]["fast_model"] == "amazon.nova-lite-v1:0"
    assert data["primary_provider"] == "bedrock"
    assert data["active_provider"] == "bedrock"
    assert data["failover_enabled"] is True
