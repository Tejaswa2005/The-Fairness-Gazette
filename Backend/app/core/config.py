from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	"""Application settings loaded from environment variables or .env files."""

	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

	app_name: str = "THE FAIRNESS GAZETTE API"
	app_version: str = "0.6.0"
	api_v1_prefix: str = "/"
	database_url: str = "sqlite:///./fairness_gazette.db"
	cors_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")
	log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
	max_upload_mb: int = 16

	@property
	def cors_origin_list(self) -> list[str]:
		return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
	return Settings()
