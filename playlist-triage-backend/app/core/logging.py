"""Logging configuration for the application."""

import logging
import sys
from typing import Any, Dict

from app.core.config import settings


def setup_logging() -> None:
    """Set up application logging configuration."""
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=(
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(module)s:%(lineno)d - %(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configure specific loggers
    loggers_config: Dict[str, Any] = {
        "app": {"level": settings.LOG_LEVEL},
        "uvicorn": {"level": "INFO"},
        "httpx": {"level": "WARNING"},
        "httpcore": {"level": "WARNING"},
    }
    
    for logger_name, config in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, config["level"]))
    
    # Disable some noisy loggers in development
    if settings.is_development():
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)