import logging
import time
from typing import Any, List
import httpx
from providers.registry import BaseProvider
from contracts.interfaces.llm import LLMProvider
from core.config.settings import settings

logger = logging.getLogger("openai_provider")

class OpenAIProvider(BaseProvider, LLMProvider):
    """Production OpenAI LLM Provider supporting structured outputs, token accounting, and cost tracking."""

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def capabilities(self) -> List[str]:
        return ["structured_json", "streaming", "chat", "tamil_support"]

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.ai.openai_api_key
        # Fallback rates for token accounting (gpt-4o-mini rates by default)
        self.input_rate_per_token = 0.150 / 1_000_000
        self.output_rate_per_token = 0.600 / 1_000_000

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, **kwargs: Any) -> str:
        """Invokes chat completion from OpenAI API with mock fallback if credentials are missing."""
        if settings.app.env == "testing" or self.api_key == "mock":
            logger.info("OpenAI in testing mode or key set to mock. Returning Mock LLM response.")
            # Calculate mock cost
            est_input_tokens = len(system_prompt + user_prompt) // 4
            mock_response = f"[OpenAI Mock Response] system_prompt={system_prompt[:30]}... user_prompt={user_prompt[:30]}..."
            est_output_tokens = len(mock_response) // 4
            self.cost = (est_input_tokens * self.input_rate_per_token) + (est_output_tokens * self.output_rate_per_token)
            return mock_response

        # Live API Call
        model = kwargs.get("model", "gpt-4o-mini")
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
        
        # Check if structured output is requested
        if kwargs.get("response_format") == "json_object":
            payload["response_format"] = {"type": "json_object"}

        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            retries = 3
            for attempt in range(retries):
                try:
                    response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Token Accounting
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    
                    # Cost Tracking
                    model_key = model.lower()
                    if "gpt-4o" in model_key and "mini" not in model_key:
                        self.input_rate_per_token = 5.00 / 1_000_000
                        self.output_rate_per_token = 15.00 / 1_000_000
                    else:
                        self.input_rate_per_token = 0.150 / 1_000_000
                        self.output_rate_per_token = 0.600 / 1_000_000
                        
                    self.cost = (prompt_tokens * self.input_rate_per_token) + (completion_tokens * self.output_rate_per_token)
                    
                    return data["choices"][0]["message"]["content"]
                except Exception as e:
                    if attempt == retries - 1:
                        raise e
                    logger.warning(f"OpenAI call failed (attempt {attempt + 1}/{retries}): {str(e)}. Retrying...")
                    time.sleep(2 ** attempt)
        
        raise RuntimeError("OpenAI call exhausted retries without returning a response.")
