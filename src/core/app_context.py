from dataclasses import dataclass, field
from typing import Optional, Callable
from pathlib import Path
import queue

try:
    import customtkinter as ctk
except ImportError as e:
    print(f"Dependência não encontrada: {e}")
    print("Execute: pip install customtkinter")
    import sys
    sys.exit(1)

from ..models import Song, SearchResult, ThemeColors
from ..managers import (
    DataManager, SettingsManager, DownloadManager, 
    SearchManager, PlaylistManager
)
from .player import MusicPlayer
from .events import EventBus


@dataclass
class AppContext:
    """Application context for dependency injection"""
    root: ctk.CTk
    event_bus: EventBus
    colors: ThemeColors
    downloads_dir: Path
    ui_queue: queue.Queue[Callable]
    
    # Managers
    data_manager: DataManager
    settings_manager: SettingsManager
    player: MusicPlayer
    download_manager: DownloadManager
    search_manager: SearchManager
    playlist_manager: PlaylistManager
    
    # Services
    music_service: 'MusicService'
    
    # Data
    feed_items: list[Song] = field(default_factory=list)
    search_results: list[SearchResult] = field(default_factory=list)
    current_view: str = "feed"
    
    # UI References
    view_frames: dict[str, ctk.CTkFrame] = field(default_factory=dict)
    navigation_buttons: dict[str, ctk.CTkButton] = field(default_factory=dict)
    content_container: Optional[ctk.CTkFrame] = None
