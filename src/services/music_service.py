from pathlib import Path
from datetime import datetime
from typing import Optional, List
from tkinter import messagebox

from ..models import Song, AUDIO_EXTENSIONS
from ..core import Event, AppContext


class MusicService:
    """Service responsible for music domain operations"""
    
    def __init__(self, app_context: AppContext):
        self.context = app_context
        self.event_bus = app_context.event_bus
    
    def get_all_songs(self) -> List[Song]:
        """Get all songs from feed"""
        return self.context.feed_items.copy()
    
    def search_songs(self, query: str) -> List[Song]:
        """Search songs by title or artist"""
        if not query:
            return self.get_all_songs()
        
        query_lower = query.lower().strip()
        return [
            song for song in self.context.feed_items
            if query_lower in song.title.lower() or query_lower in song.artist.lower()
        ]
    
    def delete_song(self, song: Song) -> bool:
        """Delete a song from the system"""
        try:
            # Stop if currently playing
            if (
                self.context.player.current_song and 
                self.context.player.current_song.file_path == song.file_path
            ):
                self.context.player.pause()
                self.context.player.current_song = None
            
            # Remove physical file
            file_path = Path(song.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Remove thumbnail if exists
            if song.thumbnail_path:
                thumbnail_path = Path(song.thumbnail_path)
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
            
            # Remove from feed items
            self.context.feed_items = [
                item for item in self.context.feed_items 
                if item.file_path != song.file_path
            ]
            
            # Remove from all playlists
            for playlist_name in self.context.playlist_manager.playlists:
                self.context.playlist_manager.remove_from_playlist(playlist_name, song)
            
            # Notify system of changes
            self.event_bus.publish(Event('save_data'))
            self.event_bus.publish(Event('song_deleted', {'song': song}))
            
            return True
            
        except Exception as e:
            print(f"Error deleting song: {e}")
            return False
    
    def add_song(self, song: Song) -> bool:
        """Add a new song to the system"""
        try:
            # Check if song already exists
            if any(existing.file_path == song.file_path for existing in self.context.feed_items):
                return False
            
            # Add to feed items
            self.context.feed_items.append(song)
            
            # Sort by creation time (newest first)
            self.context.feed_items.sort(
                key=lambda x: Path(x.file_path).stat().st_ctime,
                reverse=True
            )
            
            # Notify system of changes
            self.event_bus.publish(Event('save_data'))
            self.event_bus.publish(Event('song_added', {'song': song}))
            
            return True
            
        except Exception as e:
            print(f"Error adding song: {e}")
            return False
    
    def update_song(self, old_song: Song, new_song: Song) -> bool:
        """Update an existing song"""
        try:
            # Find and replace the song
            for i, song in enumerate(self.context.feed_items):
                if song.file_path == old_song.file_path:
                    self.context.feed_items[i] = new_song
                    break
            else:
                return False  # Song not found
            
            # Notify system of changes
            self.event_bus.publish(Event('save_data'))
            self.event_bus.publish(Event('song_updated', {'old_song': old_song, 'new_song': new_song}))
            
            return True
            
        except Exception as e:
            print(f"Error updating song: {e}")
            return False
    
    def refresh_songs_from_directory(self) -> None:
        """Refresh songs list by scanning the downloads directory"""
        self.context.feed_items = []
        
        if not self.context.downloads_dir.exists():
            return
        
        for file in self.context.downloads_dir.glob("*"):
            if file.suffix in AUDIO_EXTENSIONS:
                song = self._create_song_from_file(file)
                if song:
                    self.context.feed_items.append(song)
        
        # Sort by creation time (newest first)
        self.context.feed_items.sort(
            key=lambda x: Path(x.file_path).stat().st_ctime,
            reverse=True
        )
        
        # Note: No event publication here to avoid recursion
        # Controllers should call this method and handle UI updates directly
    
    def _create_song_from_file(self, file_path: Path) -> Optional[Song]:
        """Create a Song object from a file path"""
        try:
            filename_without_ext = file_path.stem
            
            # Extract artist and title from filename
            if ' - ' in filename_without_ext:
                artist, title = filename_without_ext.split(' - ', 1)
                artist = artist.strip().replace('_', ' ')
                title = title.strip().replace('_', ' ')
            else:
                title = filename_without_ext.replace('_', ' ').strip()
                artist = 'Artista Desconhecido'
            
            # Find thumbnail
            thumbnail_path = ""
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                thumbnail_file = file_path.with_suffix(ext)
                if thumbnail_file.exists():
                    thumbnail_path = str(thumbnail_file)
                    break
            
            return Song(
                title=title,
                artist=artist,
                file_path=str(file_path),
                date=datetime.fromtimestamp(file_path.stat().st_ctime).strftime("%d/%m/%Y"),
                thumbnail_path=thumbnail_path
            )
            
        except Exception as e:
            print(f"Error creating song from file {file_path}: {e}")
            return None
    
    def get_song_by_path(self, file_path: str) -> Optional[Song]:
        """Get a song by its file path"""
        for song in self.context.feed_items:
            if song.file_path == file_path:
                return song
        return None
    
    def confirm_delete_song(self, song: Song) -> bool:
        """Show confirmation dialog and delete song if confirmed"""
        if messagebox.askyesno(
            "Confirmar Exclusão",
            f"Excluir '{song.title}' permanentemente?\n\nEsta ação não pode ser desfeita."
        ):
            if self.delete_song(song):
                messagebox.showinfo("Sucesso", "Música excluída com sucesso!")
                return True
            else:
                messagebox.showerror("Erro", "Erro ao excluir música.")
        return False