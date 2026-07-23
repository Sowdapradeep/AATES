import logging
import time
from typing import Any, List
import httpx
from providers.registry import BaseProvider
from contracts.interfaces.llm import LLMProvider
from core.config.settings import settings

logger = logging.getLogger("gemini_provider")

class GeminiProvider(BaseProvider, LLMProvider):
    """Production Gemini LLM Provider supporting structured outputs, token accounting, and cost tracking."""

    @property
    def name(self) -> str:
        return "Gemini"

    @property
    def capabilities(self) -> List[str]:
        return ["structured_json", "streaming", "chat", "tamil_support"]

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.ai.gemini_api_key
        # Default rates for gemini-1.5-flash
        self.input_rate_per_token = 0.075 / 1_000_000
        self.output_rate_per_token = 0.300 / 1_000_000
        self.initialize()

    def initialize(self) -> None:
        self.api_key = self.api_key or settings.ai.gemini_api_key
        if not self.api_key and settings.app.env != "testing":
            logger.warning("Gemini API key is not configured.")

    async def health_check(self) -> dict[str, Any]:
        if not settings.ai.gemini_enabled:
            return {"status": "unhealthy", "error": "Gemini backup is disabled"}
        if settings.app.env == "testing" or self.api_key == "mock":
            return {"status": "healthy"}
        if not self.api_key:
            return {"status": "unhealthy", "error": "Gemini API key not configured"}
        try:
            model = settings.ai.gemini_model or "gemini-2.5-pro"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": "ping"}]}]
            }
            timeout = httpx.Timeout(5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, **kwargs: Any) -> str:
        return await self.generate(system_prompt, user_prompt, temperature, **kwargs)

    async def embeddings(self, text: str) -> list[float]:
        raise NotImplementedError("Embeddings capability is not supported on Gemini provider.")

    def shutdown(self) -> None:
        pass

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, **kwargs: Any) -> str:
        """Invokes generation from Gemini API with mock fallback if credentials are missing."""
        if settings.app.env == "testing" or self.api_key == "mock" or not self.api_key:
            logger.info("Gemini in testing mode or key set to mock. Returning Mock LLM response.")
            est_input_tokens = len(system_prompt + user_prompt) // 4
            mock_response = f"[Gemini Mock Response] system_prompt={system_prompt[:30]}... user_prompt={user_prompt[:30]}..."
            est_output_tokens = len(mock_response) // 4
            self.cost = (est_input_tokens * self.input_rate_per_token) + (est_output_tokens * self.output_rate_per_token)
            return mock_response

        # Live Gemini API call
        model = kwargs.get("model") or settings.ai.gemini_model or "gemini-2.5-pro"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        # Check structured JSON output request
        if kwargs.get("response_format") == "json_object":
            payload["generationConfig"]["responseMimeType"] = "application/json"

        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            retries = 3
            for attempt in range(retries):
                try:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Token Accounting & Cost Estimation
                    usage = data.get("usageMetadata", {})
                    prompt_tokens = usage.get("promptTokenCount", 0)
                    candidates_tokens = usage.get("candidatesTokenCount", 0)
                    
                    model_key = model.lower()
                    if "pro" in model_key:
                        self.input_rate_per_token = 3.50 / 1_000_000
                        self.output_rate_per_token = 10.50 / 1_000_000
                    else:
                        self.input_rate_per_token = 0.075 / 1_000_000
                        self.output_rate_per_token = 0.300 / 1_000_000
                        
                    self.cost = (prompt_tokens * self.input_rate_per_token) + (candidates_tokens * self.output_rate_per_token)
                    
                    # Retrieve output content
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    raise ValueError("No text candidates returned from Gemini.")
                except Exception as e:
                    if attempt == retries - 1:
                        raise e
                    logger.warning(f"Gemini call failed (attempt {attempt + 1}/{retries}): {str(e)}. Retrying...")
                    time.sleep(2 ** attempt)
                    
        raise RuntimeError("Gemini call exhausted retries without returning a response.")
