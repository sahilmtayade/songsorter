"""Triage router with improved structure and dependency injection."""

from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.dependencies import get_current_user_token, get_http_client, get_spotify_service
from app.core.exceptions import ResourceNotFoundException, SpotifyAPIException
from app.core.logging import get_logger
from app.schemas.spotify import Track
from app.schemas.triage import PlaylistSuggestion, TriageResponse
from app.services.spotify_service import SpotifyService

logger = get_logger(__name__)

router = APIRouter(prefix="/triage", tags=["triage"])


@router.get("/next", response_model=TriageResponse, summary="Get next song to triage")
async def next_song(
    access_token: str = Depends(get_current_user_token),
    spotify_service: SpotifyService = Depends(get_spotify_service),
    client: httpx.AsyncClient = Depends(get_http_client),
) -> TriageResponse:
    """
    Get the next song to triage with playlist suggestions.
    
    Returns a song that needs to be sorted along with suggested playlists
    ranked by compatibility score.
    """
    logger.info("Processing triage request for next song")
    
    try:
        # Get unassigned songs
        logger.debug("Fetching unassigned tracks")
        unassigned_tracks = await spotify_service.get_unassigned_saved_tracks(access_token)
        
        if not unassigned_tracks:
            logger.info("No unassigned songs found")
            raise ResourceNotFoundException(
                "No unassigned songs found",
                {"message": "All your saved songs are already in playlists!"}
            )
        
        # Get the first song to process
        # TODO: Implement user progress tracking to resume from where they left off
        song = unassigned_tracks[0]
        logger.info(f"Processing song: {song.name} by {', '.join(a.name for a in song.artists)}")
        
        # Get user's playlists
        logger.debug("Fetching user playlists")
        playlists = await _get_user_playlists(client, access_token)
        
        # Get audio features for the song
        logger.debug(f"Fetching audio features for song: {song.id}")
        track_features = await _get_track_audio_features(client, song.id, access_token)
        
        # Generate suggestions
        suggestions = await _generate_playlist_suggestions(
            spotify_service, playlists, track_features, access_token
        )
        
        logger.info(f"Generated {len(suggestions)} playlist suggestions")
        
        return TriageResponse(
            song_to_sort=song,
            suggestions=suggestions
        )
        
    except (ResourceNotFoundException, SpotifyAPIException):
        # Re-raise known exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in triage processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        )


async def _get_user_playlists(
    client: httpx.AsyncClient, 
    access_token: str
) -> List[dict]:
    """Get all user playlists from Spotify API."""
    playlists = []
    url = "https://api.spotify.com/v1/me/playlists"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    while url:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            playlists.extend(data.get("items", []))
            url = data.get("next")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch playlists: {e.response.status_code}")
            raise SpotifyAPIException(
                "Failed to fetch user playlists",
                {"status_code": e.response.status_code}
            )
    
    return playlists


async def _get_track_audio_features(
    client: httpx.AsyncClient,
    track_id: str,
    access_token: str
) -> dict:
    """Get audio features for a specific track."""
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch audio features for track {track_id}: {e.response.status_code}")
        raise SpotifyAPIException(
            "Failed to fetch track audio features",
            {"track_id": track_id, "status_code": e.response.status_code}
        )


async def _generate_playlist_suggestions(
    spotify_service: SpotifyService,
    playlists: List[dict],
    track_features: dict,
    access_token: str
) -> List[PlaylistSuggestion]:
    """Generate playlist suggestions based on audio feature matching."""
    suggestions = []
    
    for playlist in playlists:
        try:
            # Get audio profile for this playlist
            profile = await spotify_service.get_playlist_audio_profile(
                playlist["id"], access_token
            )
            
            if not profile:
                logger.debug(f"Skipping playlist {playlist['name']} - insufficient tracks for profile")
                continue
            
            # Calculate match score
            score = spotify_service.calculate_weighted_distance(track_features, profile)
            
            # Generate descriptive tags based on features and profile
            tags = _generate_matching_tags(track_features, profile)
            
            suggestions.append(
                PlaylistSuggestion(
                    playlist_id=playlist["id"],
                    playlist_name=playlist["name"],
                    match_score=score,
                    matching_tags=tags,
                )
            )
            
        except Exception as e:
            logger.warning(f"Failed to process playlist {playlist.get('name', 'unknown')}: {str(e)}")
            continue
    
    # Sort by match score (highest first)
    suggestions.sort(key=lambda s: s.match_score, reverse=True)
    
    return suggestions


def _generate_matching_tags(track_features: dict, playlist_profile: dict) -> List[str]:
    """Generate descriptive tags based on feature matching."""
    tags = []
    
    # Energy-based tags
    energy = track_features.get("energy", 0)
    if energy > 0.7:
        tags.append("High Energy")
    elif energy < 0.3:
        tags.append("Low Energy")
    
    # Danceability tags
    danceability = track_features.get("danceability", 0)
    if danceability > 0.7:
        tags.append("Very Danceable")
    
    # Valence (mood) tags
    valence = track_features.get("valence", 0)
    if valence > 0.7:
        tags.append("Positive Mood")
    elif valence < 0.3:
        tags.append("Melancholic")
    
    # Acousticness tags
    acousticness = track_features.get("acousticness", 0)
    if acousticness > 0.6:
        tags.append("Acoustic")
    
    # Instrumentalness tags
    instrumentalness = track_features.get("instrumentalness", 0)
    if instrumentalness > 0.5:
        tags.append("Instrumental")
    
    # Consistency tags based on playlist profile
    profile_stds = playlist_profile.get("stds", {})
    
    # Check if playlist has consistent key
    if profile_stds.get("key", 1) < 1:
        tags.append("Consistent Key")
    
    # Check if playlist has consistent tempo
    if profile_stds.get("tempo", 50) < 20:
        tags.append("Consistent Tempo")
    
    return tags
