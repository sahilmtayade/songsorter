from typing import List, Optional

from pydantic import BaseModel


class Artist(BaseModel):
    id: str
    name: str


class Track(BaseModel):
    id: str
    name: str
    uri: str
    artists: List[Artist]


class PlaylistSimple(BaseModel):
    id: str
    name: str
    owner: str


class AudioFeatures(BaseModel):
    danceability: float
    energy: float
    key: int
    valence: float
    acousticness: float
    instrumentalness: float
    liveness: float
    speechiness: float
    tempo: float
