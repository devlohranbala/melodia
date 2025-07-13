from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import Song, SearchResult, PlaylistDict, SettingsDict


# Request Models
class CreatePlaylistRequest(BaseModel):
    name: str
    description: str = ""


class AddToPlaylistRequest(BaseModel):
    song_id: str  # file_path used as ID


class UpdateSettingsRequest(BaseModel):
    theme: Optional[str] = None
    color_theme: Optional[str] = None
    default_volume: Optional[int] = None
    downloads_dir: Optional[str] = None
    crossfade_enabled: Optional[bool] = None
    crossfade_duration: Optional[int] = None
    audio_output: Optional[str] = None


class DownloadRequest(BaseModel):
    url: str


# Response Models
class SongResponse(BaseModel):
    id: str  # file_path used as ID
    title: str
    artist: str
    file_path: str
    date: str
    thumbnail_path: str
    has_thumbnail: bool
    
    @classmethod
    def from_song(cls, song: Song) -> 'SongResponse':
        return cls(
            id=song.file_path,
            title=song.title,
            artist=song.artist,
            file_path=song.file_path,
            date=song.date,
            thumbnail_path=song.thumbnail_path or "",
            has_thumbnail=bool(song.thumbnail_path)
        )


class PlaylistResponse(BaseModel):
    name: str
    description: str
    songs: List[SongResponse]
    song_count: int
    created_date: str
    
    @classmethod
    def from_playlist(cls, name: str, playlist_data: PlaylistDict) -> 'PlaylistResponse':
        songs_data = playlist_data.get('songs', [])
        songs = []
        
        for song_dict in songs_data:
            if isinstance(song_dict, dict):
                song = Song.from_dict(song_dict)
                songs.append(SongResponse.from_song(song))
        
        return cls(
            name=name,
            description=playlist_data.get('description', ''),
            songs=songs,
            song_count=len(songs),
            created_date=playlist_data.get('created_date', '')
        )


class SearchResultResponse(BaseModel):
    title: str
    artist: str
    url: str
    duration: str
    view_count: int
    formatted_views: str
    
    @classmethod
    def from_search_result(cls, result: SearchResult) -> 'SearchResultResponse':
        return cls(
            title=result.title,
            artist=result.artist,
            url=result.url,
            duration=result.duration,
            view_count=result.view_count,
            formatted_views=result.formatted_views
        )


class SettingsResponse(BaseModel):
    theme: str
    color_theme: str
    default_volume: int
    downloads_dir: str
    crossfade_enabled: bool
    crossfade_duration: int
    audio_output: Optional[str]
    
    @classmethod
    def from_settings(cls, settings: SettingsDict) -> 'SettingsResponse':
        return cls(
            theme=settings.get('theme', 'dark'),
            color_theme=settings.get('color_theme', 'blue'),
            default_volume=settings.get('default_volume', 70),
            downloads_dir=settings.get('downloads_dir', ''),
            crossfade_enabled=settings.get('crossfade_enabled', False),
            crossfade_duration=settings.get('crossfade_duration', 3),
            audio_output=settings.get('audio_output')
        )


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str = datetime.now().isoformat()


class SuccessResponse(BaseModel):
    message: str
    timestamp: str = datetime.now().isoformat()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"