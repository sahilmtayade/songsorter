"""Middleware package initialization."""

from .error_handling import error_handling_middleware

__all__ = ["error_handling_middleware"]