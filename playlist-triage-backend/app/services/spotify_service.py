from typing import Any, Dict, List, Optional

import httpx
import numpy as np

from app.schemas.spotify import Artist, AudioFeatures, PlaylistSimple, Track


class SpotifyService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_unassigned_saved_tracks(self, access_token: str) -> List[Track]:
        # Fetch all playlists
        playlists = []
        playlist_track_ids = set()
        url = "https://api.spotify.com/v1/me/playlists"
        headers = {"Authorization": f"Bearer {access_token}"}
        while url:
            resp = await self.client.get(url, headers=headers)
            data = resp.json()
            playlists.extend(data.get("items", []))
            url = data.get("next")
        # Fetch all tracks from all playlists
        for playlist in playlists:
            tracks_url = f"https://api.spotify.com/v1/playlists/{playlist['id']}/tracks"
            while tracks_url:
                resp = await self.client.get(tracks_url, headers=headers)
                data = resp.json()
                for item in data.get("items", []):
                    track = item.get("track")
                    if track:
                        playlist_track_ids.add(track["id"])
                tracks_url = data.get("next")
        # Fetch all saved tracks
        saved_tracks = []
        url = "https://api.spotify.com/v1/me/tracks"
        while url:
            resp = await self.client.get(url, headers=headers)
            data = resp.json()
            saved_tracks.extend(data.get("items", []))
            url = data.get("next")
        # Filter out tracks already in playlists
        unassigned_tracks = []
        for item in saved_tracks:
            track = item.get("track")
            if track and track["id"] not in playlist_track_ids:
                artists = [
                    Artist(id=a["id"], name=a["name"]) for a in track.get("artists", [])
                ]
                unassigned_tracks.append(
                    Track(
                        id=track["id"],
                        name=track["name"],
                        uri=track["uri"],
                        artists=artists,
                    )
                )
        return unassigned_tracks

    async def get_playlist_audio_profile(
        self, playlist_id: str, access_token: str
    ) -> Optional[Dict[str, Any]]:
        # Fetch all tracks in playlist
        track_ids = []
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {"Authorization": f"Bearer {access_token}"}
        while url:
            resp = await self.client.get(url, headers=headers)
            data = resp.json()
            for item in data.get("items", []):
                track = item.get("track")
                if track:
                    track_ids.append(track["id"])
            url = data.get("next")
        if len(track_ids) < 5:
            return None  # Not enough tracks for a reliable profile
        # Fetch audio features in batch
        features_url = (
            f"https://api.spotify.com/v1/audio-features?ids={','.join(track_ids[:100])}"
        )
        resp = await self.client.get(features_url, headers=headers)
        features_data = resp.json().get("audio_features", [])
        if not features_data:
            return None
        # Calculate mean and std for each feature
        feature_keys = [
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
        arr = np.array(
            [[f.get(k, 0) for k in feature_keys] for f in features_data if f]
        )
        means = dict(zip(feature_keys, np.mean(arr, axis=0)))
        stds = dict(zip(feature_keys, np.std(arr, axis=0)))
        return {"means": means, "stds": stds}

    def calculate_weighted_distance(
        self, track_features: Dict[str, float], playlist_profile: Dict[str, Any]
    ) -> float:
        # Weighted Euclidean distance
        means = playlist_profile["means"]
        stds = playlist_profile["stds"]
        feature_keys = [
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
        distance = 0.0
        for k in feature_keys:
            std = stds.get(k, 1e-6)  # Avoid division by zero
            weight = 1.0 / (std if std > 0 else 1e-6)
            diff = track_features.get(k, 0) - means.get(k, 0)
            distance += weight * (diff**2)
        # Normalize distance to a score (lower distance = higher score)
        score = max(0.0, 100.0 - distance)  # Simple normalization
        return score
        # Future improvement: Use more sophisticated normalization and feature selection
