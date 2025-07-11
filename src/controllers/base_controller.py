from abc import ABC, abstractmethod
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    # Evita importação circular usando TYPE_CHECKING
    from ..core import AppContext

class BaseController(ABC):
    """Base controller with common functionality"""
    def __init__(self, app_context: 'AppContext'):
        self.context = app_context
        self.colors = app_context.colors
        self.root = app_context.root
        self.event_bus = app_context.event_bus
        
    @abstractmethod
    def initialize(self) -> None:
        """Initialize controller"""
        pass
    
    def cleanup(self) -> None:
        """Cleanup controller resources"""
        pass
    
    def schedule_ui_update(self, func: Callable) -> None:
        """Schedule UI update on main thread"""
        self.context.ui_queue.put(func)