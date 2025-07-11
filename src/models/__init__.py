"""Data models for the music player application."""

from .models import (
    Song,
    SearchResult,
    ThemeColors,
    SongDict,
    PlaylistDict,
    SettingsDict,
    AUDIO_EXTENSIONS,
    DEFAULT_VOLUME,
    POSITION_UPDATE_INTERVAL,
    DEFAULT_CROSSFADE_ENABLED,
    DEFAULT_CROSSFADE_DURATION,
    DEFAULT_AUDIO_OUTPUT
)

__all__ = [
    'Song',
    'SearchResult',
    'ThemeColors',
    'SongDict',
    'PlaylistDict',
    'SettingsDict',
    'AUDIO_EXTENSIONS',
    'DEFAULT_VOLUME',
    'POSITION_UPDATE_INTERVAL',
    'DEFAULT_CROSSFADE_ENABLED',
    'DEFAULT_CROSSFADE_DURATION',
    'DEFAULT_AUDIO_OUTPUT'
]