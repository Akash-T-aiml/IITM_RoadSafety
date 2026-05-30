"""
SmartRescue AI — Application Settings
Loads configuration from environment variables with Pydantic BaseSettings.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration loaded from .env file."""

    # ── Firebase ──────────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = Field(
        default="./firebase-service-account.json",
        description="Path to Firebase service account JSON"
    )
    FIREBASE_PROJECT_ID: str = Field(
        default="smartrescue-ai",
        description="Firebase project ID"
    )

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET: str = Field(
        default="change-this-in-production",
        description="Secret key for signing JWTs"
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_MINUTES: int = Field(default=1440)  # 24 hours

    # ── ML Model ─────────────────────────────────────────────
    ML_MODEL_PATH: str = Field(
        default="./ml_models/smartrescue_final_model.pkl",
        description="Path to trained RandomForest .pkl model"
    )
    CONFIDENCE_AUTO_TRIGGER: float = Field(
        default=0.85,
        description="Above this confidence, auto-trigger emergency"
    )
    CONFIDENCE_ASK_THRESHOLD: float = Field(
        default=0.50,
        description="Between this and auto-trigger, ask for confirmation"
    )
    FALSE_ALARM_BUFFER_SIZE: int = Field(
        default=3,
        description="Number of consecutive severe predictions before triggering"
    )

    # ── Ambulance / Hospital radius ──────────────────────────
    MAX_AMBULANCE_RADIUS_KM: float = Field(default=50.0)
    MAX_HOSPITAL_RADIUS_KM: float = Field(default=100.0)

    # ── Rate Limiting ────────────────────────────────────────
    RATE_LIMIT_DEFAULT: str = Field(default="60/minute")
    RATE_LIMIT_SENSOR: str = Field(default="120/minute")

    # ── Server ───────────────────────────────────────────────
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")

    # ── CORS ─────────────────────────────────────────────────
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated allowed origins"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
