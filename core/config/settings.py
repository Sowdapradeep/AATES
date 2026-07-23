import os
from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class ApplicationSettings(BaseModel):
    name: str = "AATES"
    version: str = "1.0.0"
    env: str = "development"  # development, testing, production
    debug: bool = True

class DatabaseSettings(BaseModel):
    url: str = "postgresql://postgres:postgres@localhost:5432/aates"
    pool_size: int = 20
    max_overflow: int = 10

class RedisSettings(BaseModel):
    url: str = "redis://localhost:6379/0"

class SecuritySettings(BaseModel):
    secret_key: str = "supersecretkey_change_me_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

class AISettings(BaseModel):
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", os.getenv("ai__gemini_api_key")))
    stability_api_key: str | None = None
    elevenlabs_api_key: str | None = None
    groq_api_key: str | None = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", os.getenv("ai__groq_api_key")))
    
    # Provider Settings
    provider: str = Field(default_factory=lambda: os.getenv("AI_PROVIDER", "bedrock"))
    image_provider: str = Field(default_factory=lambda: os.getenv("IMAGE_PROVIDER", "bedrock"))
    allow_external_failover: bool = Field(default_factory=lambda: os.getenv("AI_ALLOW_EXTERNAL_FAILOVER", "True").lower() in ("true", "1"))
    
    # Bedrock Centralized Models
    bedrock_reasoning_model: str = Field(default_factory=lambda: os.getenv("BEDROCK_REASONING_MODEL", "amazon.nova-pro-v1:0"))
    bedrock_fast_model: str = Field(default_factory=lambda: os.getenv("BEDROCK_FAST_MODEL", "amazon.nova-lite-v1:0"))
    bedrock_embedding_model: str = Field(default_factory=lambda: os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v1"))
    bedrock_image_model: str = Field(default_factory=lambda: os.getenv("BEDROCK_IMAGE_MODEL", "amazon.titan-image-generator-v2:0"))
    
    # Gemini Settings
    gemini_enabled: bool = Field(default_factory=lambda: os.getenv("GEMINI_ENABLED", "True").lower() in ("true", "1"))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-pro"))
    
    # Groq Settings
    groq_enabled: bool = Field(default_factory=lambda: os.getenv("GROQ_ENABLED", "True").lower() in ("true", "1"))
    
    bedrock_region: str = Field(default_factory=lambda: os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")))
    
    bedrock_model_mappings: dict[str, str] = Field(default_factory=lambda: {
        "text_generation": os.getenv("BEDROCK_REASONING_MODEL", "amazon.nova-pro-v1:0"),
        "image_generation": os.getenv("BEDROCK_IMAGE_MODEL", "amazon.titan-image-generator-v2:0"),
        "video_generation": "amazon.titan-video-generator-v1",
        "embeddings": os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2")
    })

class PublishingSettings(BaseModel):
    youtube_enabled: bool = Field(default_factory=lambda: os.getenv("YOUTUBE_ENABLED", os.getenv("publishing__youtube_enabled", "False")).lower() in ("true", "1"))
    instagram_enabled: bool = Field(default_factory=lambda: os.getenv("INSTAGRAM_ENABLED", os.getenv("publishing__instagram_enabled", "False")).lower() in ("true", "1"))
    
    # YouTube credentials
    youtube_client_id: str | None = None
    youtube_client_secret: str | None = None
    youtube_refresh_token: str | None = None
    youtube_channel_id: str | None = None
    
    # Meta / Instagram credentials
    meta_app_id: str | None = None
    meta_app_secret: str | None = None
    instagram_access_token: str | None = None
    instagram_business_account_id: str | None = None
    facebook_page_id: str | None = None

class RenderingSettings(BaseModel):
    max_concurrent_renders: int = 2
    resolution: str = "1080p"

from pydantic import AliasChoices

class AWSSettings(BaseModel):
    region: str = Field(default_factory=lambda: os.getenv("AWS_REGION", os.getenv("aws_region", "us-east-1")))
    s3_bucket: str = Field(default_factory=lambda: os.getenv("AWS_S3_BUCKET", os.getenv("aws_s3_bucket", "aates-assets")))
    secrets_manager_enabled: bool = Field(default_factory=lambda: os.getenv("AWS_SECRETS_MANAGER_ENABLED", "False").lower() in ("true", "1"))
    secret_name: str = Field(default_factory=lambda: os.getenv("AWS_SECRET_NAME", os.getenv("aws_secret_name", "aates-production-secrets")))
    cloudwatch_logs_enabled: bool = Field(default_factory=lambda: os.getenv("AWS_CLOUDWATCH_LOGS_ENABLED", "False").lower() in ("true", "1"))
    cloudwatch_log_group: str = Field(default_factory=lambda: os.getenv("AWS_CLOUDWATCH_LOG_GROUP", "aates-logs"))

class Settings(BaseSettings):
    app: ApplicationSettings = Field(default_factory=ApplicationSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    ai: AISettings = Field(default_factory=AISettings)
    publishing: PublishingSettings = Field(default_factory=PublishingSettings)
    rendering: RenderingSettings = Field(default_factory=RenderingSettings)
    aws: AWSSettings = Field(default_factory=AWSSettings)

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
