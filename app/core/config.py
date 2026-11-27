"""Configuración de la aplicación leída desde variables de entorno (prefijo APP_)."""

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, PostgresDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    name: str = "back-office-ia-pods"
    environment: Environment = Environment.LOCAL
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: PostgresDsn = Field(
        default=PostgresDsn("postgresql+asyncpg://app:app@localhost:5432/app"),
    )
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Se usan en el change `add-iam-auth`.
    jwt_secret_key: SecretStr = SecretStr("")
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl_minutes: int = 15
    jwt_refresh_token_ttl_days: int = 7

    # Se usan en el change `add-robot-executions`.
    trigger_timeout_seconds: float = 10.0
    trigger_allowed_hosts: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_jwt_secret_key(self) -> "Settings":
        configured_key = self.jwt_secret_key.get_secret_value()
        if not configured_key:
            if self.environment not in (Environment.LOCAL, Environment.TEST):
                raise ValueError(
                    "APP_JWT_SECRET_KEY is required outside local and test environments"
                )
            return self

        if configured_key == "change-me" or len(configured_key) < 32:
            raise ValueError(
                "APP_JWT_SECRET_KEY must be a non-default value of at least 32 characters"
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    return Settings()
