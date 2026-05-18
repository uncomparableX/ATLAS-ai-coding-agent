from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "AgentForge"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    DATABASE_URL: str = "postgresql+asyncpg://agentforge:agentforge_secret@localhost:5432/agentforge"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    REDIS_URL: str = "redis://:agentforge_redis@localhost:6379/0"
    REDIS_POOL_SIZE: int = 20

    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def set_broker(cls, v, info):
        return v or info.data.get("REDIS_URL", "")

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def set_result(cls, v, info):
        return v or info.data.get("REDIS_URL", "")

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = "agentforge_qdrant"
    QDRANT_CODE_COLLECTION: str = "code_chunks"
    QDRANT_MEMORY_COLLECTION: str = "agent_memory"

    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: Optional[str] = None
    DEFAULT_MODEL: str = "claude-opus-4-5"
    FAST_MODEL: str = "claude-sonnet-4-5"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    MAX_TOKENS: int = 8192
    TEMPERATURE: float = 0.2

    GITHUB_TOKEN: Optional[str] = None

    REPO_STORAGE_PATH: str = "/app/repos"
    MAX_REPO_SIZE_MB: int = 500

    DOCKER_HOST: str = "unix:///var/run/docker.sock"
    SANDBOX_IMAGE: str = "agentforge-sandbox:latest"
    SANDBOX_TIMEOUT_SECONDS: int = 300
    SANDBOX_MEMORY_LIMIT: str = "512m"
    SANDBOX_CPU_QUOTA: int = 50000

    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    MAX_AGENT_ITERATIONS: int = 20
    MAX_RETRY_ATTEMPTS: int = 3
    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 200

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
