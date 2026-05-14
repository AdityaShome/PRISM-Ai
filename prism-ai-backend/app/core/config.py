from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Prism AI"
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@db:5432/prism_ai",
        validation_alias="DATABASE_URL",
    )
    redis_url: str | None = Field(default=None, validation_alias="REDIS_URL")

    llm_provider: str = Field(default="gemini", validation_alias="LLM_PROVIDER")
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", validation_alias="GEMINI_MODEL")

    search_provider: str = Field(default="tavily", validation_alias="SEARCH_PROVIDER")
    tavily_api_key: str | None = Field(default=None, validation_alias="TAVILY_API_KEY")

    enable_llm_analysis: bool = Field(default=True, validation_alias="ENABLE_LLM_ANALYSIS")
    enable_web_search: bool = Field(default=True, validation_alias="ENABLE_WEB_SEARCH")
    enable_url_fetch: bool = Field(default=True, validation_alias="ENABLE_URL_FETCH")

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        validation_alias="CORS_ORIGINS",
    )
    request_timeout_seconds: float = Field(default=10.0, validation_alias="REQUEST_TIMEOUT_SECONDS")
    max_fetched_chars: int = Field(default=12_000, validation_alias="MAX_FETCHED_CHARS")
    max_url_bytes: int = Field(default=1_000_000, validation_alias="MAX_URL_BYTES")
    rate_limit_per_minute: int = Field(default=60, validation_alias="RATE_LIMIT_PER_MINUTE")
    auto_create_tables: bool = Field(default=False, validation_alias="AUTO_CREATE_TABLES")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return ["http://localhost:3000", "http://localhost:5173"]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return [str(value).strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
