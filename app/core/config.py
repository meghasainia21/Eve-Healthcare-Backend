"""
Centralized application configuration.

Everything that varies between environments (local dev, docker, CI, prod)
lives here and is read from environment variables. This keeps secrets out
of source control and makes the twelve-factor-app story easy to explain.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "EVE Healthcare - Diagnostic Booking Service"
    API_V1_PREFIX: str = ""

    # --- Database ---
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/eve_healthcare"

    # --- Auth / JWT ---
    SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Misc ---
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
