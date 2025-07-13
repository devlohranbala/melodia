from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import asyncio
from datetime import datetime

from ..models import Song, SearchResult, PlaylistDict, SettingsDict, AUDIO_EXTENSIONS
from ..managers import DataManager, SettingsManager, SearchManager, DownloadManager, PlaylistManager


class BaseAPIService:
    """Base service class for API services"""
    
    def __init__(self, downloads_dir: Path):
        self.downloads_dir = downloads_dir
        self.downloads_dir.mkdir(exist_ok=True)


class SongService(BaseAPIService):
    """Service for song operations"""
    
    def __init__(self, downloads_dir: Path):
        super().__init__(downloads_dir)
        self.data_manager = DataManager(downloads_dir)
        self._songs_cache: Optional[List[Song]] = None
    
    def _load_songs(self) -> List[Song]:
        """Load songs from data manager"""
        if self._songs_cache is None:
            _, songs = self.data_manager.load_data()
            self._songs_cache = songs
        return self._songs_cache
    
    def _invalidate_cache(self):
        """Invalidate songs cache"""
        self._songs_cache = None
    
    def get_all_songs(self) -> List[Song]:
        """Get all songs"""
        return self._load_songs()
    
    def search_songs(self, query: str) -> List[Song]:
        """Search songs by title or artist"""
        if not query:
            return self.get_all_songs()
        
        query_lower = query.lower().strip()
        songs = self._load_songs()
        
        return [
            song for song in songs
            if query_lower in song.title.lower() or query_lower in song.artist.lower()
        ]
    
    def get_song_by_path(self, file_path: str) -> Optional[Song]:
        """Get song by file path"""
        songs = self._load_songs()
        for song in songs:
            if song.file_path == file_path:
                return song
        return None
    
    def delete_song(self, file_path: str) -> bool:
        """Delete a song"""
        try:
            song = self.get_song_by_path(file_path)
            if not song:
                return False
            
            # Remove physical file
            file_path_obj = Path(song.file_path)
            if file_path_obj.exists():
                file_path_obj.unlink()
            
            # Remove thumbnail if exists
            if song.thumbnail_path:
                thumbnail_path = Path(song.thumbnail_path)
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
            
            # Update data
            playlists, songs = self.data_manager.load_data()
            songs = [s for s in songs if s.file_path != file_path]
            
            # Remove from playlists
            for playlist_name in playlists:
                playlist_songs = playlists[playlist_name].get('songs', [])
                playlists[playlist_name]['songs'] = [
                    s for s in playlist_songs 
                    if isinstance(s, dict) and s.get('file_path') != file_path
                ]
            
            self.data_manager.save_data(playlists, songs)
            self._invalidate_cache()
            
            return True
            
        except Exception as e:
            print(f"Error deleting song: {e}")
            return False
    
    def add_song(self, song: Song) -> bool:
        """Add a new song"""
        try:
            playlists, songs = self.data_manager.load_data()
            
            # Check if song already exists
            if any(existing.file_path == song.file_path for existing in songs):
                return False
            
            songs.append(song)
            
            # Sort by creation time (newest first)
            songs.sort(
                key=lambda x: Path(x.file_path).stat().st_ctime if Path(x.file_path).exists() else 0,
                reverse=True
            )
            
            self.data_manager.save_data(playlists, songs)
            self._invalidate_cache()
            
            return True
            
        except Exception as e:
            print(f"Error adding song: {e}")
            return False
    
    def refresh_songs_from_directory(self) -> List[Song]:
        """Refresh songs by scanning directory"""
        songs = []
        
        if not self.downloads_dir.exists():
            return songs
        
        for file in self.downloads_dir.glob("*"):
            if file.suffix in AUDIO_EXTENSIONS:
                song = self._create_song_from_file(file)
                if song:
                    songs.append(song)
        
        # Sort by creation time (newest first)
        songs.sort(
            key=lambda x: Path(x.file_path).stat().st_ctime,
            reverse=True
        )
        
        # Save updated songs
        playlists, _ = self.data_manager.load_data()
        self.data_manager.save_data(playlists, songs)
        self._invalidate_cache()
        
        return songs
    
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


class PlaylistService(BaseAPIService):
    """Service for playlist operations"""
    
    def __init__(self, downloads_dir: Path):
        super().__init__(downloads_dir)
        self.data_manager = DataManager(downloads_dir)
        self.playlist_manager = PlaylistManager()
        self._load_playlists()
    
    def _load_playlists(self):
        """Load playlists from data manager"""
        playlists, _ = self.data_manager.load_data()
        self.playlist_manager.playlists = playlists
    
    def _save_playlists(self):
        """Save playlists to data manager"""
        _, songs = self.data_manager.load_data()
        self.data_manager.save_data(self.playlist_manager.playlists, songs)
    
    def get_all_playlists(self) -> Dict[str, PlaylistDict]:
        """Get all playlists"""
        return self.playlist_manager.playlists.copy()
    
    def get_playlist(self, name: str) -> Optional[PlaylistDict]:
        """Get a specific playlist"""
        return self.playlist_manager.playlists.get(name)
    
    def create_playlist(self, name: str, description: str = "") -> bool:
        """Create a new playlist"""
        if name in self.playlist_manager.playlists:
            return False
        
        success = self.playlist_manager.create_playlist(name, description)
        if success:
            self._save_playlists()
        return success
    
    def delete_playlist(self, name: str) -> bool:
        """Delete a playlist"""
        if name not in self.playlist_manager.playlists:
            return False
        
        success = self.playlist_manager.delete_playlist(name)
        if success:
            self._save_playlists()
        return success
    
    def add_to_playlist(self, playlist_name: str, song: Song) -> bool:
        """Add song to playlist"""
        success = self.playlist_manager.add_to_playlist(playlist_name, song)
        if success:
            self._save_playlists()
        return success
    
    def remove_from_playlist(self, playlist_name: str, song: Song) -> bool:
        """Remove song from playlist"""
        success = self.playlist_manager.remove_from_playlist(playlist_name, song)
        if success:
            self._save_playlists()
        return success


class SearchService(BaseAPIService):
    """Service for search operations"""
    
    def __init__(self, downloads_dir: Path):
        super().__init__(downloads_dir)
        self.search_manager = SearchManager()
    
    async def search_async(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search for music asynchronously"""
        loop = asyncio.get_event_loop()
        
        def search_sync():
            results = []
            
            def on_result(result):
                results.append(result)
            
            def on_complete():
                pass
            
            def on_error(error):
                print(f"Search error: {error}")
            
            self.search_manager.search(
                query=query,
                on_result=on_result,
                on_complete=on_complete,
                on_error=on_error
            )
            
            # Wait a bit for results
            import time
            time.sleep(2)
            
            return results[:limit]
        
        return await loop.run_in_executor(None, search_sync)


class DownloadService(BaseAPIService):
    """Service for download operations"""
    
    def __init__(self, downloads_dir: Path):
        super().__init__(downloads_dir)
        self.download_manager = DownloadManager(downloads_dir)
        self.data_manager = DataManager(downloads_dir)
    
    async def download_async(self, url: str) -> bool:
        """Download music asynchronously"""
        loop = asyncio.get_event_loop()
        
        def download_sync():
            success = False
            
            def on_complete(song):
                nonlocal success
                if song:
                    # Add song to database
                    try:
                        playlists, songs = self.data_manager.load_data()
                        
                        # Check if song already exists
                        if not any(existing.file_path == song.file_path for existing in songs):
                            songs.append(song)
                            
                            # Sort by creation time (newest first)
                            songs.sort(
                                key=lambda x: Path(x.file_path).stat().st_ctime if Path(x.file_path).exists() else 0,
                                reverse=True
                            )
                            
                            self.data_manager.save_data(playlists, songs)
                        
                        success = True
                    except Exception as e:
                        print(f"Error adding downloaded song: {e}")
                        success = False
            
            def on_error(error):
                print(f"Download error: {error}")
            
            def on_status(status):
                print(f"Download status: {status}")
            
            self.download_manager.download(
                url=url,
                on_complete=on_complete,
                on_error=on_error,
                on_status=on_status
            )
            
            # Wait for download to complete
            import time
            time.sleep(5)  # Adjust based on expected download time
            
            return success
        
        return await loop.run_in_executor(None, download_sync)


class SettingsService(BaseAPIService):
    """Service for settings operations"""
    
    def __init__(self, downloads_dir: Path):
        super().__init__(downloads_dir)
        self.settings_manager = SettingsManager(downloads_dir)
    
    def get_settings(self) -> SettingsDict:
        """Get current settings"""
        return self.settings_manager.load_settings()
    
    def update_settings(self, updates: Dict[str, Any]) -> SettingsDict:
        """Update settings"""
        current_settings = self.settings_manager.load_settings()
        current_settings.update(updates)
        self.settings_manager.save_settings(current_settings)
        return current_settings