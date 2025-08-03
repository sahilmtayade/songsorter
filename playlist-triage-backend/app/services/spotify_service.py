"""Spotify API service with improved error handling and structure."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
import numpy as np

from app.core.exceptions import SpotifyAPIException
from app.core.logging import get_logger
from app.schemas.spotify import Artist, AudioFeatures, PlaylistSimple, Track

logger = get_logger(__name__)


class SpotifyServiceInterface(ABC):
    """Abstract interface for Spotify service."""
    
    @abstractmethod
    async def get_unassigned_saved_tracks(self, access_token: str) -> List[Track]:
        """Get tracks that are saved but not in any playlist."""
        pass
    
    @abstractmethod
    async def get_playlist_audio_profile(
        self, playlist_id: str, access_token: str
    ) -> Optional[Dict[str, Any]]:
        """Get audio feature profile for a playlist."""
        pass
    
    @abstractmethod
    def calculate_weighted_distance(
        self, track_features: Dict[str, float], playlist_profile: Dict[str, Any]
    ) -> float:
        """Calculate match score between track and playlist."""
        pass


class SpotifyService(SpotifyServiceInterface):
    """Service for interacting with Spotify API."""
    
    SPOTIFY_API_BASE = "https://api.spotify.com/v1"
    FEATURE_KEYS = [
        "danceability",
        "energy", 
        "key",
        "valence",
        "acousticness",
        "instrumentalness",
        "liveness",
        "speechiness",
        "tempo",
    ]
    MIN_TRACKS_FOR_PROFILE = 5
    MAX_BATCH_SIZE = 100
    
    def __init__(self, client: httpx.AsyncClient) -> None:
        """Initialize Spotify service with HTTP client."""
        self.client = client
    
    def _get_auth_headers(self, access_token: str) -> Dict[str, str]:
        """Get authorization headers for Spotify API."""
        return {"Authorization": f"Bearer {access_token}"}
    
    async def _make_spotify_request(
        self, 
        url: str, 
        access_token: str,
        method: str = "GET",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Make a request to Spotify API with error handling."""
        headers = self._get_auth_headers(access_token)
        
        try:
            response = await self.client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Spotify API error: {e.response.status_code} - {e.response.text}")
            raise SpotifyAPIException(
                f"Spotify API request failed: {e.response.status_code}",
                {"url": url, "status_code": e.response.status_code, "response": e.response.text}
            )
        except Exception as e:
            logger.error(f"Unexpected error in Spotify API request: {str(e)}")
            raise SpotifyAPIException(
                "Unexpected error in Spotify API request",
                {"url": url, "error": str(e)}
            )
    
    async def _get_paginated_data(
        self, 
        initial_url: str, 
        access_token: str,
        items_key: str = "items"
    ) -> List[Dict[str, Any]]:
        """Get all items from a paginated Spotify API endpoint."""
        all_items = []
        url = initial_url
        
        while url:
            data = await self._make_spotify_request(url, access_token)
            items = data.get(items_key, [])
            all_items.extend(items)
            url = data.get("next")
            
            logger.debug(f"Retrieved {len(items)} items, total: {len(all_items)}")
        
        return all_items
    
    async def get_unassigned_saved_tracks(self, access_token: str) -> List[Track]:
        """Get tracks that are saved but not in any playlist."""
        logger.info("Starting to fetch unassigned saved tracks")
        
        # Fetch all playlists
        logger.debug("Fetching user playlists")
        playlists = await self._get_paginated_data(
            f"{self.SPOTIFY_API_BASE}/me/playlists",
            access_token
        )
        
        # Collect all track IDs from playlists
        playlist_track_ids = set()
        for playlist in playlists:
            logger.debug(f"Fetching tracks for playlist: {playlist.get('name')}")
            tracks_url = f"{self.SPOTIFY_API_BASE}/playlists/{playlist['id']}/tracks"
            track_items = await self._get_paginated_data(tracks_url, access_token)
            
            for item in track_items:
                track = item.get("track")
                if track and track.get("id"):
                    playlist_track_ids.add(track["id"])
        
        logger.info(f"Found {len(playlist_track_ids)} tracks across {len(playlists)} playlists")
        
        # Fetch all saved tracks
        logger.debug("Fetching saved tracks")
        saved_track_items = await self._get_paginated_data(
            f"{self.SPOTIFY_API_BASE}/me/tracks",
            access_token
        )
        
        # Filter out tracks already in playlists
        unassigned_tracks = []
        for item in saved_track_items:
            track = item.get("track")
            if track and track.get("id") and track["id"] not in playlist_track_ids:
                try:
                    artists = [
                        Artist(id=a["id"], name=a["name"]) 
                        for a in track.get("artists", [])
                    ]
                    unassigned_tracks.append(
                        Track(
                            id=track["id"],
                            name=track["name"],
                            uri=track["uri"],
                            artists=artists,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse track {track.get('id')}: {str(e)}")
                    continue
        
        logger.info(f"Found {len(unassigned_tracks)} unassigned tracks")
        return unassigned_tracks
    
    async def get_playlist_audio_profile(
        self, playlist_id: str, access_token: str
    ) -> Optional[Dict[str, Any]]:
        """Get audio feature profile for a playlist."""
        logger.debug(f"Getting audio profile for playlist: {playlist_id}")
        
        # Fetch all tracks in playlist
        tracks_url = f"{self.SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks"
        track_items = await self._get_paginated_data(tracks_url, access_token)
        
        track_ids = []
        for item in track_items:
            track = item.get("track")
            if track and track.get("id"):
                track_ids.append(track["id"])
        
        if len(track_ids) < self.MIN_TRACKS_FOR_PROFILE:
            logger.warning(
                f"Playlist {playlist_id} has only {len(track_ids)} tracks, "
                f"need at least {self.MIN_TRACKS_FOR_PROFILE} for profile"
            )
            return None
        
        # Fetch audio features in batches
        features_data = []
        for i in range(0, len(track_ids), self.MAX_BATCH_SIZE):
            batch_ids = track_ids[i:i + self.MAX_BATCH_SIZE]
            features_url = f"{self.SPOTIFY_API_BASE}/audio-features"
            params = {"ids": ",".join(batch_ids)}
            
            response_data = await self._make_spotify_request(
                features_url, access_token, params=params
            )
            batch_features = response_data.get("audio_features", [])
            features_data.extend([f for f in batch_features if f is not None])
        
        if not features_data:
            logger.warning(f"No audio features found for playlist {playlist_id}")
            return None
        
        # Calculate statistics
        try:
            feature_matrix = np.array([
                [f.get(k, 0.0) for k in self.FEATURE_KEYS] 
                for f in features_data
            ])
            
            means = dict(zip(self.FEATURE_KEYS, np.mean(feature_matrix, axis=0)))
            stds = dict(zip(self.FEATURE_KEYS, np.std(feature_matrix, axis=0)))
            
            logger.debug(f"Calculated profile for {len(features_data)} tracks")
            return {"means": means, "stds": stds, "track_count": len(features_data)}
            
        except Exception as e:
            logger.error(f"Error calculating audio profile: {str(e)}")
            return None
    
    def calculate_weighted_distance(
        self, track_features: Dict[str, float], playlist_profile: Dict[str, Any]
    ) -> float:
        """Calculate weighted distance between track and playlist profile."""
        means = playlist_profile["means"]
        stds = playlist_profile["stds"]
        
        distance = 0.0
        for feature_key in self.FEATURE_KEYS:
            std = stds.get(feature_key, 1e-6)
            # Avoid division by zero and use meaningful weight
            weight = 1.0 / max(std, 1e-6)
            
            track_value = track_features.get(feature_key, 0.0)
            mean_value = means.get(feature_key, 0.0)
            
            diff = track_value - mean_value
            distance += weight * (diff ** 2)
        
        # Normalize to 0-100 scale (higher is better match)
        # Use exponential decay to convert distance to score
        score = 100.0 * np.exp(-distance / 10.0)
        return float(np.clip(score, 0.0, 100.0))
