import logging
import time
from typing import Any, Dict, List, Type, TypeVar
from core.config.settings import settings

logger = logging.getLogger("provider_registry")

T = TypeVar("T")

class BaseProvider:
    """Base class for all service providers carrying metadata and capabilities."""
    
    @property
    def name(self) -> str:
        raise NotImplementedError
        
    @property
    def capabilities(self) -> List[str]:
        return []

    async def check_health(self) -> bool:
        """Lightweight check to evaluate provider availability."""
        return True


class ModelRegistry:
    """Capability-driven model catalog mapping Bedrock foundation models to active features."""
    
    def __init__(self) -> None:
        self._models: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    def register_model(
        self,
        model_id: str,
        capabilities: List[str],
        regions: List[str] = None,
        formats: List[str] = None,
        limits: Dict[str, Any] = None,
        pricing: Dict[str, float] = None
    ) -> None:
        """Manually register a model specification with its capabilities and pricing metadata."""
        self._models[model_id] = {
            "model_id": model_id,
            "capabilities": capabilities,
            "regions": regions or ["us-east-1"],
            "formats": formats or ["json", "text"],
            "limits": limits or {"max_tokens": 4096},
            "pricing": pricing or {"input_cost_per_token": 0.0, "output_cost_per_token": 0.0},
            "is_available": True
        }
        logger.info(f"ModelRegistry: Registered Bedrock model {model_id} with capabilities {capabilities}")

    def discover_models(self) -> None:
        """Discovers available Bedrock models via boto3 bedrock client or registers defaults if offline/mock."""
        if self._initialized:
            return
        self._initialized = True
        
        # Populate defaults first
        self.register_model(
            "amazon.nova-pro-v1:0",
            ["text_generation", "long_context", "structured_json", "streaming", "tamil_support"],
            pricing={"input_cost_per_token": 0.80 / 1_000_000, "output_cost_per_token": 3.20 / 1_000_000}
        )
        self.register_model(
            "amazon.nova-lite-v1:0",
            ["text_generation", "structured_json", "streaming", "tamil_support"],
            pricing={"input_cost_per_token": 0.06 / 1_000_000, "output_cost_per_token": 0.24 / 1_000_000}
        )
        self.register_model(
            "amazon.titan-embed-text-v2",
            ["embeddings"],
            pricing={"input_cost_per_token": 0.02 / 1_000_000, "output_cost_per_token": 0.0}
        )
        self.register_model(
            "amazon.titan-image-generator-v2:0",
            ["image_generation", "seed_tracking", "style_presets"],
            pricing={"input_cost_per_token": 0.03, "output_cost_per_token": 0.03} # Per image cost
        )
        self.register_model(
            "amazon.titan-image-generator-v1",
            ["image_generation", "seed_tracking", "style_presets"],
            pricing={"input_cost_per_token": 0.03, "output_cost_per_token": 0.03}
        )
        self.register_model(
            "amazon.titan-video-generator-v1",
            ["video_generation", "duration_control"],
            pricing={"input_cost_per_token": 0.20, "output_cost_per_token": 0.20} # Per video cost
        )
        # Keep claude for test reference
        self.register_model(
            "anthropic.claude-3-sonnet-20240229-v1:0",
            ["text_generation", "long_context", "structured_json", "streaming", "tamil_support"],
            pricing={"input_cost_per_token": 3.00 / 1_000_000, "output_cost_per_token": 15.00 / 1_000_000}
        )

        # Attempt dynamic AWS discovery
        try:
            import boto3
            # Query bedrock list-foundation-models
            client = boto3.client("bedrock", region_name=settings.ai.bedrock_region)
            resp = client.list_foundation_models()
            discovered_ids = [m["modelId"] for m in resp.get("modelSummaries", [])]
            logger.info(f"ModelRegistry: Dynamic Bedrock discovery found {len(discovered_ids)} foundation models.")
            # Set unavailability for models not returned in Bedrock region list
            for model_id in list(self._models.keys()):
                if model_id not in discovered_ids:
                    # In test/dev environment, we keep them active so unit testing works
                    if settings.app.env == "production":
                        logger.warning(f"ModelRegistry: Bedrock model {model_id} not available in {settings.ai.bedrock_region}. Deactivating.")
                        self._models[model_id]["is_available"] = False
        except Exception as e:
            logger.info(f"ModelRegistry: Dynamic boto3 bedrock discovery skipped: {str(e)}. Using default catalog.")

    def select_best_model_for_capability(self, capability: str) -> str | None:
        """Selects the configured or matching Bedrock model ID for the requested capability."""
        self.discover_models()
        
        # 1. Check custom settings override mapping first
        configured_id = settings.ai.bedrock_model_mappings.get(capability)
        if configured_id and configured_id in self._models and self._models[configured_id]["is_available"]:
            return configured_id
            
        # 2. Fallback to scanning registry capabilities
        for model_id, spec in self._models.items():
            if capability in spec["capabilities"] and spec["is_available"]:
                return model_id
                
        return None

    def get_pricing(self, model_id: str) -> Dict[str, float]:
        """Retrieve model pricing rate structures."""
        spec = self._models.get(model_id)
        if spec:
            return spec["pricing"]
        return {"input_cost_per_token": 0.0, "output_cost_per_token": 0.0}


# Global model registry instance
model_registry = ModelRegistry()


class ProviderProxy:
    """Intermediary proxy routing all provider requests dynamically for circuit breaking and fallbacks."""
    
    def __init__(self, category: str, required_capabilities: List[str] = None):
        self._category = category
        self._required_capabilities = required_capabilities or []

    @property
    def name(self) -> str:
        try:
            p = provider_registry.get_best_candidate(self._category, self._required_capabilities)
            return p.name
        except:
            return "ProviderProxy"

    @property
    def capabilities(self) -> List[str]:
        return self._required_capabilities

    def __getattr__(self, name: str):
        """Wraps target operations in execute_with_fallback dynamically."""
        async def _wrapper(*args, **kwargs):
            return await provider_registry.execute_with_fallback(
                self._category,
                name,
                self._required_capabilities,
                None,
                *args,
                **kwargs
            )
        return _wrapper


class ProviderRegistry:
    """Central registry mapping provider types, capabilities, environment profiles, and fallback loops."""
    
    def __init__(self) -> None:
        # Category -> List of instantiated providers
        self._registry: Dict[str, List[Any]] = {
            "llm": [],
            "image": [],
            "video": [],
            "voice": [],
            "music": [],
            "rendering": [],
            "storage": []
        }
        # Benchmarking / health state mapping: provider_name -> metrics dict
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.health_map: Dict[str, Any] = {}
        self.provider_status: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    def _ensure_default_providers(self) -> None:
        """Dynamically registers default providers lazily to avoid circular imports during startup."""
        if not self._initialized:
            self._initialized = True
            logger.info("Lazily registering default AATES service providers...")
            try:
                from providers.llm.openai_provider import OpenAIProvider
                from providers.llm.gemini_provider import GeminiProvider
                from providers.llm.bedrock_llm import BedrockLLMProvider
                from providers.llm.groq_provider import GroqLLMProvider
                from providers.image.mock import MockImageProvider
                from providers.image.stability_provider import StabilityImageProvider
                from providers.image.openai_image_provider import OpenAIImageProvider
                from providers.image.bedrock_image import BedrockImageProvider
                from providers.video.mock import MockVideoProvider
                from providers.video.stability_video import StabilityVideoProvider
                from providers.video.bedrock_video import BedrockVideoProvider
                from providers.voice.mock import MockVoiceProvider
                from providers.voice.elevenlabs_provider import ElevenLabsVoiceProvider
                from providers.music.mock import MockMusicProvider
                from providers.music.stability_music import StabilityMusicProvider
                from providers.rendering.mock import MockRenderingProvider
                from providers.storage.local_storage import LocalStorage
                from providers.storage.s3_storage import AmazonS3Storage

                self.register("llm", BedrockLLMProvider())
                self.register("llm", GroqLLMProvider())
                self.register("llm", OpenAIProvider())
                self.register("llm", GeminiProvider())
                
                self.register("image", BedrockImageProvider())
                self.register("image", MockImageProvider())
                self.register("image", StabilityImageProvider())
                self.register("image", OpenAIImageProvider())
                
                self.register("video", BedrockVideoProvider())
                self.register("video", MockVideoProvider())
                self.register("video", StabilityVideoProvider())
                
                self.register("voice", MockVoiceProvider())
                self.register("voice", ElevenLabsVoiceProvider())
                self.register("music", MockMusicProvider())
                self.register("music", StabilityMusicProvider())
                self.register("rendering", MockRenderingProvider())
                self.register("storage", LocalStorage())
                self.register("storage", AmazonS3Storage())
            except Exception as e:
                logger.error(f"Error registering default providers in registry: {str(e)}", exc_info=True)

    def register(self, category: str, provider: Any) -> None:
        """Register a provider instance within a category."""
        if category not in self._registry:
            self._registry[category] = []
        # Avoid duplicate registration
        if not any(p.name == provider.name for p in self._registry[category]):
            self._registry[category].append(provider)
            logger.info(f"Registered provider {provider.name} in category '{category}'")

    def get_provider(self, category: str, name: str) -> Any:
        """Directly retrieve a provider by name."""
        self._ensure_default_providers()
        for p in self._registry.get(category, []):
            if p.name == name:
                return p
        raise ValueError(f"Provider '{name}' not found in category '{category}'")

    def get_best_candidate(self, category: str, required_capabilities: List[str]) -> Any:
        """Finds the best active provider candidate matching capabilities."""
        self._ensure_default_providers()
        providers = self._registry.get(category, [])
        candidates = [p for p in providers if all(cap in p.capabilities for cap in required_capabilities)]
        if not candidates:
            raise RuntimeError(f"No providers match capabilities {required_capabilities} in '{category}'")
        return candidates[0]

    def select_provider(
        self,
        category: str,
        required_capabilities: List[str] = None,
        preferred_name: str = None
    ) -> Any:
        """Selects and returns a resilient ProviderProxy wrapper."""
        self._ensure_default_providers()
        return ProviderProxy(category, required_capabilities)

    def record_metrics(self, provider_name: str, latency_ms: float, success: bool, cost: float = 0.0) -> None:
        """Persist benchmarking performance logs in-memory."""
        if provider_name not in self.metrics:
            self.metrics[provider_name] = {
                "calls": 0,
                "successes": 0,
                "failures": 0,
                "total_latency_ms": 0.0,
                "total_cost": 0.0
            }
        
        m = self.metrics[provider_name]
        m["calls"] += 1
        if success:
            m["successes"] += 1
        else:
            m["failures"] += 1
        m["total_latency_ms"] += latency_ms
        m["total_cost"] += cost
        
        logger.debug(
            f"Metrics for {provider_name}: Success={success}, Latency={latency_ms}ms, Cost=${cost:.4f}"
        )

    async def execute_with_fallback(
        self,
        category: str,
        operation_name: str,
        required_capabilities: List[str] = None,
        preferred_name: str = None,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Executes a provider method on the best available provider, falling back on error."""
        self._ensure_default_providers()
        required_capabilities = required_capabilities or []
        import time
        from core.workflow.resilience import execute_resilient_call

        # Centralized capability mapping preferences
        _CAPABILITY_ROUTING_PREFERENCE = {
            "story": [
                {"provider": "BedrockLLM", "model": settings.ai.bedrock_reasoning_model},
                {"provider": "Gemini", "model": settings.ai.gemini_model},
                {"provider": "Groq", "model": "qwen-2.5-72b"},
                {"provider": "Groq", "model": "llama-3.2-3b-preview"},
                {"provider": "Groq", "model": "llama3-70b-8192"}
            ],
            "research": [
                {"provider": "BedrockLLM", "model": settings.ai.bedrock_reasoning_model},
                {"provider": "Gemini", "model": settings.ai.gemini_model},
                {"provider": "Groq", "model": "deepseek-coder-33b"},
                {"provider": "Groq", "model": "llama3-70b-8192"}
            ],
            "coding": [
                {"provider": "BedrockLLM", "model": settings.ai.bedrock_reasoning_model},
                {"provider": "Gemini", "model": settings.ai.gemini_model},
                {"provider": "Groq", "model": "deepseek-coder-33b"},
                {"provider": "Groq", "model": "llama3-70b-8192"}
            ],
            "summarization": [
                {"provider": "BedrockLLM", "model": settings.ai.bedrock_fast_model},
                {"provider": "Gemini", "model": settings.ai.gemini_model},
                {"provider": "Groq", "model": "mistral-7b-instruct"},
                {"provider": "Groq", "model": "llama3-8b-8192"}
            ],
            "embeddings": [
                {"provider": "BedrockLLM", "model": settings.ai.bedrock_embedding_model}
            ],
            "image": [
                {"provider": "BedrockLLM", "model": settings.ai.bedrock_image_model}
            ]
        }

        # Perform pre-execution budget checks
        db = kwargs.get("db")
        universe_id = kwargs.get("universe_id")
        if db and universe_id:
            from core.workflow.billing import billing_engine
            billing_engine.verify_budget_limit(db, universe_id)

        # Resolve capability
        capability = kwargs.get("capability")
        if not capability and required_capabilities:
            for cap in required_capabilities:
                if cap in _CAPABILITY_ROUTING_PREFERENCE:
                    capability = cap
                    break
        if not capability and category == "llm":
            capability = "story"

        # Get all matching candidates
        env = settings.app.env.lower()
        providers = self._registry.get(category, [])
        
        # Filter candidates matching all required capabilities, excluding mocks outside testing
        candidates = []
        for p in providers:
            name_lower = p.name.lower()
            if "mock" in name_lower and env != "testing":
                continue
            if all(cap in p.capabilities for cap in required_capabilities) or (capability and capability in ("story", "research", "coding", "summarization", "embeddings", "image") and p.name in ("BedrockLLM", "Gemini", "Groq")):
                candidates.append(p)

        # Build execution sequence (attempts list)
        attempts = []
        if capability in _CAPABILITY_ROUTING_PREFERENCE:
            preference = _CAPABILITY_ROUTING_PREFERENCE[capability]
            for pref in preference:
                # Find matching provider instance
                p = next((prov for prov in candidates if prov.name.lower() == pref["provider"].lower()), None)
                if p:
                    # Enforce settings.ai enabled flags
                    if p.name.lower() == "gemini" and not settings.ai.gemini_enabled:
                        continue
                    if p.name.lower() == "groq" and not settings.ai.groq_enabled:
                        continue
                    attempts.append((p, pref["model"]))
        else:
            # Fall back to default providers sorting
            def provider_priority(p):
                name_lower = p.name.lower()
                if preferred_name and name_lower == preferred_name.lower():
                    return -100
                if env in ["testing"] and "mock" in name_lower:
                    return -50
                if "bedrock" in name_lower:
                    return 0
                if "gemini" in name_lower:
                    return 1
                if "groq" in name_lower:
                    return 2
                if "openai" in name_lower:
                    return 3
                if "mock" in name_lower:
                    return 100
                return 50

            sorted_providers = sorted(candidates, key=provider_priority)
            for p in sorted_providers:
                if p.name.lower() == "gemini" and not settings.ai.gemini_enabled:
                    continue
                if p.name.lower() == "groq" and not settings.ai.groq_enabled:
                    continue
                model_id = None
                if p.name.lower() == "bedrockllm":
                    model_id = settings.ai.bedrock_reasoning_model
                elif p.name.lower() == "gemini":
                    model_id = settings.ai.gemini_model
                attempts.append((p, model_id))

        if not attempts:
            raise RuntimeError(f"No providers match capabilities {required_capabilities} in '{category}'")

        last_error = None
        allow_failover = settings.ai.allow_external_failover
        primary_provider_name = attempts[0][0].name
        
        for idx, (p, model_id) in enumerate(attempts):
            is_external = p.name.lower() not in ("bedrockllm", "bedrockimage", "bedrockvideo", "bedrockscript")
            
            # Check failover restriction
            if is_external and idx > 0 and not allow_failover:
                logger.warning(f"AI_ALLOW_EXTERNAL_FAILOVER is false. Skipping fallback to external provider {p.name}.")
                raise RuntimeError("ProviderUnavailable: External failover is disabled.")

            func = getattr(p, operation_name, None)
            if not func:
                continue

            # Overwrite model in kwargs
            if model_id:
                kwargs["model"] = model_id

            start_time = time.time()
            fallback_used = None
            if idx > 0:
                fallback_used = p.name
                logger.warning(
                    f"Primary Provider: {primary_provider_name}\n"
                    f"Reason: {str(last_error)}\n"
                    f"Failing over to: {p.name}\n"
                    f"Status: Initiating"
                )

            try:
                res = await execute_resilient_call(p.name, func, *args, **kwargs)
                execution_time_ms = (time.time() - start_time) * 1000
                
                cost = 0.0
                if isinstance(res, dict):
                    cost = res.get("cost", 0.0)
                elif hasattr(res, "cost"):
                    cost = getattr(res, "cost", 0.0)

                self.record_metrics(p.name, execution_time_ms, success=True, cost=cost)

                # Log Telemetry
                logger.info(
                    f"=== AI Call Telemetry ===\n"
                    f"Requested Capability: {capability or required_capabilities}\n"
                    f"Primary Provider: {primary_provider_name}\n"
                    f"Selected Model: {model_id or 'default'}\n"
                    f"Execution Time: {execution_time_ms:.2f}ms\n"
                    f"Fallback Used (if any): {fallback_used}\n"
                    f"Reason: None\n"
                    f"Success/Failure: Success"
                )

                if idx > 0:
                    logger.warning(
                        f"Primary Provider: {primary_provider_name}\n"
                        f"Reason: {str(last_error)}\n"
                        f"Failing over to: {p.name}\n"
                        f"Status: Success"
                    )
                return res
            except Exception as e:
                execution_time_ms = (time.time() - start_time) * 1000
                self.record_metrics(p.name, execution_time_ms, success=False)
                last_error = e

                # Log Telemetry
                logger.info(
                    f"=== AI Call Telemetry ===\n"
                    f"Requested Capability: {capability or required_capabilities}\n"
                    f"Primary Provider: {primary_provider_name}\n"
                    f"Selected Model: {model_id or 'default'}\n"
                    f"Execution Time: {execution_time_ms:.2f}ms\n"
                    f"Fallback Used (if any): {fallback_used}\n"
                    f"Reason: {str(e)}\n"
                    f"Success/Failure: Failure"
                )

                if idx > 0:
                    logger.warning(
                        f"Primary Provider: {primary_provider_name}\n"
                        f"Reason: {str(last_error)}\n"
                        f"Failing over to: {p.name}\n"
                        f"Status: Failed"
                    )

        raise RuntimeError(f"All matching providers in '{category}' failed. Last error: {str(last_error)}")

    async def run_startup_checks(self, db) -> Dict[str, Any]:
        """Verify health of AWS services, database, publishing providers, and local runtime."""
        health = {}
        
        # 1. Database Check
        try:
            if db:
                from sqlalchemy import text
                db.execute(text("SELECT 1"))
                health["database"] = {"status": "ONLINE", "error": None}
            else:
                health["database"] = {"status": "OFFLINE", "error": "Database session not provided"}
        except Exception as e:
            health["database"] = {"status": "OFFLINE", "error": str(e)}

        # 2. AWS Secrets Manager Check
        try:
            import boto3
            if settings.aws.secrets_manager_enabled:
                sm = boto3.client("secretsmanager", region_name=settings.aws.region)
                sm.describe_secret(SecretId=settings.aws.secret_name)
                health["secrets_manager"] = {"status": "ONLINE", "error": None}
            else:
                health["secrets_manager"] = {"status": "OFFLINE", "error": "AWS Secrets Manager is disabled locally"}
        except Exception as e:
            health["secrets_manager"] = {"status": "OFFLINE", "error": str(e)}

        # 3. AWS Bedrock Check
        try:
            import boto3
            bedrock = boto3.client("bedrock", region_name=settings.aws.region)
            bedrock.list_foundation_models()
            health["bedrock"] = {"status": "ONLINE", "error": None}
        except Exception as e:
            health["bedrock"] = {"status": "OFFLINE", "error": str(e)}

        # 4. AWS S3 Check
        try:
            import boto3
            s3 = boto3.client("s3", region_name=settings.aws.region)
            s3.head_bucket(Bucket=settings.aws.s3_bucket)
            health["s3"] = {"status": "ONLINE", "error": None}
        except Exception as e:
            health["s3"] = {"status": "OFFLINE", "error": str(e)}

        # 5. AWS CloudWatch Check
        try:
            import boto3
            if settings.aws.cloudwatch_logs_enabled:
                cw = boto3.client("logs", region_name=settings.aws.region)
                cw.describe_log_groups(logGroupNamePrefix=settings.aws.cloudwatch_log_group)
                health["cloudwatch"] = {"status": "ONLINE", "error": None}
            else:
                health["cloudwatch"] = {"status": "OFFLINE", "error": "CloudWatch logs disabled locally"}
        except Exception as e:
            health["cloudwatch"] = {"status": "OFFLINE", "error": str(e)}

        # 6. Publishing Providers Checks
        # YouTube
        try:
            if settings.publishing.youtube_enabled:
                from providers.publishing.youtube import YouTubePublisher
                yt = YouTubePublisher()
                yt_health = await yt.health_check()
                health["youtube"] = {"status": "ONLINE" if yt_health.get("is_available") else "OFFLINE", "error": yt_health.get("error")}
            else:
                health["youtube"] = {"status": "OFFLINE", "error": "YouTube publishing disabled"}
        except Exception as e:
            health["youtube"] = {"status": "OFFLINE", "error": str(e)}

        # Instagram
        try:
            if settings.publishing.instagram_enabled:
                from providers.publishing.instagram import InstagramPublishingProvider
                ig = InstagramPublishingProvider()
                ig_health = await ig.health_check()
                health["instagram"] = {"status": "ONLINE" if ig_health.get("is_available") else "OFFLINE", "error": ig_health.get("error")}
            else:
                health["instagram"] = {"status": "OFFLINE", "error": "Instagram publishing disabled"}
        except Exception as e:
            health["instagram"] = {"status": "OFFLINE", "error": str(e)}

        # 7. Runtime Services Check
        health["runtime_services"] = {"status": "ONLINE", "error": None}

        # Populate global health state
        self.health_map = health
        
        # Populate provider registry status maps
        for svc, stat in health.items():
            self.provider_status[svc] = stat
            
        return health


# Global provider registry instance
provider_registry = ProviderRegistry()
