"""Authentication router with improved structure and error handling."""

import base64
from typing import Dict, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.config import Settings
from app.core.dependencies import get_current_settings, get_http_client
from app.core.exceptions import SpotifyAPIException
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Spotify OAuth configuration
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SCOPES = [
    "playlist-read-private",
    "playlist-modify-public", 
    "playlist-modify-private",
    "user-library-read",
    "user-read-private"
]


@router.get("/login", summary="Initiate Spotify OAuth login")
def login(settings: Settings = Depends(get_current_settings)) -> RedirectResponse:
    """
    Initiate Spotify OAuth login flow.
    
    Redirects user to Spotify's authorization page.
    """
    logger.info("Initiating Spotify OAuth login")
    
    auth_params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": " ".join(SPOTIFY_SCOPES),
        "show_dialog": "true",  # Force user to reauthorize
    }
    
    # Build authorization URL
    param_string = "&".join([f"{k}={v}" for k, v in auth_params.items()])
    auth_url = f"{SPOTIFY_AUTH_URL}?{param_string}"
    
    logger.debug(f"Redirecting to Spotify auth URL: {auth_url}")
    return RedirectResponse(auth_url)


@router.get("/callback", summary="Handle Spotify OAuth callback")
async def callback(
    request: Request,
    settings: Settings = Depends(get_current_settings),
    client: httpx.AsyncClient = Depends(get_http_client),
) -> RedirectResponse:
    """
    Handle the OAuth callback from Spotify.
    
    Exchanges authorization code for access token and sets secure cookies.
    """
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    
    if error:
        logger.warning(f"OAuth callback received error: {error}")
        raise HTTPException(
            status_code=400, 
            detail=f"Spotify authorization failed: {error}"
        )
    
    if not code:
        logger.warning("OAuth callback missing authorization code")
        raise HTTPException(
            status_code=400, 
            detail="Missing authorization code"
        )
    
    logger.info("Processing OAuth callback with authorization code")
    
    # Exchange code for tokens
    token_data = await _exchange_code_for_tokens(code, settings, client)
    
    # Create response with redirect
    # In production, this should redirect to the frontend app
    response = RedirectResponse(
        url="/docs",  # For development - redirect to API docs
        status_code=302
    )
    
    # Set secure HTTP-only cookies for tokens
    if "access_token" in token_data:
        response.set_cookie(
            key="access_token",
            value=token_data["access_token"],
            httponly=True,
            secure=settings.is_production(),  # Only use secure in production
            samesite="lax",
            max_age=token_data.get("expires_in", 3600),
        )
        logger.info("Access token cookie set successfully")
    
    if "refresh_token" in token_data:
        response.set_cookie(
            key="refresh_token", 
            value=token_data["refresh_token"],
            httponly=True,
            secure=settings.is_production(),
            samesite="lax",
            max_age=30 * 24 * 3600,  # 30 days
        )
        logger.debug("Refresh token cookie set successfully")
    
    return response


@router.post("/logout", summary="Logout user")
def logout() -> RedirectResponse:
    """
    Log out the current user by clearing authentication cookies.
    """
    logger.info("User logging out")
    
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return response


async def _exchange_code_for_tokens(
    code: str, 
    settings: Settings, 
    client: httpx.AsyncClient
) -> Dict[str, Any]:
    """Exchange authorization code for access and refresh tokens."""
    
    token_request_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    
    try:
        logger.debug("Requesting tokens from Spotify")
        response = await client.post(
            SPOTIFY_TOKEN_URL, 
            data=token_request_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        
        token_data = response.json()
        logger.info("Successfully obtained tokens from Spotify")
        return token_data
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Token exchange failed: {e.response.status_code} - {e.response.text}")
        raise SpotifyAPIException(
            "Failed to exchange authorization code for tokens",
            {"status_code": e.response.status_code, "response": e.response.text}
        )
    except Exception as e:
        logger.error(f"Unexpected error during token exchange: {str(e)}")
        raise SpotifyAPIException(
            "Unexpected error during token exchange",
            {"error": str(e)}
        )
