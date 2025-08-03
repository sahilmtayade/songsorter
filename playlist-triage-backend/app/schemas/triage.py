from typing import List

from pydantic import BaseModel

from app.schemas.spotify import Track


class PlaylistSuggestion(BaseModel):
    playlist_id: str
    playlist_name: str
    match_score: float  # 0.0 to 100.0
    matching_tags: List[str]


class TriageResponse(BaseModel):
    song_to_sort: Track
    suggestions: List[PlaylistSuggestion]
