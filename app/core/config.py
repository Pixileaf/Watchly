from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    TMDB_API_KEY: str
    PORT: int = 8000
    ADDON_ID: str = "com.bimal.watchly"
    APP_ENV: Literal["development", "production"] = "development"


settings = Settings()

