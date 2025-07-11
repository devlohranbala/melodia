from tkinter import messagebox
from typing import Optional, Callable
from contextlib import suppress
from functools import partial

import customtkinter as ctk

from ..models import Song, SearchResult
from ..ui import UIComponents, UIFactory
from ..core import Event, AppContext
from .base_controller import BaseController


class SearchController(BaseController):
    """Controller for search and download functionality"""
    
    def __init__(self, app_context: AppContext):
        super().__init__(app_context)
        self.search_entry: Optional[ctk.CTkEntry] = None
        self.search_status: Optional[ctk.CTkLabel] = None
        self.results_container: Optional[ctk.CTkScrollableFrame] = None
        self.url_entry: Optional[ctk.CTkEntry] = None
        self.url_status: Optional[ctk.CTkLabel] = None
        self.tab_content: Optional[ctk.CTkFrame] = None
        self.search_tab: Optional[ctk.CTkButton] = None
        self.url_tab: Optional[ctk.CTkButton] = None
    
    def initialize(self) -> None:
        """Initialize search controller"""
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers"""
        self.event_bus.subscribe('show_search', lambda e: self.show_search())
    
    def show_search(self) -> None:
        """Show search page with tabs"""
        parent = self.context.view_frames['search']
        UIComponents.clear_widget_children(parent)
        
        # Header
        UIFactory.create_content_header(parent, "Descobrir Músicas", "🔍 Busque e baixe suas músicas favoritas")
        
        # Main container
        main_container = ctk.CTkFrame(parent, corner_radius=15)
        main_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Tabs
        tab_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        tab_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        self.search_tab = ctk.CTkButton(
            tab_frame,
            text="Buscar no YouTube",
            command=lambda: self.show_tab_content("search"),
            font=ctk.CTkFont(size=14),
            width=150,
            height=40
        )
        self.search_tab.pack(side="left", padx=(0, 10))
        
        self.url_tab = ctk.CTkButton(
            tab_frame,
            text="Baixar por URL",
            command=lambda: self.show_tab_content("url"),
            font=ctk.CTkFont(size=14),
            width=150,
            height=40,
            fg_color="gray",
            hover_color="gray"
        )
        self.url_tab.pack(side="left")
        
        # Tab content container
        self.tab_content = ctk.CTkFrame(main_container, fg_color="transparent")
        self.tab_content.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        self.show_tab_content("search")
    
    def show_tab_content(self, tab: str) -> None:
        """Show tab content"""
        if not self.search_tab or not self.url_tab:
            return
            
        if tab == "search":
            self.search_tab.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
            self.url_tab.configure(fg_color="gray", hover_color="gray")
            self.show_search_tab()
        else:
            self.search_tab.configure(fg_color="gray", hover_color="gray")
            self.url_tab.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
            self.show_url_tab()
    
    def show_search_tab(self) -> None:
        """Show search tab"""
        if not self.tab_content:
            return
            
        UIComponents.clear_widget_children(self.tab_content)
        
        # Search form
        search_form = ctk.CTkFrame(self.tab_content, fg_color="transparent")
        search_form.pack(fill="x")
        
        input_frame = ctk.CTkFrame(search_form, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, 20))
        
        self.search_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Digite sua busca aqui...",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind('<Return>', lambda e: self.search_music())
        
        ctk.CTkButton(
            input_frame,
            text="🔍 Buscar",
            command=self.search_music,
            font=ctk.CTkFont(size=14),
            width=120,
            height=40
        ).pack(side="right")
        
        self.search_status = ctk.CTkLabel(
            search_form,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.search_status.pack()
        
        self.results_container = ctk.CTkScrollableFrame(self.tab_content, height=400)
        self.results_container.pack(fill="both", expand=True, pady=20)
    
    def show_url_tab(self) -> None:
        """Show URL tab"""
        if not self.tab_content:
            return
            
        UIComponents.clear_widget_children(self.tab_content)
        
        url_form = ctk.CTkFrame(self.tab_content, fg_color="transparent")
        url_form.pack(fill="x")
        
        ctk.CTkLabel(
            url_form,
            text="URL do YouTube:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.url_entry = ctk.CTkEntry(
            url_form,
            placeholder_text="Cole aqui o link do vídeo...",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.url_entry.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(
            url_form,
            text="Baixar Música",
            command=self.download_from_url,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color=self.colors.success,
            hover_color="#1e7e34"
        ).pack(pady=20)
        
        self.url_status = ctk.CTkLabel(
            url_form,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.url_status.pack()
    
    def search_music(self) -> None:
        """Search music"""
        if not self.search_entry or not (query := self.search_entry.get().strip()):
            messagebox.showerror("Erro", "Digite algo para buscar!")
            return
        
        if self.results_container:
            UIComponents.clear_widget_children(self.results_container)
        
        self.context.search_manager.search_music(
            query,
            on_results=lambda results: self.schedule_ui_update(
                partial(self.display_search_results, results)
            ),
            on_error=lambda error: self.schedule_ui_update(
                partial(self._handle_error, error, "search")
            ),
            on_status=lambda status: self.schedule_ui_update(
                partial(self._update_status_label, self.search_status, status)
            )
        )
    
    def display_search_results(self, results: list[SearchResult]) -> None:
        """Display search results"""
        self.context.search_results = results
        
        if self.search_status:
            self._update_status_label(self.search_status, f"✅ {len(results)} resultados encontrados")
        
        if not self.results_container:
            return
            
        UIComponents.clear_widget_children(self.results_container)
        
        if not results:
            empty_label = ctk.CTkLabel(
                self.results_container,
                text="Nenhum resultado encontrado",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            empty_label.pack(pady=50)
            return
        
        for i, result in enumerate(results):
            self.create_result_card(self.results_container, result, i)
    
    def create_result_card(self, parent: ctk.CTkScrollableFrame, result: SearchResult, index: int) -> None:
        """Create result card"""
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(fill="x", padx=10, pady=5)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)
        
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        title_text = UIComponents.truncate_text(result.title, 60)
        ctk.CTkLabel(
            info_frame,
            text=title_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        ).pack(fill="x")
        
        details = f"🎤 {result.artist} • ⏱ {result.duration}"
        if result.view_count:
            details += f" • 👁 {result.formatted_views}"
        
        ctk.CTkLabel(
            info_frame,
            text=details,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        ).pack(fill="x", pady=(5, 0))
        
        UIComponents.create_action_button(
            content,
            "⬇ Baixar",
            partial(self.download_selected_song, result),
            width=80,
            height=35,
            fg_color=self.colors.success,
            hover_color="#1e7e34"
        ).pack(side="right", padx=(10, 0))
    
    def download_from_url(self) -> None:
        """Download music by URL"""
        if not self.url_entry or not (url := self.url_entry.get().strip()):
            messagebox.showerror("Erro", "Digite uma URL!")
            return
        
        handlers = self._create_status_handler(self.url_status, "url")
        self.context.download_manager.download_music(url, **handlers)
    
    def download_selected_song(self, result: SearchResult) -> None:
        """Download selected song"""
        handlers = self._create_status_handler(self.search_status, "search")
        self.context.download_manager.download_music(result.url, **handlers)
    
    def _create_status_handler(self, status_label: Optional[ctk.CTkLabel], source_type: str) -> dict[str, Callable]:
        """Create status handler callbacks"""
        return {
            'on_complete': lambda result: self.schedule_ui_update(
                partial(self._handle_complete, result, source_type)
            ),
            'on_error': lambda error: self.schedule_ui_update(
                partial(self._handle_error, error, source_type)
            ),
            'on_status': lambda status: self.schedule_ui_update(
                partial(self._update_status_label, status_label, status)
            )
        }
    
    def _handle_complete(self, song: Song, source_type: str) -> None:
        """Handle download complete"""
        status_label = self.url_status if source_type == "url" else self.search_status
        self._update_status_label(status_label, "✅ Download concluído!")
        
        self.context.feed_items.insert(0, song)
        self.event_bus.publish(Event('save_data'))
        
        if source_type == "url" and self.url_entry:
            self.url_entry.delete(0, "end")
        
        self.event_bus.publish(Event('update_feed'))
        
        if messagebox.askyesno("Adicionar", "Adicionar a uma playlist?"):
            self.event_bus.publish(Event('add_to_playlist', {'song': song}))
    
    def _handle_error(self, error: str, source_type: str) -> None:
        """Handle download error"""
        status_label = self.url_status if source_type == "url" else self.search_status
        self._update_status_label(status_label, "❌ Erro no download!")
        messagebox.showerror("Erro", f"Erro ao baixar: {error}")
    
    def _update_status_label(self, label: Optional[ctk.CTkLabel], text: str) -> None:
        """Update status label safely"""
        with suppress(Exception):
            if label and label.winfo_exists():
                label.configure(text=text)