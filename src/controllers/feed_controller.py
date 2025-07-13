import sys
from typing import Optional, Callable, Any
from pathlib import Path
import threading

try:
    import customtkinter as ctk
except ImportError as e:
    print(f"Dependência não encontrada: {e}")
    print("Execute: pip install customtkinter")
    sys.exit(1)

try:
    from PIL import Image
except ImportError as e:
    print(f"Dependência não encontrada: {e}")
    print("Execute: pip install Pillow")
    sys.exit(1)

from ..core import AppContext, Event
from ..models import Song
from ..ui import UIComponents
from .base_controller import BaseController


class FeedController(BaseController):
    """Controller for music feed functionality"""
    
    def __init__(self, app_context: AppContext):
        super().__init__(app_context)
        self.feed_search_entry: Optional[ctk.CTkEntry] = None
        self.feed_music_container: Optional[ctk.CTkFrame] = None
        self.search_timer: Optional[threading.Timer] = None
    
    def initialize(self) -> None:
        """Initialize feed controller"""
        self._setup_event_handlers()
        self.refresh_feed()
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers"""
        self.event_bus.subscribe('show_feed', lambda e: self.show_feed())
        self.event_bus.subscribe('update_feed', lambda e: self.refresh_feed())
        self.event_bus.subscribe('song_deleted', lambda e: self.refresh_feed())
        self.event_bus.subscribe('songs_refreshed', lambda e: self.refresh_feed())
        self.event_bus.subscribe('song_added', lambda e: self.refresh_feed())
        self.event_bus.subscribe('song_updated', lambda e: self.refresh_feed())
    
    def show_feed(self) -> None:
        """Show music feed with search"""
        parent = self.context.view_frames['feed']
        UIComponents.clear_widget_children(parent)
        
        # Header with search
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        
        # Search bar
        search_container = ctk.CTkFrame(header, corner_radius=15)
        search_container.pack(fill="x")
        
        search_frame = ctk.CTkFrame(search_container, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=20)
        
        self.feed_search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Pesquisar suas músicas...",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.feed_search_entry.pack(fill="x")
        self.feed_search_entry.bind('<KeyRelease>', self.filter_feed)
        
        # Scrollable content
        feed_scroll = ctk.CTkScrollableFrame(parent)
        feed_scroll.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Music container
        self.feed_music_container = ctk.CTkFrame(feed_scroll, fg_color="transparent")
        self.feed_music_container.pack(fill="both", expand=True)
        
        self.display_filtered_feed(self.context.feed_items)
    
    def filter_feed(self, event=None) -> None:
        """Filter feed music with debounce"""
        # Cancel previous timer if exists
        if self.search_timer:
            self.search_timer.cancel()
        
        # Start new timer with 300ms delay
        self.search_timer = threading.Timer(0.3, self._perform_search)
        self.search_timer.start()
    
    def _perform_search(self) -> None:
        """Perform the actual search"""
        search_term = ""
        if self.feed_search_entry:
            search_term = self.feed_search_entry.get().strip()
        
        # If search term is empty, use local feed items
        if not search_term:
            filtered_items = self.context.feed_items
        else:
            # Filter locally first to avoid API calls for simple searches
            filtered_items = [
                song for song in self.context.feed_items
                if search_term.lower() in song.title.lower() or 
                   search_term.lower() in song.artist.lower()
            ]
        
        # Schedule UI update on main thread
        self.context.root.after(0, lambda: self.display_filtered_feed(filtered_items))
    
    def display_filtered_feed(self, items: list[Song]) -> None:
        """Display filtered music"""
        if not self.feed_music_container:
            return
            
        empty_state = {
            'icon': '🔍' if self.feed_search_entry and self.feed_search_entry.get().strip() else '🎵',
            'title': 'Nenhuma música encontrada' if self.feed_search_entry and self.feed_search_entry.get().strip() else 'Nenhuma música ainda',
            'subtitle': 'Tente pesquisar com outros termos' if self.feed_search_entry and self.feed_search_entry.get().strip() else 'Comece baixando suas músicas favoritas!'
        }
        
        self._display_grid_items(
            self.feed_music_container,
            items,
            self.create_music_card,
            empty_state
        )
    
    def create_music_card(self, parent: ctk.CTkFrame, item: Song, row: int, col: int) -> None:
        """Create modern music card"""
        card, inner = UIComponents.create_base_card(parent, row, col)
        
        # Thumbnail
        thumbnail_container = ctk.CTkFrame(inner, fg_color="transparent")
        thumbnail_container.pack(pady=(0, 20))
        
        if item.thumbnail_path and Path(item.thumbnail_path).exists():
            try:
                thumbnail_frame = ctk.CTkFrame(
                    thumbnail_container, 
                    width=140, 
                    height=140, 
                    corner_radius=15,
                    border_width=2,
                    border_color=("gray80", "gray20")
                )
                thumbnail_frame.pack()
                thumbnail_frame.pack_propagate(False)
                
                image = Image.open(item.thumbnail_path)
                ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(136, 136))
                
                thumbnail_label = ctk.CTkLabel(thumbnail_frame, image=ctk_image, text="")
                thumbnail_label.pack(expand=True, padx=2, pady=2)
            except Exception:
                self._create_default_thumbnail(thumbnail_container)
        else:
            self._create_default_thumbnail(thumbnail_container)
        
        # Content
        content_frame = ctk.CTkFrame(inner, fg_color="transparent")
        content_frame.pack(fill="x", pady=(0, 20))
        
        title_text = UIComponents.truncate_text(item.title, 28)
        ctk.CTkLabel(
            content_frame,
            text=title_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="center"
        ).pack(pady=(0, 8))
        
        ctk.CTkLabel(
            content_frame,
            text=item.artist,
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
            anchor="center"
        ).pack(pady=(0, 12))
        
        ctk.CTkLabel(
            content_frame,
            text=item.date,
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
            anchor="center"
        ).pack()
        
        # Action buttons
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        play_btn = ctk.CTkButton(
            btn_frame,
            text="▶ Tocar",
            command=lambda: self.event_bus.publish(Event('play_song', {'song': item})),
            font=ctk.CTkFont(size=13, weight="bold"),
            width=100,
            height=36,
            corner_radius=18,
            fg_color=("#007AFF", "#0A84FF"),
            hover_color=("#005BB5", "#0056CC")
        )
        play_btn.pack(pady=(0, 12))
        
        secondary_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        secondary_frame.pack()
        
        add_btn = ctk.CTkButton(
            secondary_frame,
            text="➕",
            command=lambda: self.event_bus.publish(Event('add_to_playlist', {'song': item})),
            font=ctk.CTkFont(size=14),
            width=36,
            height=36,
            corner_radius=18,
            fg_color="transparent",
            border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray60", "gray40"),
            hover_color=("gray90", "gray20")
        )
        add_btn.pack(side="left", padx=(0, 8))
        
        delete_btn = ctk.CTkButton(
            secondary_frame,
            text="🗑",
            command=lambda: self.context.music_service.confirm_delete_song(item),
            font=ctk.CTkFont(size=14),
            width=36,
            height=36,
            corner_radius=18,
            fg_color="transparent",
            border_width=1,
            border_color=("#FF3B30", "#FF453A"),
            text_color=("#FF3B30", "#FF453A"),
            hover_color=("#FFE5E5", "#2D1B1B")
        )
        delete_btn.pack(side="left")
    
    def refresh_feed(self) -> None:
        """Refresh music feed using MusicService"""
        try:
            # Get songs from API and update context
            songs = self.context.music_service.get_all_songs()
            self.context.feed_items = songs
            
            # Update display if on feed view
            if self.context.current_view == "feed" and hasattr(self, 'feed_search_entry'):
                self._perform_search()
        except Exception as e:
            print(f"Error refreshing feed: {e}")
            # Fallback to existing items
            if self.context.current_view == "feed" and hasattr(self, 'feed_search_entry'):
                self._perform_search()
    

    
    def _create_default_thumbnail(self, parent: ctk.CTkFrame) -> None:
        """Create default thumbnail"""
        icon_frame = ctk.CTkFrame(
            parent,
            width=140,
            height=140,
            corner_radius=15,
            fg_color=("gray90", "gray10")
        )
        icon_frame.pack()
        icon_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            icon_frame, 
            text="🎵", 
            font=ctk.CTkFont(size=52),
            text_color=("gray60", "gray40")
        ).pack(expand=True)
    
    def _display_grid_items(
        self,
        container: ctk.CTkFrame,
        items: list[Any],
        create_card_func: Callable,
        empty_state: dict
    ) -> None:
        """Display items in grid"""
        UIComponents.clear_widget_children(container)
        
        if items:
            for i, item in enumerate(items):
                row, col = divmod(i, 3)
                create_card_func(container, item, row, col)
        else:
            UIComponents.create_empty_state(
                container,
                empty_state['icon'],
                empty_state['title'],
                empty_state['subtitle']
            )