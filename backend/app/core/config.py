from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./devops_agent.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    OLLAMA_URL: str = "http://localhost:11434"
    SECRET_KEY: str = "dev-secret-key-change-in-production-at-least-32-characters-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_CODE_MODEL: str = "codellama"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_STORE_PATH: str = "./faiss_index"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    APP_NAME: str = "DevOps Agent Platform"
    APP_VERSION: str = "1.0.0"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
