import sys
from typing import Callable
from pathlib import Path
from contextlib import suppress
from functools import partial
import queue

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

# Import our modules
from .managers import (
    DataManager, SettingsManager, DownloadManager, 
    SearchManager, PlaylistManager
)
from .core import MusicPlayer, Event, EventBus, AppContext
from .ui import UIFactory
from .controllers import (
    Controller, NavigationController, PlayerController,
    FeedController, SearchController, PlaylistController,
    SettingsController
)
from .models import ThemeColors


class MusicApp:
    """Main application class"""
    
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("🎵 Melodia - Modern Music Player")
        
        # Maximize window
        self.root.after(0, lambda: self.root.state('zoomed'))
        
        # Downloads directory
        downloads_dir = Path.home() / "melodia"
        downloads_dir.mkdir(exist_ok=True)
        
        # Clean temporary files
        self._cleanup_temp_files(downloads_dir)
        
        # Create event bus
        event_bus = EventBus()
        
        # Create UI queue
        ui_queue: queue.Queue[Callable] = queue.Queue()
        
        # Initialize managers
        data_manager = DataManager(downloads_dir)
        settings_manager = SettingsManager(downloads_dir)
        player = MusicPlayer()
        player.set_root_reference(root)
        download_manager = DownloadManager(downloads_dir)
        search_manager = SearchManager()
        playlist_manager = PlaylistManager()
        
        # Load data
        playlists, feed_items = data_manager.load_data()
        playlist_manager.playlists = playlists
        
        # Create application context
        self.context = AppContext(
            root=root,
            event_bus=event_bus,
            colors=ThemeColors(),
            downloads_dir=downloads_dir,
            ui_queue=ui_queue,
            data_manager=data_manager,
            settings_manager=settings_manager,
            player=player,
            download_manager=download_manager,
            search_manager=search_manager,
            playlist_manager=playlist_manager,
            feed_items=feed_items
        )
        
        # Initialize controllers
        self.controllers: dict[str, Controller] = {
            'navigation': NavigationController(self.context),
            'player': PlayerController(self.context),
            'feed': FeedController(self.context),
            'search': SearchController(self.context),
            'playlist': PlaylistController(self.context),
            'settings': SettingsController(self.context)
        }
        
        # Setup event handlers
        self._setup_global_event_handlers()
        
        # Create main UI
        self._create_main_ui()
        
        # Initialize all controllers
        for controller in self.controllers.values():
            controller.initialize()
        
        # Apply saved settings
        player_controller = self.controllers['player']
        if isinstance(player_controller, PlayerController) and (settings_controller := self.controllers.get('settings')):
            if isinstance(settings_controller, SettingsController):
                player.set_volume(settings_controller.saved_default_volume / 100)
                if player_controller.volume:
                    player_controller.volume.set(settings_controller.saved_default_volume)
                if player_controller.volume_label:
                    player_controller.volume_label.configure(text=f"{settings_controller.saved_default_volume}%")
        
        # Navigate to initial view
        nav_controller = self.controllers['navigation']
        if isinstance(nav_controller, NavigationController):
            nav_controller.navigate_to("feed")
        
        # Start UI processing
        self._process_ui_queue()
        
        # Configure cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _cleanup_temp_files(self, downloads_dir: Path) -> None:
        """Clean temporary files"""
        with suppress(Exception):
            for pattern in ('*.part', '*.tmp', '*.temp'):
                for file in downloads_dir.glob(pattern):
                    with suppress(Exception):
                        file.unlink()
    
    def _setup_global_event_handlers(self) -> None:
        """Setup global event handlers"""
        # Data events
        self.context.event_bus.subscribe('save_data', lambda e: self._save_data())
        
        # Volume events
        self.context.event_bus.subscribe('volume_changed', self._handle_volume_changed)
    
    def _handle_volume_changed(self, event: Event) -> None:
        """Handle volume changed event"""
        if volume := event.data.get('volume'):
            player_controller = self.controllers['player']
            if isinstance(player_controller, PlayerController):
                if player_controller.volume:
                    player_controller.volume.set(volume)
                player_controller.change_volume(volume)
    
    def _save_data(self) -> None:
        """Save all data"""
        self.context.data_manager.save_data(
            self.context.playlist_manager.playlists,
            self.context.feed_items
        )
    
    def _create_main_ui(self) -> None:
        """Create main interface"""
        # Main container
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sidebar
        self._create_sidebar(main)
        
        # Content area container
        self.context.content_container = ctk.CTkFrame(main, corner_radius=15)
        self.context.content_container.pack(side="left", fill="both", expand=True)
    
    def _create_sidebar(self, parent: ctk.CTkFrame) -> None:
        """Create sidebar with navigation and player"""
        sidebar = ctk.CTkFrame(parent, width=300, corner_radius=15)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)
        
        # Logo and title
        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=30)
        
        ctk.CTkLabel(header, text="🎵", font=ctk.CTkFont(size=48)).pack()
        ctk.CTkLabel(header, text="Melodia", font=ctk.CTkFont(size=28, weight="bold")).pack()
        ctk.CTkLabel(
            header, 
            text="Your Music Experience",
            font=ctk.CTkFont(size=12), 
            text_color="gray"
        ).pack()
        
        # Navigation menu
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=20)
        
        menu_items = [
            ("🏠", "Início", "feed"),
            ("🔍", "Descobrir", "search"),
            ("📚", "Biblioteca", "playlists"),
            ("⚙️", "Configuração", "settings")
        ]
        
        nav_controller = self.controllers['navigation']
        for icon, text, view in menu_items:
            if isinstance(nav_controller, NavigationController):
                btn = UIFactory.create_nav_button(
                    nav_frame, 
                    icon, 
                    text, 
                    partial(nav_controller.navigate_to, view)
                )
                self.context.navigation_buttons[view] = btn
        
        # Player
        player_controller = self.controllers['player']
        if isinstance(player_controller, PlayerController):
            player_controller.create_player_ui(sidebar)
    
    def _process_ui_queue(self) -> None:
        """Process UI updates from queue"""
        try:
            while True:
                func = self.context.ui_queue.get_nowait()
                func()
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._process_ui_queue)
    
    def _on_closing(self) -> None:
        """Cleanup on application close"""
        # Cleanup controllers
        for controller in self.controllers.values():
            controller.cleanup()
        
        # Shutdown managers
        self.context.download_manager.shutdown()
        self.context.search_manager.shutdown()
        
        # Save data
        self._save_data()
        
        # Destroy window
        self.root.destroy()