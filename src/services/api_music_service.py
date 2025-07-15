from typing import List, Optional
from pathlib import Path

from ..models import Song, SearchResult
from ..api.client import get_api_client, APIClient
from ..api.models import SongResponse, SearchResultResponse
from ..core import Event, AppContext


class APIMusicService:
    """Music service that communicates with the API instead of direct managers"""
    
    def __init__(self, app_context: AppContext):
        self.context = app_context
        self.event_bus = app_context.event_bus
        self.api_client = get_api_client()
        
        # Initialize by syncing with API and local files
        self.refresh_songs_from_directory()
    
    def get_all_songs(self) -> List[Song]:
        """Get all songs from local context (updated to fix feed loading issue)"""
        return self.context.feed_items.copy()
    
    def search_songs(self, query: str) -> List[Song]:
        """Search songs by title or artist via API"""
        try:
            song_responses = self.api_client.get_songs(search=query)
            return [self._song_response_to_song(response) for response in song_responses]
        except Exception as e:
            print(f"Error searching songs via API: {e}")
            return []
    
    def delete_song(self, song: Song) -> bool:
        """Delete a song via API"""
        try:
            success = self.api_client.delete_song(song.file_path)
            if success:
                # Update local context
                self.context.feed_items = [
                    item for item in self.context.feed_items 
                    if item.file_path != song.file_path
                ]
                
                # Remove from all playlists
                for playlist_name in self.context.playlist_manager.playlists:
                    self.context.playlist_manager.remove_from_playlist(playlist_name, song)
                
                # Notify system of changes
                self.event_bus.publish(Event('song_deleted', {'song': song}))
            
            return success
        except Exception as e:
            print(f"Error deleting song via API: {e}")
            return False
    
    def add_song(self, song: Song) -> bool:
        """Add a new song via API"""
        try:
            # For now, we'll update the local context directly
            # In a full implementation, the API would handle this
            if any(existing.file_path == song.file_path for existing in self.context.feed_items):
                return False
            
            self.context.feed_items.append(song)
            
            # Sort by creation time (newest first)
            self.context.feed_items.sort(
                key=lambda x: Path(x.file_path).stat().st_ctime if Path(x.file_path).exists() else 0,
                reverse=True
            )
            
            # Notify system of changes
            self.event_bus.publish(Event('song_added', {'song': song}))
            
            return True
        except Exception as e:
            print(f"Error adding song: {e}")
            return False
    
    def update_song(self, old_song: Song, new_song: Song) -> bool:
        """Update an existing song"""
        try:
            # Find and replace the song in local context
            for i, song in enumerate(self.context.feed_items):
                if song.file_path == old_song.file_path:
                    self.context.feed_items[i] = new_song
                    break
            else:
                return False  # Song not found
            
            # Notify system of changes
            self.event_bus.publish(Event('song_updated', {'old_song': old_song, 'new_song': new_song}))
            
            return True
        except Exception as e:
            print(f"Error updating song: {e}")
            return False
    
    def refresh_songs_from_directory(self) -> None:
        """Refresh songs list by syncing with API and local files"""
        try:
            # Get songs from API to sync with server state
            api_songs = []
            try:
                song_responses = self.api_client.get_songs()
                api_songs = [self._song_response_to_song(response) for response in song_responses]
            except Exception as e:
                print(f"Warning: Could not sync with API: {e}")
            
            # Merge with local context, keeping local additions
            local_paths = {song.file_path for song in self.context.feed_items}
            api_paths = {song.file_path for song in api_songs}
            
            # Keep local songs that aren't in API yet
            merged_songs = list(self.context.feed_items)
            
            # Add API songs that aren't in local context
            for api_song in api_songs:
                if api_song.file_path not in local_paths:
                    merged_songs.append(api_song)
            
            # Sort by creation time (newest first)
            merged_songs.sort(
                key=lambda x: Path(x.file_path).stat().st_ctime if Path(x.file_path).exists() else 0,
                reverse=True
            )
            
            self.context.feed_items = merged_songs
            
            # Notify system of changes
            self.event_bus.publish(Event('songs_refreshed'))
        except Exception as e:
            print(f"Error refreshing songs: {e}")
    
    def get_song_by_path(self, file_path: str) -> Optional[Song]:
        """Get a song by its file path"""
        try:
            response = self.api_client.get_song(file_path)
            return self._song_response_to_song(response)
        except Exception as e:
            print(f"Error getting song by path from API: {e}")
            # Fallback to local search
            for song in self.context.feed_items:
                if song.file_path == file_path:
                    return song
            return None
    
    def confirm_delete_song(self, song: Song) -> bool:
        """Show confirmation dialog and delete song if confirmed"""
        from tkinter import messagebox
        
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
    
    def search_online(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search for music online via API"""
        try:
            search_responses = self.api_client.search_music(query, limit)
            return [self._search_response_to_search_result(response) for response in search_responses]
        except Exception as e:
            print(f"Error searching online via API: {e}")
            return []
    
    def download_music(self, url: str) -> bool:
        """Download music via API"""
        try:
            return self.api_client.download_music(url)
        except Exception as e:
            print(f"Error downloading music via API: {e}")
            return False
    
    def _song_response_to_song(self, response: SongResponse) -> Song:
        """Convert API SongResponse to Song model"""
        return Song(
            title=response.title,
            artist=response.artist,
            file_path=response.file_path,
            date=response.date,
            thumbnail_path=response.thumbnail_path
        )
    
    def _search_response_to_search_result(self, response: SearchResultResponse) -> SearchResult:
        """Convert API SearchResultResponse to SearchResult model"""
        return SearchResult(
            title=response.title,
            artist=response.artist,
            url=response.url,
            duration=response.duration,
            view_count=response.view_count
        )