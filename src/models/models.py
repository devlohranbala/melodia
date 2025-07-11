from dataclasses import dataclass, asdict, field
from typing import Self, TypeAlias, Final

# Type aliases
SongDict: TypeAlias = dict[str, str | int]
PlaylistDict: TypeAlias = dict[str, list[SongDict] | str]
SettingsDict: TypeAlias = dict[str, str | int | None]

# Constants
AUDIO_EXTENSIONS: Final[tuple[str, ...]] = ('.webm')
DEFAULT_VOLUME: Final[int] = 70
POSITION_UPDATE_INTERVAL: Final[int] = 500
DEFAULT_CROSSFADE_ENABLED: Final[bool] = False
DEFAULT_CROSSFADE_DURATION: Final[int] = 3
DEFAULT_AUDIO_OUTPUT: Final[str | None] = None

# ====================
# Data Classes
# ====================

@dataclass(slots=True, frozen=True)
class Song:
    """Immutable song representation with slots for memory efficiency"""
    title: str
    artist: str
    file_path: str
    date: str
    thumbnail_path: str = ""  # Caminho para a capa da música
    
    def to_dict(self) -> SongDict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: SongDict) -> Self:
        return cls(**data)
    
    def __str__(self) -> str:
        return f"{self.artist} - {self.title}"

@dataclass(slots=True)
class SearchResult:
    """Search result representation with slots"""
    title: str
    artist: str
    url: str
    duration: str
    view_count: int
    
    @property
    def formatted_views(self) -> str:
        """Format view count for display"""
        match self.view_count:
            case v if v >= 1_000_000:
                return f"{v/1_000_000:.1f}M"
            case v if v >= 1_000:
                return f"{v/1_000:.1f}K"
            case _:
                return str(self.view_count)

@dataclass(frozen=True)
class ThemeColors:
    """Theme color configuration"""
    bg: str = field(default='#212121')
    sidebar: str = field(default='#1a1a1a')
    card: str = field(default='#2b2b2b')
    card_hover: str = field(default='#3d3d3d')
    accent: str = field(default='#1f538d')
    accent_hover: str = field(default='#14375e')
    text: str = field(default='#ffffff')
    text_secondary: str = field(default='#b0b0b0')
    success: str = field(default='#2fa572')
    danger: str = field(default='#fa5252')
    warning: str = field(default='#fd7e14')