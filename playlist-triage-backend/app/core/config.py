"""Configuration management for the application."""

import logging
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""

    # Spotify API Configuration
    SPOTIFY_CLIENT_ID: str = Field(..., description="Spotify API client ID")
    SPOTIFY_CLIENT_SECRET: str = Field(..., description="Spotify API client secret")
    SPOTIFY_REDIRECT_URI: str = Field(
        default="http://localhost:8000/auth/callback",
        description="Spotify OAuth redirect URI",
    )

    # Application Configuration
    APP_SECRET_KEY: str = Field(..., description="Secret key for application security")
    APP_NAME: str = Field(default="Playlist Triage API", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")

    # Environment Configuration
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development", description="Application environment"
    )
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # API Configuration
    API_V1_PREFIX: str = Field(default="/api/v1", description="API version 1 prefix")
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    # Security Configuration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, description="Access token expiration time in minutes"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @field_validator("DEBUG", mode="before")
    @classmethod
    def validate_debug(cls, v: str | bool) -> bool:
        """Convert string to boolean for DEBUG field."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()  # pyright: ignore[reportCallIssue]


# Create settings instance
settings = get_settings()
