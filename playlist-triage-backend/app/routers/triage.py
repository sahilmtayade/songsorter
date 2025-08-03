from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas.spotify import Track
from app.schemas.triage import PlaylistSuggestion, TriageResponse
from app.services.spotify_service import SpotifyService

router = APIRouter(prefix="/triage", tags=["triage"])


# Dependency to extract access_token from cookie or Authorization header
def get_access_token(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")
    return token


@router.get("/next", response_model=TriageResponse)
async def next_song(request: Request, access_token: str = Depends(get_access_token)):
    async with httpx.AsyncClient() as client:
        service = SpotifyService(client)
        # Get unassigned songs
        unassigned_tracks: List[Track] = await service.get_unassigned_saved_tracks(
            access_token
        )
        if not unassigned_tracks:
            raise HTTPException(status_code=404, detail="No unassigned songs found.")
        song = unassigned_tracks[0]  # Future: track user progress
        # Get user's playlists
        playlists = []
        url = "https://api.spotify.com/v1/me/playlists"
        headers = {"Authorization": f"Bearer {access_token}"}
        while url:
            resp = await client.get(url, headers=headers)
            data = resp.json()
            playlists.extend(data.get("items", []))
            url = data.get("next")
        suggestions = []
        # Get audio features for the song
        features_url = f"https://api.spotify.com/v1/audio-features/{song.id}"
        resp = await client.get(features_url, headers=headers)
        track_features = resp.json()
        for playlist in playlists:
            profile = await service.get_playlist_audio_profile(
                playlist["id"], access_token
            )
            if profile:
                score = service.calculate_weighted_distance(track_features, profile)
                tags = []
                # Example tags: High Energy, Stable Key, etc. (Future: improve tagging logic)
                if track_features.get("energy", 0) > 0.7:
                    tags.append("High Energy")
                if profile["stds"].get("key", 1) < 1:
                    tags.append("Stable Key")
                suggestions.append(
                    PlaylistSuggestion(
                        playlist_id=playlist["id"],
                        playlist_name=playlist["name"],
                        match_score=score,
                        matching_tags=tags,
                    )
                )
        suggestions.sort(key=lambda s: s.match_score, reverse=True)
        return TriageResponse(song_to_sort=song, suggestions=suggestions)
