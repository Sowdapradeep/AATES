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
    gemini_api_key: str | None = None

class PublishingSettings(BaseModel):
    youtube_enabled: bool = False
    instagram_enabled: bool = False

class RenderingSettings(BaseModel):
    max_concurrent_renders: int = 2
    resolution: str = "1080p"

class AWSSettings(BaseModel):
    region: str = "us-east-1"
    s3_bucket: str = "aates-assets"
    secrets_manager_enabled: bool = False

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
