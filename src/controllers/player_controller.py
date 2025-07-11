from typing import Optional
from contextlib import suppress
import customtkinter as ctk

from ..models import (
    Song, DEFAULT_VOLUME, POSITION_UPDATE_INTERVAL
)
from ..core import Event, AppContext
from .base_controller import BaseController


class PlayerController(BaseController):
    """Controller for music player functionality"""
    
    def __init__(self, app_context: AppContext):
        super().__init__(app_context)
        self._position_update_id: Optional[str] = None
        self.current_index: int = 0
        
        # UI References
        self.play_btn: Optional[ctk.CTkButton] = None
        self.position_slider: Optional[ctk.CTkSlider] = None
        self.position_label: Optional[ctk.CTkLabel] = None
        self.duration_label: Optional[ctk.CTkLabel] = None
        self.volume: Optional[ctk.CTkSlider] = None
        self.volume_label: Optional[ctk.CTkLabel] = None
        self.now_playing: Optional[ctk.CTkLabel] = None
        self.artist_label: Optional[ctk.CTkLabel] = None
    
    def initialize(self) -> None:
        """Initialize player controller"""
        self._setup_player_callbacks()
        self._setup_event_handlers()
        self.start_position_timer()
    
    def cleanup(self) -> None:
        """Cleanup player resources"""
        self.stop_position_timer()
        if self.context.player.is_playing:
            self.context.player.pause()
    
    def _setup_player_callbacks(self) -> None:
        """Setup player callbacks"""
        self.context.player.set_callback('on_play', self._on_play)
        self.context.player.set_callback('on_pause', self._on_pause)
        self.context.player.set_callback('on_song_change', self._on_song_change)
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers"""
        self.event_bus.subscribe('play_song', self._handle_play_song)
        self.event_bus.subscribe('play_playlist', self._handle_play_playlist)
    
    def _handle_play_song(self, event: Event) -> None:
        """Handle play song event"""
        if song := event.data.get('song'):
            # Clear playlist context when playing individual song
            self.context.player.current_playlist = None
            self.play_song(song)
    
    def _handle_play_playlist(self, event: Event) -> None:
        """Handle play playlist event"""
        if (name := event.data.get('name')) and (songs := event.data.get('songs')):
            self.context.player.current_playlist = name
            self.play_song(songs[0])
    
    def create_player_ui(self, parent: ctk.CTkFrame) -> None:
        """Create modern player UI"""
        player_frame = ctk.CTkFrame(parent, corner_radius=15)
        player_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        inner = ctk.CTkFrame(player_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Song information
        self.now_playing = ctk.CTkLabel(
            inner,
            text="Nenhuma música tocando",
            font=ctk.CTkFont(size=16, weight="bold"),
            wraplength=250
        )
        self.now_playing.pack()
        
        self.artist_label = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.artist_label.pack(pady=(5, 15))
        
        # Progress bar
        progress_frame = ctk.CTkFrame(inner, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(0, 15))
        
        self.position_label = ctk.CTkLabel(
            progress_frame,
            text="0:00",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.position_label.pack(side="left")
        
        self.position_slider = ctk.CTkSlider(
            progress_frame,
            from_=0,
            to=100,
            command=self.seek_position
        )
        self.position_slider.pack(side="left", fill="x", expand=True, padx=10)
        self.position_slider.bind('<Button-1>', self._on_slider_press)
        self.position_slider.bind('<ButtonRelease-1>', self._on_slider_release)
        
        self.duration_label = ctk.CTkLabel(
            progress_frame,
            text="0:00",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.duration_label.pack(side="right")
        
        # Playback controls
        controls = ctk.CTkFrame(inner, fg_color="transparent")
        controls.pack(pady=(0, 15))
        
        ctk.CTkButton(
            controls,
            text="⏮",
            width=40,
            height=40,
            command=self.prev_song,
            font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=5)
        
        self.play_btn = ctk.CTkButton(
            controls,
            text="▶",
            width=50,
            height=50,
            command=self.toggle_play,
            font=ctk.CTkFont(size=20)
        )
        self.play_btn.pack(side="left", padx=10)
        
        ctk.CTkButton(
            controls,
            text="⏭",
            width=40,
            height=40,
            command=self.next_song,
            font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=5)
        
        # Volume control
        vol_frame = ctk.CTkFrame(inner, fg_color="transparent")
        vol_frame.pack(fill="x")
        
        ctk.CTkLabel(
            vol_frame,
            text="🔊",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 10))
        
        self.volume = ctk.CTkSlider(
            vol_frame,
            from_=0,
            to=100,
            command=self.change_volume
        )
        self.volume.set(DEFAULT_VOLUME)
        self.volume.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.volume_label = ctk.CTkLabel(
            vol_frame,
            text=f"{DEFAULT_VOLUME}%",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            width=40
        )
        self.volume_label.pack(side="right")
    
    def play_song(self, song: Song) -> None:
        """Play song"""
        # Only clear playlist if not playing from a playlist context
        if not self.context.player.current_playlist:
            self.context.player.current_playlist = None
        self.context.player.play_song(song)
        self._update_current_index(song)
    
    def toggle_play(self) -> None:
        """Toggle play/pause"""
        self.context.player.toggle_play()
    
    def prev_song(self) -> None:
        """Previous song"""
        self._navigate_song(-1)
    
    def next_song(self) -> None:
        """Next song"""
        self._navigate_song(1)
    
    def seek_position(self, value: float) -> None:
        """Seek position"""
        if self.context.player.current_source and not self.context.player.is_seeking:
            with suppress(Exception):
                if duration := self.context.player.duration:
                    position = (value / 100) * duration
                    self.context.player.seek(position)
    
    def change_volume(self, value: float) -> None:
        """Change volume"""
        volume = value / 100
        self.context.player.set_volume(volume)
        if self.volume_label:
            self.volume_label.configure(text=f"{int(value)}%")
    
    def _on_play(self) -> None:
        """Callback when music starts playing"""
        def update():
            if self.play_btn:
                self.play_btn.configure(text="⏸")
            if not self._position_update_id:
                self.update_position_timer()
        self.schedule_ui_update(update)
    
    def _on_pause(self) -> None:
        """Callback when music is paused"""
        def update():
            if self.play_btn:
                self.play_btn.configure(text="▶")
            self.stop_position_timer()
        self.schedule_ui_update(update)
    
    def _on_song_change(self, song: Song) -> None:
        """Callback when song changes"""
        def update():
            with suppress(Exception):
                if self.now_playing and self.now_playing.winfo_exists():
                    self.now_playing.configure(text=song.title)
                if self.artist_label and self.artist_label.winfo_exists():
                    self.artist_label.configure(text=song.artist)
        self.schedule_ui_update(update)
    
    def _navigate_song(self, direction: int) -> None:
        """Navigate to prev/next song"""
        match (self.context.player.current_playlist, self.context.player.current_song):
            case (str() as playlist_name, Song() as current_song):
                songs_list = self.context.playlist_manager.get_playlist_songs(playlist_name)
            case (None, Song() as current_song) if self.context.feed_items:
                songs_list = self.context.feed_items
            case _:
                return
        
        if songs_list:
            with suppress(Exception):
                current_index = next(
                    (i for i, song in enumerate(songs_list) 
                     if song.file_path == current_song.file_path),
                    -1
                )
                
                if current_index != -1:
                    new_index = (current_index + direction) % len(songs_list)
                    self.play_song(songs_list[new_index])
    
    def _update_current_index(self, song: Song) -> None:
        """Update current index based on the song being played"""
        try:
            # Check if we're playing from a playlist
            if self.context.player.current_playlist:
                playlist_songs = self.context.playlist_manager.get_playlist_songs(self.context.player.current_playlist)
                for i, playlist_song in enumerate(playlist_songs):
                    if playlist_song.file_path == song.file_path:
                        self.current_index = i
                        break
                else:
                    self.current_index = 0
            else:
                # Playing from feed
                for i, feed_song in enumerate(self.context.feed_items):
                    if feed_song.file_path == song.file_path:
                        self.current_index = i
                        break
                else:
                    self.current_index = 0
        except Exception:
            self.current_index = 0
    
    def _on_slider_press(self, event) -> None:
        """Slider press event"""
        self.context.player.is_seeking = True
    
    def _on_slider_release(self, event) -> None:
        """Slider release event"""
        self.context.player.is_seeking = False
        if self.context.player.current_source and self.position_slider:
            with suppress(Exception):
                if duration := self.context.player.duration:
                    value = self.position_slider.get()
                    position = (value / 100) * duration
                    self.context.player.seek(position)
    
    def start_position_timer(self) -> None:
        """Start position timer"""
        if not self._position_update_id and self.context.player.is_playing and self.context.player.current_source:
            self.update_position_timer()
    
    def stop_position_timer(self) -> None:
        """Stop position timer"""
        if self._position_update_id:
            self.root.after_cancel(self._position_update_id)
            self._position_update_id = None
    
    def update_position_timer(self) -> None:
        """Update position timer"""
        with suppress(Exception):
            if (
                self.context.player.current_source and 
                self.context.player.is_playing and 
                not self.context.player.is_seeking
            ):
                position = self.context.player.position
                duration = self.context.player.duration
                
                if duration and duration > 0:
                    # Update slider
                    progress = (position / duration) * 100
                    if self.position_slider:
                        self.position_slider.set(progress)
                    
                    # Update labels
                    pos_min, pos_sec = divmod(int(position), 60)
                    dur_min, dur_sec = divmod(int(duration), 60)
                    
                    if self.position_label:
                        self.position_label.configure(text=f"{pos_min}:{pos_sec:02d}")
                    if self.duration_label:
                        self.duration_label.configure(text=f"{dur_min}:{dur_sec:02d}")
                    
                    # Check for crossfade or song end
                    # Get current song list (playlist or feed)
                    current_songs = []
                    if self.context.player.current_playlist:
                        current_songs = self.context.playlist_manager.get_playlist_songs(self.context.player.current_playlist)
                    else:
                        current_songs = self.context.feed_items
                    
                    if (self.context.player.crossfade_enabled and 
                        not self.context.player.is_crossfading and 
                        self.context.player.crossfade_duration > 0 and
                        position >= duration - self.context.player.crossfade_duration):
                        if self.current_index < len(current_songs) - 1:
                            self._trigger_auto_crossfade()
                    elif position >= duration - 0.1:
                        if self.current_index < len(current_songs) - 1:
                            self.next_song()
                        else:
                            self.context.player.pause()
                            self.context.player.is_playing = False
                            self._on_pause()
                            self.context.player.seek(0)
                            if self.position_slider:
                                self.position_slider.set(0)
                            if self.position_label:
                                self.position_label.configure(text="0:00")
                            self.stop_position_timer()
        
        # Schedule next update
        if self.context.player.is_playing and self.context.player.current_source:
            self._position_update_id = self.root.after(POSITION_UPDATE_INTERVAL, self.update_position_timer)
        else:
            self._position_update_id = None
    
    def _trigger_auto_crossfade(self) -> None:
        """Trigger automatic crossfade to next song"""
        # Get current song list (playlist or feed)
        current_songs = []
        if self.context.player.current_playlist:
            current_songs = self.context.playlist_manager.get_playlist_songs(self.context.player.current_playlist)
        else:
            current_songs = self.context.feed_items
            
        if self.current_index < len(current_songs) - 1:
            next_song = current_songs[self.current_index + 1]
            self.context.player.play_song(next_song)
            self.current_index += 1