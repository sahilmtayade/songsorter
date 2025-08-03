import base64

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPES = "playlist-read-private playlist-modify-public playlist-modify-private user-library-read user-read-private"


@router.get("/login")
def login():
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
    }
    url = f"{SPOTIFY_AUTH_URL}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return RedirectResponse(url)


@router.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code provided"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(SPOTIFY_TOKEN_URL, data=data)
        token_data = resp.json()
    # For demo: store tokens in cookie (not secure for production)
    response = RedirectResponse("/app/triage")
    if "access_token" in token_data:
        response.set_cookie(
            key="access_token", value=token_data["access_token"], httponly=True
        )
        response.set_cookie(
            key="refresh_token",
            value=token_data.get("refresh_token", ""),
            httponly=True,
        )
    # Future improvement: Store tokens in a secure server-side session or database
    return response
