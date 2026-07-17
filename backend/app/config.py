from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "CloudCertPro"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str
    app_port: int = 8000

    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 40

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Elasticsearch
    elasticsearch_hosts: str = "http://localhost:9200"

    # Storage
    storage_endpoint: str = "http://localhost:9000"
    storage_access_key: str = "minioadmin"
    storage_secret_key: str = "minioadmin"
    storage_bucket: str = "cloudcert-media"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/1"

    # AI
    openai_api_key: str | None = None

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
