import requests
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import (
    SongResponse, PlaylistResponse, SearchResultResponse,
    SettingsResponse, CreatePlaylistRequest, AddToPlaylistRequest,
    UpdateSettingsRequest, DownloadRequest
)


class APIClient:
    """HTTP client for communicating with the Melodia API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """Make GET request"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response
    
    def _post(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make POST request"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response
    
    def _put(self, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make PUT request"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response
    
    def _delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url)
        response.raise_for_status()
        return response
    
    # Songs endpoints
    def get_songs(self, search: Optional[str] = None) -> List[SongResponse]:
        """Get all songs or search songs"""
        params = {'search': search} if search else None
        response = self._get('/api/songs', params=params)
        return [SongResponse(**song) for song in response.json()]
    
    def get_song(self, song_id: str) -> SongResponse:
        """Get a specific song"""
        response = self._get(f'/api/songs/{song_id}')
        return SongResponse(**response.json())
    
    def delete_song(self, song_id: str) -> bool:
        """Delete a song"""
        try:
            self._delete(f'/api/songs/{song_id}')
            return True
        except requests.RequestException:
            return False
    
    def get_song_file_url(self, song_id: str) -> str:
        """Get URL for song audio file"""
        return f"{self.base_url}/api/songs/{song_id}/file"
    
    def get_song_thumbnail_url(self, song_id: str) -> str:
        """Get URL for song thumbnail"""
        return f"{self.base_url}/api/songs/{song_id}/thumbnail"
    
    def download_song_file(self, song_id: str, output_path: Path) -> bool:
        """Download song file to local path"""
        try:
            response = self._get(f'/api/songs/{song_id}/file')
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        except (requests.RequestException, IOError):
            return False
    
    # Playlists endpoints
    def get_playlists(self) -> List[PlaylistResponse]:
        """Get all playlists"""
        response = self._get('/api/playlists')
        return [PlaylistResponse(**playlist) for playlist in response.json()]
    
    def get_playlist(self, playlist_name: str) -> PlaylistResponse:
        """Get a specific playlist"""
        response = self._get(f'/api/playlists/{playlist_name}')
        return PlaylistResponse(**response.json())
    
    def create_playlist(self, name: str, description: str = "") -> PlaylistResponse:
        """Create a new playlist"""
        request = CreatePlaylistRequest(name=name, description=description)
        response = self._post('/api/playlists', data=request.model_dump())
        return PlaylistResponse(**response.json())
    
    def delete_playlist(self, playlist_name: str) -> bool:
        """Delete a playlist"""
        try:
            self._delete(f'/api/playlists/{playlist_name}')
            return True
        except requests.RequestException:
            return False
    
    def add_to_playlist(self, playlist_name: str, song_id: str) -> bool:
        """Add song to playlist"""
        try:
            request = AddToPlaylistRequest(song_id=song_id)
            self._post(f'/api/playlists/{playlist_name}/songs', data=request.model_dump())
            return True
        except requests.RequestException:
            return False
    
    def remove_from_playlist(self, playlist_name: str, song_id: str) -> bool:
        """Remove song from playlist"""
        try:
            self._delete(f'/api/playlists/{playlist_name}/songs/{song_id}')
            return True
        except requests.RequestException:
            return False
    
    # Search endpoints
    def search_music(self, query: str, limit: int = 10) -> List[SearchResultResponse]:
        """Search for music online"""
        params = {'query': query, 'limit': limit}
        response = self._get('/api/search', params=params)
        return [SearchResultResponse(**result) for result in response.json()]
    
    # Download endpoints
    def download_music(self, url: str) -> bool:
        """Download music from URL"""
        try:
            request = DownloadRequest(url=url)
            self._post('/api/download', data=request.model_dump())
            return True
        except requests.RequestException:
            return False
    
    # Settings endpoints
    def get_settings(self) -> SettingsResponse:
        """Get application settings"""
        response = self._get('/api/settings')
        return SettingsResponse(**response.json())
    
    def update_settings(self, **kwargs) -> SettingsResponse:
        """Update application settings"""
        request = UpdateSettingsRequest(**kwargs)
        response = self._put('/api/settings', data=request.model_dump(exclude_unset=True))
        return SettingsResponse(**response.json())
    
    # Health check
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self._get('/api/health')
        return response.json()
    
    def is_api_available(self) -> bool:
        """Check if API is available"""
        try:
            self.health_check()
            return True
        except requests.RequestException:
            return False
    
    def close(self):
        """Close the session"""
        self.session.close()


class AsyncAPIClient:
    """Async HTTP client for communicating with the Melodia API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make async GET request"""
        url = f"{self.base_url}{endpoint}"
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def _post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make async POST request"""
        url = f"{self.base_url}{endpoint}"
        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def search_music(self, query: str, limit: int = 10) -> List[SearchResultResponse]:
        """Search for music online asynchronously"""
        params = {'query': query, 'limit': limit}
        data = await self._get('/api/search', params=params)
        return [SearchResultResponse(**result) for result in data]
    
    async def download_music(self, url: str) -> bool:
        """Download music from URL asynchronously"""
        try:
            request = DownloadRequest(url=url)
            await self._post('/api/download', data=request.model_dump())
            return True
        except aiohttp.ClientError:
            return False


# Singleton instance for easy access
_api_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Get singleton API client instance"""
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client


def set_api_base_url(base_url: str):
    """Set API base URL and reset client"""
    global _api_client
    if _api_client:
        _api_client.close()
    _api_client = APIClient(base_url)