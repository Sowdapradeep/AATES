import logging
import time
from typing import Any, List
from providers.registry import BaseProvider, model_registry
from contracts.interfaces.llm import LLMProvider
from core.config.settings import settings

logger = logging.getLogger("bedrock_llm")

class BedrockLLMProvider(BaseProvider, LLMProvider):
    """Production AWS Bedrock LLM Provider using bedrock-runtime Converse API."""

    @property
    def name(self) -> str:
        return "BedrockLLM"

    @property
    def capabilities(self) -> List[str]:
        return ["text_generation", "long_context", "structured_json", "streaming", "tamil_support"]

    def __init__(self) -> None:
        self.bedrock_client = None
        self.cost = 0.0
        self.initialize()

    def initialize(self) -> None:
        if not self.bedrock_client:
            try:
                import boto3
                self.bedrock_client = boto3.client("bedrock-runtime", region_name=settings.ai.bedrock_region)
                logger.info("Bedrock Runtime client initialized successfully.")
            except Exception as e:
                logger.warning(f"Bedrock Runtime initialization skipped or failed: {str(e)}. Fallback to Mock is enabled.")

    async def health_check(self) -> dict[str, Any]:
        try:
            import boto3
            client = boto3.client("bedrock", region_name=settings.ai.bedrock_region)
            client.list_foundation_models()
            return {
                "status": "healthy",
                "reasoning_model": settings.ai.bedrock_reasoning_model,
                "fast_model": settings.ai.bedrock_fast_model,
                "embedding_model": settings.ai.bedrock_embedding_model,
                "image_model": settings.ai.bedrock_image_model
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "reasoning_model": settings.ai.bedrock_reasoning_model,
                "fast_model": settings.ai.bedrock_fast_model,
                "embedding_model": settings.ai.bedrock_embedding_model,
                "image_model": settings.ai.bedrock_image_model
            }

    async def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, **kwargs: Any) -> str:
        return await self.generate(system_prompt, user_prompt, temperature, **kwargs)

    async def embeddings(self, text: str) -> list[float]:
        if not self.bedrock_client:
            self.initialize()
        import asyncio
        loop = asyncio.get_event_loop()
        
        if settings.app.env == "testing":
            return [0.1] * 1536
            
        def call_embed():
            import json
            body = json.dumps({"inputText": text})
            response = self.bedrock_client.invoke_model(
                modelId=settings.ai.bedrock_embedding_model,
                contentType="application/json",
                accept="application/json",
                body=body
            )
            resp_body = json.loads(response.get("body").read())
            return resp_body.get("embedding", [])
            
        return await loop.run_in_executor(None, call_embed)

    def shutdown(self) -> None:
        pass

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, **kwargs: Any) -> str:
        """Invokes Bedrock Converse API with mock fallback if credentials/keys are missing or during tests."""
        # Resolve active model ID for text generation using capability registry
        model_id = kwargs.get("model") or model_registry.select_best_model_for_capability("text_generation")
        if not model_id:
            model_id = settings.ai.bedrock_reasoning_model

        # Check if running in mock/testing env
        if settings.app.env == "testing":
            logger.info(f"Bedrock: Test environment or client offline. Simulating {model_id} LLM response.")
            est_input_tokens = len(system_prompt + user_prompt) // 4
            mock_res = f"[Bedrock {model_id} Mock Response] system_prompt={system_prompt[:30]}... user_prompt={user_prompt[:30]}..."
            est_output_tokens = len(mock_res) // 4
            
            pricing = model_registry.get_pricing(model_id)
            self.cost = (est_input_tokens * pricing["input_cost_per_token"]) + (est_output_tokens * pricing["output_cost_per_token"])
            return mock_res

        # Execute Converse API request
        try:
            payload_messages = [
                {"role": "user", "content": [{"text": user_prompt}]}
            ]
            
            # Format system prompt
            system_config = [{"text": system_prompt}] if system_prompt else []
            
            inference_config = {
                "temperature": temperature,
                "maxTokens": 4000
            }
            
            logger.info(f"Bedrock Converse: Calling model {model_id}...")
            
            # Run blocking call in executor
            import asyncio
            loop = asyncio.get_event_loop()
            
            if not self.bedrock_client:
                self.initialize()

            def call_converse():
                return self.bedrock_client.converse(
                    modelId=model_id,
                    messages=payload_messages,
                    system=system_config,
                    inferenceConfig=inference_config
                )
                
            response = await loop.run_in_executor(None, call_converse)
            
            # Extract content text
            output_message = response.get("output", {}).get("message", {})
            content = output_message.get("content", [])
            output_text = ""
            if content:
                output_text = content[0].get("text", "")
                
            # Token accounting and pricing
            usage = response.get("usage", {})
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)
            
            pricing = model_registry.get_pricing(model_id)
            self.cost = (input_tokens * pricing["input_cost_per_token"]) + (output_tokens * pricing["output_cost_per_token"])
            
            logger.info(f"Bedrock Converse success. Cost: ${self.cost:.5f}")
            return output_text
            
        except Exception as e:
            logger.error(f"Bedrock Converse call failed for model {model_id}: {str(e)}")
            raise e
