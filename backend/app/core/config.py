from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	app_name: str = "AI Logistics Control Tower"
	api_prefix: str = "/api"
	database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/logistics"
	redis_url: str = "redis://localhost:6379/0"
	analytics_cache_ttl_seconds: int = 300
	cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
	eta_model_path: str = "artifacts/eta_model.joblib"

	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

	@field_validator("cors_origins", mode="before")
	@classmethod
	def parse_cors_origins(cls, value: object) -> list[str]:
		if isinstance(value, str):
			return [origin.strip() for origin in value.split(",") if origin.strip()]
		if isinstance(value, list):
			return [str(origin).strip() for origin in value if str(origin).strip()]
		return ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
	return Settings()


settings = get_settings()
