import logging
import time
from typing import Any, List
import httpx
from providers.registry import BaseProvider
from contracts.interfaces.llm import LLMProvider
from core.config.settings import settings

logger = logging.getLogger("groq_provider")

class GroqLLMProvider(BaseProvider, LLMProvider):
    """Production Groq LLM Provider (OpenAI-compatible) used as a primary fallback option."""

    @property
    def name(self) -> str:
        return "Groq"

    @property
    def capabilities(self) -> List[str]:
        return ["text_generation", "structured_json", "streaming", "tamil_support"]

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.ai.groq_api_key
        # Default rates for llama3-70b
        self.input_rate_per_token = 0.59 / 1_000_000
        self.output_rate_per_token = 0.79 / 1_000_000
        self.initialize()

    def initialize(self) -> None:
        self.api_key = self.api_key or settings.ai.groq_api_key
        if not self.api_key and settings.app.env != "testing":
            logger.warning("Groq API key is not configured.")

    async def health_check(self) -> dict[str, Any]:
        if not settings.ai.groq_enabled:
            return {"status": "unhealthy", "error": "Groq backup is disabled"}
        if settings.app.env == "testing" or self.api_key == "mock":
            return {"status": "healthy"}
        if not self.api_key:
            return {"status": "unhealthy", "error": "Groq API key not configured"}
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            timeout = httpx.Timeout(5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
                res.raise_for_status()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, **kwargs: Any) -> str:
        return await self.generate(system_prompt, user_prompt, temperature, **kwargs)

    async def embeddings(self, text: str) -> list[float]:
        raise NotImplementedError("Embeddings capability is not supported on Groq provider.")

    def shutdown(self) -> None:
        pass

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, **kwargs: Any) -> str:
        """Invokes chat completions from Groq cloud API with mock fallback."""
        if settings.app.env == "testing" or self.api_key == "mock" or not self.api_key:
            logger.info("Groq in testing mode or key set to mock. Returning Mock Groq response.")
            est_input_tokens = len(system_prompt + user_prompt) // 4
            mock_res = f"[Groq Mock Response] system_prompt={system_prompt[:30]}... user_prompt={user_prompt[:30]}..."
            est_output_tokens = len(mock_res) // 4
            
            self.cost = (est_input_tokens * self.input_rate_per_token) + (est_output_tokens * self.output_rate_per_token)
            return mock_res

        # Live Groq API Call
        model = kwargs.get("model", "llama3-70b-8192")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }
        
        if kwargs.get("response_format") == "json_object":
            payload["response_format"] = {"type": "json_object"}

        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            retries = 3
            for attempt in range(retries):
                try:
                    response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Token accounting
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    
                    self.cost = (prompt_tokens * self.input_rate_per_token) + (completion_tokens * self.output_rate_per_token)
                    logger.info(f"Groq API call success. Cost: ${self.cost:.6f}")
                    
                    return data["choices"][0]["message"]["content"]
                except Exception as e:
                    if attempt == retries - 1:
                        raise e
                    logger.warning(f"Groq call failed (attempt {attempt + 1}/{retries}): {str(e)}. Retrying...")
                    time.sleep(2 ** attempt)
                    
        raise RuntimeError("Groq call exhausted retries without returning a response.")
