from tkinter import messagebox
from functools import partial
import customtkinter as ctk

from ..models import Song, PlaylistDict
from ..ui import UIComponents
from ..core import Event
from .base_controller import BaseController


class PlaylistController(BaseController):
    """Controller for playlist functionality"""
    
    def initialize(self) -> None:
        """Initialize playlist controller"""
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers"""
        self.event_bus.subscribe('show_playlists', lambda e: self.show_playlists())
        self.event_bus.subscribe('add_to_playlist', self._handle_add_to_playlist)
    
    def _handle_add_to_playlist(self, event: Event) -> None:
        """Handle add to playlist event"""
        if song := event.data.get('song'):
            self.add_to_playlist_dialog(song)
    
    def show_playlists(self) -> None:
        """Show playlists"""
        parent = self.context.view_frames['playlists']
        UIComponents.clear_widget_children(parent)
        
        # Header
        header_container = ctk.CTkFrame(parent, fg_color="transparent")
        header_container.pack(fill="x", padx=30, pady=(30, 20))
        
        header_frame = ctk.CTkFrame(header_container, fg_color="transparent")
        header_frame.pack(fill="x")
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            title_frame,
            text="Sua Biblioteca",
            font=ctk.CTkFont(size=32, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="📚 Gerencie suas playlists",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            header_frame,
            text="➕ Nova Playlist",
            command=self.create_playlist,
            font=ctk.CTkFont(size=14),
            height=40,
            width=150
        ).pack(side="right")
        
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Display playlists
        if self.context.playlist_manager.playlists:
            grid_container = ctk.CTkFrame(scroll, fg_color="transparent")
            grid_container.pack(fill="both", expand=True)
            
            for i, (name, playlist) in enumerate(self.context.playlist_manager.playlists.items()):
                row, col = divmod(i, 3)
                self.create_playlist_card(grid_container, name, playlist, row, col)
        else:
            UIComponents.create_empty_state(
                scroll,
                '📁',
                'Nenhuma playlist criada',
                "Clique em 'Nova Playlist' para começar!"
            )
    
    def create_playlist_card(self, parent: ctk.CTkFrame, name: str, playlist: PlaylistDict, row: int, col: int) -> None:
        """Create playlist card"""
        card, inner = UIComponents.create_base_card(parent, row, col)
        
        # Icon
        icon_container = ctk.CTkFrame(inner, fg_color="transparent")
        icon_container.pack(pady=(0, 20))
        
        icon_frame = ctk.CTkFrame(
            icon_container,
            width=120,
            height=120,
            corner_radius=15,
            fg_color=("gray90", "gray10")
        )
        icon_frame.pack()
        icon_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            icon_frame, 
            text="📁", 
            font=ctk.CTkFont(size=48),
            text_color=("gray60", "gray40")
        ).pack(expand=True)
        
        # Content
        content_frame = ctk.CTkFrame(inner, fg_color="transparent")
        content_frame.pack(fill="x", pady=(0, 20))
        
        title_text = UIComponents.truncate_text(name, 28)
        ctk.CTkLabel(
            content_frame,
            text=title_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="center"
        ).pack(pady=(0, 8))
        
        song_count = len(playlist['songs'])
        count_text = f"{song_count} música{'s' if song_count != 1 else ''}"
        ctk.CTkLabel(
            content_frame,
            text=count_text,
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
            anchor="center"
        ).pack(pady=(0, 12))
        
        # Buttons
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        play_btn = ctk.CTkButton(
            btn_frame,
            text="▶ Tocar",
            command=partial(self.play_playlist, name),
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
        
        view_btn = ctk.CTkButton(
            secondary_frame,
            text="👁",
            command=partial(self.view_playlist, name),
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
        view_btn.pack(side="left", padx=(0, 8))
        
        delete_btn = ctk.CTkButton(
            secondary_frame,
            text="🗑",
            command=partial(self.delete_playlist, name),
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
    
    def create_playlist(self) -> None:
        """Create playlist"""
        dialog = ctk.CTkInputDialog(text="Nome da playlist:", title="Nova Playlist")
        if name := dialog.get_input():
            if self.context.playlist_manager.create_playlist(name):
                self.event_bus.publish(Event('save_data'))
                self.show_playlists()
            else:
                messagebox.showerror("Erro", "Playlist já existe!")
    
    def play_playlist(self, name: str) -> None:
        """Play playlist"""
        if songs := self.context.playlist_manager.get_playlist_songs(name):
            self.event_bus.publish(Event('play_playlist', {'name': name, 'songs': songs}))
        else:
            messagebox.showinfo("Info", "Playlist vazia!")
    
    def view_playlist(self, name: str) -> None:
        """View playlist details"""
        parent = self.context.view_frames['playlist_detail']
        UIComponents.clear_widget_children(parent)
        
        # Switch to detail view
        self.context.view_frames['playlists'].pack_forget()
        parent.pack(fill="both", expand=True)
        
        playlist = self.context.playlist_manager.playlists[name]
        songs = self.context.playlist_manager.get_playlist_songs(name)
        
        # Header
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkButton(
            header_frame,
            text="← Voltar",
            command=self.back_to_playlists,
            font=ctk.CTkFont(size=12),
            width=80,
            height=30
        ).pack(side="left", anchor="w")
        
        info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=(20, 0))
        
        ctk.CTkLabel(
            info_frame,
            text=f"📁 {name}",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")
        
        song_count = len(songs)
        count_text = f"{song_count} música{'s' if song_count != 1 else ''}"
        ctk.CTkLabel(
            info_frame,
            text=count_text,
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(anchor="w", pady=(5, 0))
        
        # Botão "Tocar Tudo" removido
        
        # Content
        scroll = ctk.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        if songs:
            songs_frame = ctk.CTkFrame(scroll, corner_radius=15)
            songs_frame.pack(fill="both", expand=True)
            
            list_header = ctk.CTkFrame(songs_frame, fg_color="transparent")
            list_header.pack(fill="x", padx=20, pady=(20, 10))
            
            ctk.CTkLabel(
                list_header,
                text="Músicas da Playlist",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(anchor="w")
            
            for i, song in enumerate(songs):
                self.create_playlist_song_card(songs_frame, song, name, i)
        else:
            UIComponents.create_empty_state(
                scroll,
                '📁',
                'Playlist vazia',
                'Adicione músicas para começar a ouvir!'
            )
    
    def create_playlist_song_card(self, parent: ctk.CTkFrame, song: Song, playlist_name: str, index: int) -> None:
        """Create playlist song card"""
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(fill="x", padx=20, pady=5)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)
        
        ctk.CTkLabel(
            content,
            text=f"{index + 1:02d}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="gray",
            width=30
        ).pack(side="left", padx=(0, 15))
        
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        title_text = UIComponents.truncate_text(song.title, 50)
        ctk.CTkLabel(
            info_frame,
            text=title_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            info_frame,
            text=f"🎤 {song.artist}",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        ).pack(fill="x", pady=(2, 0))
        
        UIComponents.create_action_button(
            content,
            "▶",
            lambda: self.play_song_from_playlist(song, playlist_name),
            width=35,
            height=35
        ).pack(side="left", padx=2)
        
        UIComponents.create_action_button(
            content,
            "🗑",
            partial(self.remove_from_playlist, song, playlist_name),
            width=35,
            height=35,
            fg_color=self.colors.danger,
            hover_color="#c82333"
        ).pack(side="left", padx=2)
    
    def play_song_from_playlist(self, song: Song, playlist_name: str) -> None:
        """Play song from playlist"""
        self.context.player.current_playlist = playlist_name
        self.event_bus.publish(Event('play_song', {'song': song}))
    
    def back_to_playlists(self) -> None:
        """Go back to playlists view"""
        self.context.view_frames['playlist_detail'].pack_forget()
        self.event_bus.publish(Event('navigate', {'view': 'playlists'}))
    
    def add_to_playlist_dialog(self, song: Song) -> None:
        """Dialog to add song to playlist"""
        if not self.context.playlist_manager.playlists:
            if messagebox.askyesno("Criar Playlist", "Nenhuma playlist encontrada. Deseja criar uma nova?"):
                self.create_playlist()
                if self.context.playlist_manager.playlists:
                    self.add_to_playlist_dialog(song)
            return
        
        # Create dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Adicionar à Playlist")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 300
        y = (dialog.winfo_screenheight() // 2) - 250
        dialog.geometry(f"600x500+{x}+{y}")
        
        # Main container
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="Selecione uma playlist:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 20))
        
        # Song info
        song_info = ctk.CTkFrame(main_frame, fg_color="gray20")
        song_info.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            song_info,
            text=f"🎵 {song.title}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        ctk.CTkLabel(
            song_info,
            text=f"🎤 {song.artist}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(0, 5))
        
        # Playlist list
        playlist_frame = ctk.CTkScrollableFrame(main_frame, height=180)
        playlist_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        selected_playlist = ctk.StringVar()
        
        for playlist_name in self.context.playlist_manager.playlists.keys():
            playlist_count = len(self.context.playlist_manager.playlists[playlist_name]['songs'])
            radio_text = f"📁 {playlist_name} ({playlist_count} música{'s' if playlist_count != 1 else ''})"
            
            ctk.CTkRadioButton(
                playlist_frame,
                text=radio_text,
                variable=selected_playlist,
                value=playlist_name,
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=5, padx=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        def add_to_selected():
            if not (playlist_name := selected_playlist.get()):
                messagebox.showwarning("Aviso", "Selecione uma playlist!")
                return
            
            if self.context.playlist_manager.add_to_playlist(playlist_name, song):
                self.event_bus.publish(Event('save_data'))
                messagebox.showinfo("Sucesso", f"Música adicionada à playlist '{playlist_name}'!")
                dialog.destroy()
            else:
                messagebox.showinfo("Info", "Esta música já está na playlist!")
                dialog.destroy()
        
        def create_new_playlist():
            dialog.destroy()
            self.create_playlist()
            if self.context.playlist_manager.playlists:
                self.add_to_playlist_dialog(song)
        
        ctk.CTkButton(
            button_frame,
            text="➕ Adicionar",
            command=add_to_selected,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2fa572",
            hover_color="#1e7e34"
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame,
            text="📁 Nova Playlist",
            command=create_new_playlist,
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame,
            text="❌ Cancelar",
            command=dialog.destroy,
            font=ctk.CTkFont(size=12),
            fg_color="gray",
            hover_color="#666"
        ).pack(side="right")
    
    def remove_from_playlist(self, song: Song, playlist_name: str) -> None:
        """Remove song from playlist"""
        if messagebox.askyesno("Confirmar", f"Remover '{song.title}' da playlist?"):
            self.context.playlist_manager.remove_from_playlist(playlist_name, song)
            self.event_bus.publish(Event('save_data'))
            self.view_playlist(playlist_name)
    
    def delete_playlist(self, name: str) -> None:
        """Delete playlist"""
        if messagebox.askyesno("Confirmar", f"Excluir playlist '{name}'?"):
            self.context.playlist_manager.delete_playlist(name)
            self.event_bus.publish(Event('save_data'))
            self.show_playlists()