from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = "Personal Shopper Assistant"
    app_env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./data/personal_shopper.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_timezone: str = "America/New_York"
    search_timeout_seconds: float = 12.0
    search_max_results_per_provider: int = 12
    ebay_app_id: str = ""
    bestbuy_api_key: str = ""
    read_only_mode: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
