"""Dependency injection setup for the application."""

from typing import AsyncGenerator

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.core.logging import get_logger
from app.services.spotify_service import SpotifyService

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide HTTP client dependency."""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    ) as client:
        yield client


async def get_spotify_service(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> SpotifyService:
    """Provide Spotify service dependency."""
    return SpotifyService(client)


def get_access_token_from_request(request: Request) -> str:
    """Extract access token from request cookies or Authorization header."""
    # Try to get token from cookie first
    token = request.cookies.get("access_token")
    
    if not token:
        # Try to get from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
    
    if not token:
        logger.warning("No access token found in request")
        raise AuthenticationException("Access token required")
    
    return token


async def get_current_user_token(
    request: Request,
) -> str:
    """Get and validate current user's access token."""
    try:
        return get_access_token_from_request(request)
    except AuthenticationException:
        raise HTTPException(status_code=401, detail="Authentication required")


def get_current_settings():
    """Provide application settings dependency."""
    return settings