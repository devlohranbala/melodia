import customtkinter as ctk
from ..core import Event
from .base_controller import BaseController


class NavigationController(BaseController):
    """Controller for navigation between views"""
    
    def initialize(self) -> None:
        """Initialize navigation"""
        self._create_view_frames()
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers"""
        self.event_bus.subscribe('navigate', self._handle_navigate)
    
    def _handle_navigate(self, event: Event) -> None:
        """Handle navigation event"""
        if view := event.data.get('view'):
            self.navigate_to(view)
    
    def _create_view_frames(self) -> None:
        """Create all view frames upfront"""
        views = ['feed', 'search', 'playlists', 'settings', 'playlist_detail']
        
        for view in views:
            frame = ctk.CTkFrame(self.context.content_container, fg_color="transparent")
            self.context.view_frames[view] = frame
    
    def navigate_to(self, view: str) -> None:
        """Navigate to a specific view"""
        # Hide all frames
        for frame in self.context.view_frames.values():
            frame.pack_forget()
        
        # Update button states
        for btn_view, btn in self.context.navigation_buttons.items():
            btn.configure(fg_color=self.colors.accent if btn_view == view else "transparent")
        
        # Show the selected view
        self.context.current_view = view
        self.context.view_frames[view].pack(fill="both", expand=True)
        
        # Publish view change event
        self.event_bus.publish(Event(f'show_{view}'))