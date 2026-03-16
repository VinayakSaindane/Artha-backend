from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import Header, HTTPException


AI_SERVICE_DIR = Path(__file__).resolve().parents[1]
BACKEND_ROOT_DIR = AI_SERVICE_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(AI_SERVICE_DIR / ".env", BACKEND_ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ARTHA AI Service"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    mongo_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongo_db_name: str = Field(default="artha", alias="MONGO_DB_NAME")
    mongo_tls_mode: Literal["auto", "enabled", "disabled"] = Field(default="auto", alias="MONGO_TLS_MODE")
    mongo_tls_ca_file: str | None = Field(default=None, alias="MONGO_TLS_CA_FILE")
    ai_service_api_key: str = Field(default="artha-ai-internal-key", alias="AI_SERVICE_API_KEY")
    cache_ttl_seconds: int = Field(default=300, alias="CACHE_TTL_SECONDS")
    max_upload_mb: int = Field(default=5, alias="MAX_UPLOAD_MB")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if x_api_key != settings.ai_service_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")