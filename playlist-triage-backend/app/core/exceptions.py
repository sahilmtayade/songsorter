"""Custom exceptions for the application."""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception class for application-specific errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.status_code = status_code


class SpotifyAPIException(AppException):
    """Exception raised when Spotify API calls fail."""
    
    def __init__(
        self,
        message: str = "Spotify API error",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 502
    ) -> None:
        super().__init__(message, details, status_code)


class AuthenticationException(AppException):
    """Exception raised for authentication errors."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 401
    ) -> None:
        super().__init__(message, details, status_code)


class AuthorizationException(AppException):
    """Exception raised for authorization errors."""
    
    def __init__(
        self,
        message: str = "Authorization failed",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 403
    ) -> None:
        super().__init__(message, details, status_code)


class ValidationException(AppException):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 422
    ) -> None:
        super().__init__(message, details, status_code)


class ResourceNotFoundException(AppException):
    """Exception raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 404
    ) -> None:
        super().__init__(message, details, status_code)