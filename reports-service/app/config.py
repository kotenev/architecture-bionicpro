"""
Configuration settings for Reports Service.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service info
    app_name: str = "BionicPRO Reports Service"
    app_version: str = "1.0.0"
    debug: bool = False

    # ClickHouse connection
    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 9000
    clickhouse_user: str = "reports_reader"
    clickhouse_password: str = "reports_password_change_me"
    clickhouse_database: str = "reports"

    # Redis cache
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 1
    cache_ttl_seconds: int = 300  # 5 minutes

    # JWT / Auth
    jwt_secret_key: str = "your-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    auth_service_url: str = "http://bionicpro-auth:8000"

    # Keycloak public key URL (for JWT validation)
    keycloak_url: str = "http://keycloak:8080"
    keycloak_realm: str = "reports-realm"

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
