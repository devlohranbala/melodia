from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Optional
import uvicorn
import json
from datetime import datetime

from .models import (
    SongResponse, PlaylistResponse, SearchResultResponse,
    CreatePlaylistRequest, AddToPlaylistRequest, SettingsResponse,
    UpdateSettingsRequest, DownloadRequest
)
from .services import (
    SongService, PlaylistService, SearchService,
    DownloadService, SettingsService
)
from ..models import Song, SearchResult


class MusicAPI:
    """Main API class for the music application"""
    
    def __init__(self, downloads_dir: Path):
        self.app = FastAPI(
            title="Melodia Music API",
            description="API for Melodia Music Player",
            version="1.0.0"
        )
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize services
        self.downloads_dir = downloads_dir
        self.song_service = SongService(downloads_dir)
        self.playlist_service = PlaylistService(downloads_dir)
        self.search_service = SearchService(downloads_dir)
        self.download_service = DownloadService(downloads_dir)
        self.settings_service = SettingsService(downloads_dir)
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        # Songs endpoints
        @self.app.get("/api/songs", response_model=List[SongResponse])
        async def get_songs(search: Optional[str] = None):
            """Get all songs or search songs"""
            if search:
                songs = self.song_service.search_songs(search)
            else:
                songs = self.song_service.get_all_songs()
            return [SongResponse.from_song(song) for song in songs]
        
        @self.app.get("/api/songs/{song_id}", response_model=SongResponse)
        async def get_song(song_id: str):
            """Get a specific song by ID (file path)"""
            song = self.song_service.get_song_by_path(song_id)
            if not song:
                raise HTTPException(status_code=404, detail="Song not found")
            return SongResponse.from_song(song)
        
        @self.app.delete("/api/songs/{song_id}")
        async def delete_song(song_id: str):
            """Delete a song"""
            success = self.song_service.delete_song(song_id)
            if not success:
                raise HTTPException(status_code=404, detail="Song not found or could not be deleted")
            return {"message": "Song deleted successfully"}
        
        @self.app.get("/api/songs/{song_id}/file")
        async def get_song_file(song_id: str):
            """Get song audio file"""
            song = self.song_service.get_song_by_path(song_id)
            if not song or not Path(song.file_path).exists():
                raise HTTPException(status_code=404, detail="Song file not found")
            return FileResponse(song.file_path)
        
        @self.app.get("/api/songs/{song_id}/thumbnail")
        async def get_song_thumbnail(song_id: str):
            """Get song thumbnail"""
            song = self.song_service.get_song_by_path(song_id)
            if not song or not song.thumbnail_path or not Path(song.thumbnail_path).exists():
                raise HTTPException(status_code=404, detail="Thumbnail not found")
            return FileResponse(song.thumbnail_path)
        
        # Playlists endpoints
        @self.app.get("/api/playlists", response_model=List[PlaylistResponse])
        async def get_playlists():
            """Get all playlists"""
            playlists = self.playlist_service.get_all_playlists()
            return [PlaylistResponse.from_playlist(name, data) for name, data in playlists.items()]
        
        @self.app.get("/api/playlists/{playlist_name}", response_model=PlaylistResponse)
        async def get_playlist(playlist_name: str):
            """Get a specific playlist"""
            playlist = self.playlist_service.get_playlist(playlist_name)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            return PlaylistResponse.from_playlist(playlist_name, playlist)
        
        @self.app.post("/api/playlists", response_model=PlaylistResponse)
        async def create_playlist(request: CreatePlaylistRequest):
            """Create a new playlist"""
            success = self.playlist_service.create_playlist(request.name, request.description)
            if not success:
                raise HTTPException(status_code=400, detail="Playlist already exists")
            playlist = self.playlist_service.get_playlist(request.name)
            return PlaylistResponse.from_playlist(request.name, playlist)
        
        @self.app.delete("/api/playlists/{playlist_name}")
        async def delete_playlist(playlist_name: str):
            """Delete a playlist"""
            success = self.playlist_service.delete_playlist(playlist_name)
            if not success:
                raise HTTPException(status_code=404, detail="Playlist not found")
            return {"message": "Playlist deleted successfully"}
        
        @self.app.post("/api/playlists/{playlist_name}/songs")
        async def add_to_playlist(playlist_name: str, request: AddToPlaylistRequest):
            """Add song to playlist"""
            song = self.song_service.get_song_by_path(request.song_id)
            if not song:
                raise HTTPException(status_code=404, detail="Song not found")
            
            success = self.playlist_service.add_to_playlist(playlist_name, song)
            if not success:
                raise HTTPException(status_code=400, detail="Could not add song to playlist")
            return {"message": "Song added to playlist successfully"}
        
        @self.app.delete("/api/playlists/{playlist_name}/songs/{song_id}")
        async def remove_from_playlist(playlist_name: str, song_id: str):
            """Remove song from playlist"""
            song = self.song_service.get_song_by_path(song_id)
            if not song:
                raise HTTPException(status_code=404, detail="Song not found")
            
            success = self.playlist_service.remove_from_playlist(playlist_name, song)
            if not success:
                raise HTTPException(status_code=400, detail="Could not remove song from playlist")
            return {"message": "Song removed from playlist successfully"}
        
        # Search endpoints
        @self.app.get("/api/search", response_model=List[SearchResultResponse])
        async def search_music(query: str, limit: int = 10):
            """Search for music online"""
            results = await self.search_service.search_async(query, limit)
            return [SearchResultResponse.from_search_result(result) for result in results]
        
        # Download endpoints
        @self.app.post("/api/download")
        async def download_music(request: DownloadRequest):
            """Download music from URL"""
            success = await self.download_service.download_async(request.url)
            if not success:
                raise HTTPException(status_code=400, detail="Could not download music")
            return {"message": "Download started successfully"}
        
        # Settings endpoints
        @self.app.get("/api/settings", response_model=SettingsResponse)
        async def get_settings():
            """Get application settings"""
            settings = self.settings_service.get_settings()
            return SettingsResponse.from_settings(settings)
        
        @self.app.put("/api/settings", response_model=SettingsResponse)
        async def update_settings(request: UpdateSettingsRequest):
            """Update application settings"""
            settings = self.settings_service.update_settings(request.dict(exclude_unset=True))
            return SettingsResponse.from_settings(settings)
        
        # Health check
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}


def create_api(downloads_dir: Path) -> FastAPI:
    """Factory function to create API instance"""
    api = MusicAPI(downloads_dir)
    return api.app


def run_api(downloads_dir: Path, host: str = "127.0.0.1", port: int = 8000):
    """Run the API server"""
    app = create_api(downloads_dir)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    from pathlib import Path
    downloads_dir = Path.home() / "melodia"
    downloads_dir.mkdir(exist_ok=True)
    run_api(downloads_dir)