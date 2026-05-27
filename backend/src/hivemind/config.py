"""Application configuration.

Single source of truth, env-driven via pydantic-settings. Drives storage backend
selection, database URL, OAuth credentials, and session config.
"""
from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    PRODUCTION = "production"


class StorageBackend(StrEnum):
    LOCAL = "local"
    GCS = "gcs"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    env: Environment = Field(default=Environment.LOCAL, alias="HIVEMIND_ENV")
    host: str = Field(default="0.0.0.0", alias="HIVEMIND_HOST")
    port: int = Field(default=8080, alias="HIVEMIND_PORT")
    log_level: str = Field(default="INFO", alias="HIVEMIND_LOG_LEVEL")

    storage_backend: StorageBackend = Field(default=StorageBackend.LOCAL, alias="STORAGE_BACKEND")
    local_content_root: Path = Field(
        default=Path("./content"), alias="HIVEMIND_LOCAL_CONTENT_ROOT"
    )
    gcs_bucket: str = Field(default="", alias="HIVEMIND_GCS_BUCKET")
    gcs_prefix: str = Field(default="", alias="HIVEMIND_GCS_PREFIX")

    database_url: str = Field(
        default="postgresql+psycopg://hivemind:hivemind@localhost:5432/hivemind",
        alias="DATABASE_URL",
    )

    google_oauth_client_id: str = Field(default="", alias="GOOGLE_OAUTH_CLIENT_ID")
    google_oauth_client_secret: str = Field(default="", alias="GOOGLE_OAUTH_CLIENT_SECRET")
    google_oauth_redirect_url: str = Field(
        default="http://localhost:8080/api/auth/google/callback",
        alias="GOOGLE_OAUTH_REDIRECT_URL",
    )
    session_secret: str = Field(default="dev-secret-change-me", alias="SESSION_SECRET")

    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")

    @property
    def is_local(self) -> bool:
        return self.env == Environment.LOCAL

    @property
    def oauth_enabled(self) -> bool:
        return bool(self.google_oauth_client_id and self.google_oauth_client_secret)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
