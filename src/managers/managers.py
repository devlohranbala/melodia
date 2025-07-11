import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from functools import cache

try:
    import yt_dlp
except ImportError as e:
    print(f"Dependência não encontrada: {e}")
    print("Execute: pip install yt-dlp")
    import sys
    sys.exit(1)

from ..models import Song, SearchResult, PlaylistDict, SettingsDict, AUDIO_EXTENSIONS, DEFAULT_VOLUME, DEFAULT_CROSSFADE_ENABLED, DEFAULT_CROSSFADE_DURATION, DEFAULT_AUDIO_OUTPUT

# ====================
# Base Managers
# ====================

class ThreadedManager:
    """Base class for managers that handle threading"""
    def __init__(self) -> None:
        self._shutdown = False
        self._active_threads: list[threading.Thread] = []
        
    def shutdown(self) -> None:
        """Shutdown all active threads"""
        self._shutdown = True
        for thread in self._active_threads[:]:
            if thread.is_alive():
                thread.join(timeout=1.0)
                
    def _run_threaded(self, target: Callable) -> None:
        """Run function in thread with management"""
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        self._active_threads.append(thread)
        self._active_threads = [t for t in self._active_threads if t.is_alive()]

class FileManager:
    """Base class for file-based managers"""
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        
    def _safe_json_write(self, file_path: Path, data: dict) -> None:
        """Safely write JSON data"""
        try:
            file_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        except OSError as e:
            print(f"Erro ao salvar em {file_path}: {e}")
            
    def _safe_json_read(self, file_path: Path, default: dict) -> dict:
        """Safely read JSON data"""
        try:
            if file_path.exists():
                return json.loads(file_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as e:
            print(f"Erro ao carregar de {file_path}: {e}")
        return default

# ====================
# Managers
# ====================

class DataManager(FileManager):
    """Enhanced data manager with modern Python features"""
    def __init__(self, downloads_dir: str | Path) -> None:
        super().__init__(downloads_dir)
        self.data_file = self.base_dir / 'music_data.json'
        
    def save_data(self, playlists: dict[str, PlaylistDict], feed_items: list[Song]) -> None:
        """Save data with better error handling"""
        data = {
            'playlists': playlists,
            'feed_items': [song.to_dict() for song in feed_items]
        }
        self._safe_json_write(self.data_file, data)
            
    def load_data(self) -> tuple[dict[str, PlaylistDict], list[Song]]:
        """Load data with pattern matching"""
        data = self._safe_json_read(self.data_file, {})
        
        match data:
            case {'playlists': dict() as playlists, 'feed_items': list() as feed_items}:
                return (
                    playlists,
                    [Song.from_dict(item) for item in feed_items]
                )
            case _:
                return {}, []

class SettingsManager(FileManager):
    """Settings manager with modern defaults"""
    def __init__(self, downloads_dir: str | Path) -> None:
        super().__init__(downloads_dir)
        self.settings_file = self.base_dir / 'settings.json'
        self.default_settings: SettingsDict = {
            'theme': 'dark',
            'color_theme': 'blue',
            'default_volume': DEFAULT_VOLUME,
            'downloads_dir': str(downloads_dir),
            'crossfade_enabled': DEFAULT_CROSSFADE_ENABLED,
            'crossfade_duration': DEFAULT_CROSSFADE_DURATION,
            'audio_output': DEFAULT_AUDIO_OUTPUT
        }
        
    def save_settings(self, settings: SettingsDict) -> None:
        """Save settings with Path API"""
        self._safe_json_write(self.settings_file, settings)
            
    def load_settings(self) -> SettingsDict:
        """Load settings with dict union operator"""
        settings = self._safe_json_read(self.settings_file, {})
        return self.default_settings | settings

class BaseYtdlManager(ThreadedManager):
    """Base manager for yt-dlp operations"""
    
    @staticmethod
    def extract_artist_title(info: dict[str, any]) -> tuple[str, str]:
        """Extract artist and title from metadata only"""
        title = info.get('title', 'Título Desconhecido')
        artist = info.get('artist') or info.get('creator') or info.get('uploader', 'Artista Desconhecido')
        return title, artist
        
    def _execute_async(
        self,
        operation: Callable,
        on_complete: Callable,
        on_error: Callable[[str], None],
        on_status: Callable[[str], None]
    ) -> None:
        """Execute async operation with callbacks"""
        def execute():
            if self._shutdown:
                return
            try:
                result = operation()
                if not self._shutdown:
                    on_complete(result)
            except Exception as e:
                if not self._shutdown:
                    on_error(str(e))
                    
        self._run_threaded(execute)

class DownloadManager(BaseYtdlManager):
    """Download manager with modern threading"""
    def __init__(self, downloads_dir: str | Path) -> None:
        super().__init__()
        self.downloads_dir = Path(downloads_dir)
        
    @staticmethod
    @cache
    def create_safe_filename(artist: str, title: str) -> str:
        """Create safe filename with caching"""
        filename = f"{artist} - {title}"
        return "".join(c for c in filename if c not in '<>:"/\\|?*')
        
    def find_downloaded_file(self, title: str) -> Optional[Path]:
        """Find downloaded file with Path API"""
        try:
            safe_title = "".join(c for c in title if c not in '<>:"/\\|?*')
            
            # Try exact match
            for ext in AUDIO_EXTENSIONS:
                if (exact_path := self.downloads_dir / f"{safe_title}{ext}").exists():
                    return exact_path
                    
            # Try similar match
            for file in self.downloads_dir.glob("*"):
                if file.suffix in AUDIO_EXTENSIONS:
                    file_title = file.stem
                    if (safe_title.lower() in file_title.lower() or 
                        file_title.lower() in safe_title.lower()):
                        return file
                        
            # Try most recent file
            recent_files = [
                f for f in self.downloads_dir.glob("*")
                if f.suffix in AUDIO_EXTENSIONS and
                f.stat().st_ctime > (time.time() - 120)
            ]
            
            if recent_files:
                return max(recent_files, key=lambda f: f.stat().st_ctime)
                
        except Exception as e:
            print(f"Erro ao buscar arquivo: {e}")
            
        return None
    
    def find_thumbnail_file(self, title: str) -> Optional[Path]:
        """Find downloaded thumbnail file"""
        try:
            safe_title = "".join(c for c in title if c not in '<>:"/\\|?*')
            
            # Common thumbnail extensions
            thumbnail_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            
            # Try exact match
            for ext in thumbnail_extensions:
                if (exact_path := self.downloads_dir / f"{safe_title}{ext}").exists():
                    return exact_path
                    
            # Try similar match
            for file in self.downloads_dir.glob("*"):
                if file.suffix.lower() in thumbnail_extensions:
                    file_title = file.stem
                    if (safe_title.lower() in file_title.lower() or 
                        file_title.lower() in safe_title.lower()):
                        return file
                        
        except Exception as e:
            print(f"Erro ao buscar thumbnail: {e}")
            
        return None
            
    def download_music(
        self, 
        url: str, 
        on_complete: Callable[[Song], None],
        on_error: Callable[[str], None],
        on_status: Callable[[str], None]
    ) -> None:
        """Download music with modern threading"""
        def download():
            on_status("⬇ Baixando...")
            
            # Get metadata
            ydl_opts_info = {'quiet': True, 'no_warnings': True}
            
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                
            # Extract information
            title, artist = self.extract_artist_title(info)
            safe_filename = self.create_safe_filename(artist, title)
            
            # Download audio and thumbnail
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(self.downloads_dir / f'{safe_filename}.%(ext)s'),
                'writethumbnail': True,
                'writeinfojson': False,
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            if not (file_path := self.find_downloaded_file(safe_filename)):
                raise Exception("Arquivo não encontrado após download")
            
            # Find thumbnail file
            thumbnail_path = self.find_thumbnail_file(safe_filename)
                
            return Song(
                title=title,
                artist=artist,
                file_path=str(file_path),
                date=datetime.now().strftime("%d/%m/%Y"),
                thumbnail_path=str(thumbnail_path) if thumbnail_path else ""
            )
            
        self._execute_async(download, on_complete, on_error, on_status)

class SearchManager(BaseYtdlManager):
    """Search manager with modern features"""
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration with divmod"""
        if not seconds:
            return "0:00"
        minutes, seconds = divmod(int(seconds), 60)
        return f"{minutes}:{seconds:02d}"
        
    def search_music(
        self,
        query: str,
        on_results: Callable[[list[SearchResult]], None],
        on_error: Callable[[str], None],
        on_status: Callable[[str], None]
    ) -> None:
        """Search music with pattern matching"""
        def search():
            on_status("🔍 Buscando...")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(f"ytsearch10:{query}", download=False)
                
                search_results: list[SearchResult] = []
                
                if results and 'entries' in results:
                    for entry in results['entries']:
                        if not entry:
                            continue
                            
                        # Extract URL
                        match (entry.get('id', ''), entry.get('url', '')):
                            case (video_id, _) if video_id and not entry.get('url', '').startswith('http'):
                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                            case (_, video_url) if video_url and not video_url.startswith('http'):
                                video_url = f"https://www.youtube.com/watch?v={video_url}"
                            case (_, video_url):
                                pass
                                
                        # Extract info
                        title, artist = self.extract_artist_title(entry)
                                
                        result = SearchResult(
                            title=title,
                            artist=artist,
                            url=video_url,
                            duration=self.format_duration(entry.get('duration', 0)),
                            view_count=entry.get('view_count', 0)
                        )
                        search_results.append(result)
                        
                return search_results
                
        self._execute_async(search, on_results, on_error, on_status)

class PlaylistManager:
    """Playlist manager with modern dict operations"""
    def __init__(self) -> None:
        self.playlists: dict[str, PlaylistDict] = {}
        
    def create_playlist(self, name: str) -> bool:
        """Create new playlist"""
        if name and name not in self.playlists:
            self.playlists[name] = {
                'songs': [],
                'created': datetime.now().isoformat()
            }
            return True
        return False
        
    def add_to_playlist(self, playlist_name: str, song: Song) -> bool:
        """Add song to playlist with any()"""
        if playlist_name not in self.playlists:
            return False
            
        playlist = self.playlists[playlist_name]
        
        # Check if already exists
        if any(s['file_path'] == song.file_path for s in playlist['songs']):
            return False
            
        playlist['songs'].append(song.to_dict())
        return True
        
    def remove_from_playlist(self, playlist_name: str, song: Song) -> None:
        """Remove song from playlist"""
        if playlist := self.playlists.get(playlist_name):
            playlist['songs'] = [
                s for s in playlist['songs'] 
                if s['file_path'] != song.file_path
            ]
            
    def delete_playlist(self, name: str) -> None:
        """Delete playlist"""
        self.playlists.pop(name, None)
            
    def get_playlist_songs(self, name: str) -> list[Song]:
        """Get playlist songs"""
        if playlist := self.playlists.get(name):
            return [Song.from_dict(s) for s in playlist['songs']]
        return []