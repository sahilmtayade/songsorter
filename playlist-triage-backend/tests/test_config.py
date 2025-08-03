"""Tests for configuration management."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_with_env_vars(monkeypatch):
    """Test settings loading with environment variables."""
    # Set environment variables
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "test_client_secret")
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/auth/callback")
    monkeypatch.setenv("APP_SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    # Create settings instance
    settings = Settings()
    
    assert settings.SPOTIFY_CLIENT_ID == "test_client_id"
    assert settings.SPOTIFY_CLIENT_SECRET == "test_client_secret"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is True
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.is_development() is True
    assert settings.is_production() is False


def test_settings_validation(monkeypatch):
    """Test settings validation."""
    # Clear environment variables to ensure validation fails
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)
    
    with pytest.raises(ValidationError):
        # Missing required fields
        Settings(_env_file=None)  # Don't load from .env file


def test_log_level_validation():
    """Test log level validation."""
    with pytest.raises(ValidationError):
        Settings(
            SPOTIFY_CLIENT_ID="test",
            SPOTIFY_CLIENT_SECRET="test", 
            APP_SECRET_KEY="test",
            LOG_LEVEL="INVALID_LEVEL"
        )


def test_debug_field_conversion():
    """Test DEBUG field string to boolean conversion."""
    settings = Settings(
        SPOTIFY_CLIENT_ID="test",
        SPOTIFY_CLIENT_SECRET="test",
        APP_SECRET_KEY="test",
        DEBUG="true"
    )
    assert settings.DEBUG is True
    
    settings = Settings(
        SPOTIFY_CLIENT_ID="test",
        SPOTIFY_CLIENT_SECRET="test",
        APP_SECRET_KEY="test", 
        DEBUG="false"
    )
    assert settings.DEBUG is False