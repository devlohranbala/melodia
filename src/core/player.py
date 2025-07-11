from typing import Optional, Callable
from contextlib import suppress
from pathlib import Path

try:
    import pyglet
except ImportError as e:
    print(f"Dependência não encontrada: {e}")
    print("Execute: pip install pyglet")
    import sys
    sys.exit(1)

from ..models import Song, DEFAULT_VOLUME, DEFAULT_CROSSFADE_ENABLED, DEFAULT_CROSSFADE_DURATION

# Configure pyglet
pyglet.options['audio'] = ('openal', 'pulse', 'directsound', 'silent')

class MusicPlayer:
    """Enhanced music player with weakref callbacks"""
    def __init__(self) -> None:
        self.player = pyglet.media.Player()
        self.player.volume = DEFAULT_VOLUME / 100
        self.current_song: Optional[Song] = None
        self.current_source = None
        self.is_playing: bool = False
        self.is_seeking: bool = False
        self.current_playlist: Optional[str] = None
        self._callbacks: dict[str, Callable] = {}
        
        # Crossfade properties
        self.crossfade_enabled: bool = DEFAULT_CROSSFADE_ENABLED
        self.crossfade_duration: int = DEFAULT_CROSSFADE_DURATION
        self.next_player: Optional[pyglet.media.Player] = None
        self.is_crossfading: bool = False
        self.crossfade_start_time: Optional[float] = None
        self.original_volume: float = DEFAULT_VOLUME / 100
        self._crossfade_timer_id: Optional[str] = None
        self._root_ref: Optional[object] = None  # Reference to tkinter root for timer
        
    def set_callback(self, name: str, callback: Callable) -> None:
        """Set callback"""
        self._callbacks[name] = callback
        
    def _call_callback(self, name: str, *args) -> None:
        """Call callback if it exists"""
        if callback := self._callbacks.get(name):
            with suppress(Exception):
                callback(*args)
            
    def play_song(self, song: Song) -> None:
        """Play song with crossfade support"""
        try:
            if (path := Path(song.file_path)).exists():
                source = pyglet.media.load(str(path))
                
                # Check crossfade conditions
                
                # If crossfade is enabled and there's a current song playing
                if (self.crossfade_enabled and 
                    self.current_song and 
                    self.is_playing and 
                    self.crossfade_duration > 0):
                    self._start_crossfade(source, song)
                else:
                    # Normal playback without crossfade
                    if self.player.playing:
                        self.player.pause()
                        
                    while self.player.source:
                        self.player.next_source()
                        
                    self.player.queue(source)
                    self.player.play()
                    
                    self.current_song = song
                    self.current_source = source
                    self.is_playing = True
                    
                    self._call_callback('on_song_change', song)
                    self._call_callback('on_play')
                    
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erro", f"Erro ao reproduzir: {e}")
            
    def toggle_play(self) -> None:
        """Toggle play/pause with match statement"""
        match self.is_playing:
            case True:
                self.pause()
            case False:
                self.play()
                
    def play(self) -> None:
        """Play with callback"""
        self.player.play()
        self.is_playing = True
        self._call_callback('on_play')
            
    def pause(self) -> None:
        """Pause with callback"""
        self.player.pause()
        self.is_playing = False
        self._call_callback('on_pause')
            
    def set_volume(self, volume: float) -> None:
        """Set volume (0-1)"""
        self.player.volume = volume
        # Update original volume for crossfade calculations
        if not self.is_crossfading:
            self.original_volume = volume
        else:
            # If crossfading, update the original volume but maintain current fade ratios
            self.original_volume = volume
        
    def seek(self, position: float) -> None:
        """Seek position with suppress"""
        if self.player.source:
            with suppress(Exception):
                self.player.seek(position)
                
    @property
    def position(self) -> float:
        """Get current position"""
        return self.player.time if self.player.source else 0
        
    @property
    def duration(self) -> float:
        """Get duration"""
        return self.player.source.duration if self.player.source else 0
        
    def _start_crossfade(self, next_source, next_song: Song) -> None:
        """Start crossfade between current and next song"""
        try:
            import time
            
            # Store original volume before crossfade
            self.original_volume = self.player.volume
            
            # Create a new player for the next song
            self.next_player = pyglet.media.Player()
            self.next_player.volume = 0.0  # Start with volume at 0
            self.next_player.queue(next_source)
            self.next_player.play()
            
            # Mark crossfade as started
            self.is_crossfading = True
            self.crossfade_start_time = time.time()  # Use real time instead of player time
            
            # Store next song info
            self._next_song = next_song
            self._next_source = next_source
            
            # Start crossfade update timer (50ms for smooth transitions)
            self._start_crossfade_timer()
            
            # Crossfade started successfully
            
        except Exception as e:
            # Fallback to normal playback on crossfade error
            # Fallback to normal playback
            self._finish_crossfade()
            
    def _update_crossfade(self) -> None:
        """Update crossfade volumes"""
        if not self.is_crossfading or not self.next_player:
            return
            
        try:
            import time
            current_time = time.time()
            elapsed = current_time - self.crossfade_start_time
            progress = min(elapsed / self.crossfade_duration, 1.0)
            
            # Calculate volumes using equal-power crossfade curve
            import math
            fade_out_volume = math.cos(progress * math.pi / 2) ** 2
            fade_in_volume = math.sin(progress * math.pi / 2) ** 2
            
            # Apply volumes using the preserved original volume
            self.player.volume = self.original_volume * fade_out_volume
            self.next_player.volume = self.original_volume * fade_in_volume
            
            # Track progress for completion check
            
            # Check if crossfade is complete
            if progress >= 1.0:
                self._finish_crossfade()
                
        except Exception as e:
            # Handle crossfade update error
            self._finish_crossfade()
            
    def _start_crossfade_timer(self) -> None:
        """Start the crossfade update timer"""
        if self._root_ref:
            self._crossfade_timer_id = self._root_ref.after(50, self._crossfade_timer_callback)
        # Timer will not start without root reference
    
    def _crossfade_timer_callback(self) -> None:
        """Crossfade timer callback"""
        if self.is_crossfading:
            self._update_crossfade()
            # Schedule next update
            if self.is_crossfading:  # Check again in case crossfade finished
                self._crossfade_timer_id = self._root_ref.after(50, self._crossfade_timer_callback)
        else:
            self._crossfade_timer_id = None
    
    def _stop_crossfade_timer(self) -> None:
        """Stop the crossfade timer"""
        if self._crossfade_timer_id and self._root_ref:
            self._root_ref.after_cancel(self._crossfade_timer_id)
            self._crossfade_timer_id = None
    
    def set_root_reference(self, root) -> None:
        """Set reference to tkinter root for timer management"""
        self._root_ref = root
    
    def _finish_crossfade(self) -> None:
        """Finish crossfade and switch to next song"""
        try:
            # Stop crossfade timer first
            self._stop_crossfade_timer()
            
            if self.next_player:
                # Finishing crossfade transition
                
                # Stop current player
                if self.player.playing:
                    self.player.pause()
                    
                while self.player.source:
                    self.player.next_source()
                
                # Switch players and restore original volume
                self.player = self.next_player
                self.player.volume = self.original_volume
                
                # Update current song info
                if hasattr(self, '_next_song'):
                    self.current_song = self._next_song
                    self.current_source = self._next_source
                    # Ensure is_playing state is maintained
                    self.is_playing = True
                    self._call_callback('on_song_change', self.current_song)
                    self._call_callback('on_play')  # Notify that playback is active
                
                # Crossfade completed successfully
                
                # Clean up
                self.next_player = None
                self.is_crossfading = False
                self.crossfade_start_time = None
                
                if hasattr(self, '_next_song'):
                    delattr(self, '_next_song')
                if hasattr(self, '_next_source'):
                    delattr(self, '_next_source')
                if hasattr(self, '_last_progress_debug'):
                    delattr(self, '_last_progress_debug')
                    
        except Exception as e:
            # Handle crossfade finish error
            self.is_crossfading = False
            self.crossfade_start_time = None
            self._stop_crossfade_timer()