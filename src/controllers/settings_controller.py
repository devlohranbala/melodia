from tkinter import messagebox, filedialog
from typing import Optional
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError as e:
    print(f"Dependência não encontrada: {e}")
    print("Execute: pip install customtkinter")
    import sys
    sys.exit(1)

from ..models import (
    SettingsDict, DEFAULT_VOLUME, DEFAULT_CROSSFADE_ENABLED, DEFAULT_CROSSFADE_DURATION, DEFAULT_AUDIO_OUTPUT
)
from ..ui import UIComponents, UIFactory
from ..core import Event, AppContext
from ..utils import get_audio_devices, get_device_name_by_id, set_audio_output_device
from .base_controller import BaseController


class SettingsController(BaseController):
    """Controller for settings functionality"""
    
    def __init__(self, app_context: AppContext):
        super().__init__(app_context)
        # Settings variables
        self.theme_var: Optional[ctk.StringVar] = None
        self.color_var: Optional[ctk.StringVar] = None
        self.default_volume_var: Optional[ctk.IntVar] = None
        self.crossfade_enabled_var: Optional[ctk.BooleanVar] = None
        self.crossfade_duration_var: Optional[ctk.IntVar] = None
        self.audio_output_var: Optional[ctk.StringVar] = None
        
        # UI references
        self.downloads_path_entry: Optional[ctk.CTkEntry] = None
        self.volume_value_label: Optional[ctk.CTkLabel] = None
        self.crossfade_duration_frame: Optional[ctk.CTkFrame] = None
        self.crossfade_duration_label: Optional[ctk.CTkLabel] = None
        
        # Saved values
        self.saved_theme = 'dark'
        self.saved_color_theme = 'blue'
        self.saved_default_volume = DEFAULT_VOLUME
        self.saved_crossfade_enabled = DEFAULT_CROSSFADE_ENABLED
        self.saved_crossfade_duration = DEFAULT_CROSSFADE_DURATION
        self.saved_audio_output = DEFAULT_AUDIO_OUTPUT
        
        # Audio devices cache
        self.audio_devices = []
    
    def initialize(self) -> None:
        """Initialize settings controller"""
        self._setup_event_handlers()
        self.load_and_apply_settings()
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers"""
        self.event_bus.subscribe('show_settings', lambda e: self.show_settings())
    
    def load_and_apply_settings(self) -> None:
        """Load and apply settings"""
        settings = self.context.settings_manager.load_settings()
        
        # Update downloads directory
        if (downloads_dir := settings.get('downloads_dir')) and Path(downloads_dir).exists():
            self.context.downloads_dir = Path(downloads_dir)
            self.context.download_manager.downloads_dir = self.context.downloads_dir
        
        # Apply theme
        theme = settings.get('theme', 'dark')
        color_theme = settings.get('color_theme', 'blue')
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme(color_theme)
        
        # Store values
        self.saved_theme = theme
        self.saved_color_theme = color_theme
        self.saved_default_volume = settings.get('default_volume', DEFAULT_VOLUME)
        self.saved_crossfade_enabled = settings.get('crossfade_enabled', DEFAULT_CROSSFADE_ENABLED)
        self.saved_crossfade_duration = settings.get('crossfade_duration', DEFAULT_CROSSFADE_DURATION)
        self.saved_audio_output = settings.get('audio_output', DEFAULT_AUDIO_OUTPUT)
        
        # Apply settings to player
        self.context.player.set_volume(self.saved_default_volume / 100)
        self.context.player.crossfade_enabled = self.saved_crossfade_enabled
        self.context.player.crossfade_duration = self.saved_crossfade_duration
        
        # Apply audio output device
        if self.saved_audio_output is not None:
            set_audio_output_device(self.saved_audio_output)
    
    def show_settings(self) -> None:
        """Show settings"""
        self.load_and_apply_settings()
        parent = self.context.view_frames['settings']
        UIComponents.clear_widget_children(parent)
        
        # Header
        UIFactory.create_content_header(parent, "Configurações", "⚙️ Personalize sua experiência musical")
        
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Main container
        main_container = ctk.CTkFrame(scroll, corner_radius=15)
        main_container.pack(fill="x")
        
        inner = ctk.CTkFrame(main_container, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Settings sections
        sections = [
            ("🎨 Aparência", self.create_appearance_section),
            ("🔊 Áudio", self.create_audio_section),
            ("📥 Downloads", self.create_downloads_section),
            ("ℹ️ Sobre", self.create_about_section)
        ]
        
        for title, create_func in sections:
            section = self._create_settings_section(inner, title)
            create_func(section)
    
    def _create_settings_section(self, parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
        """Create a settings section"""
        section = ctk.CTkFrame(parent, corner_radius=10)
        section.pack(fill="x", pady=(0, 20))
        
        inner = ctk.CTkFrame(section, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            inner,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(0, 15))
        
        return inner
    
    def create_appearance_section(self, parent: ctk.CTkFrame) -> None:
        """Create appearance section"""
        # Theme
        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            theme_frame,
            text="Tema:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")
        
        self.theme_var = ctk.StringVar(value=self.saved_theme)
        ctk.CTkOptionMenu(
            theme_frame,
            values=["dark", "light", "system"],
            variable=self.theme_var,
            command=self.change_theme
        ).pack(side="right")
        
        # Color theme
        color_frame = ctk.CTkFrame(parent, fg_color="transparent")
        color_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            color_frame,
            text="Cor do tema:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")
        
        self.color_var = ctk.StringVar(value=self.saved_color_theme)
        ctk.CTkOptionMenu(
            color_frame,
            values=["blue", "green", "dark-blue"],
            variable=self.color_var,
            command=self.change_color_theme
        ).pack(side="right")
    
    def create_audio_section(self, parent: ctk.CTkFrame) -> None:
        """Create audio section"""
        # Audio output device
        output_frame = ctk.CTkFrame(parent, fg_color="transparent")
        output_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            output_frame,
            text="Saída de áudio:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")
        
        # Get audio devices
        self.audio_devices = get_audio_devices()
        device_names = [device['name'] for device in self.audio_devices]
        
        # Find current device name
        current_device_name = get_device_name_by_id(self.saved_audio_output)
        if current_device_name not in device_names and device_names:
            current_device_name = device_names[0]
        
        self.audio_output_var = ctk.StringVar(value=current_device_name)
        ctk.CTkOptionMenu(
            output_frame,
            values=device_names if device_names else ["Sistema Padrão"],
            variable=self.audio_output_var,
            command=self.change_audio_output
        ).pack(side="right")
        
        # Default volume
        volume_frame = ctk.CTkFrame(parent, fg_color="transparent")
        volume_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            volume_frame,
            text="Volume padrão:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")
        
        self.default_volume_var = ctk.IntVar(value=self.saved_default_volume)
        volume_slider = ctk.CTkSlider(
            volume_frame,
            from_=0,
            to=100,
            variable=self.default_volume_var,
            command=self.change_default_volume
        )
        volume_slider.pack(side="right", padx=(10, 0))
        
        self.volume_value_label = ctk.CTkLabel(
            volume_frame,
            text=f"{self.saved_default_volume}%",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.volume_value_label.pack(side="right", padx=(10, 0))
        
        # Crossfade settings
        crossfade_frame = ctk.CTkFrame(parent, fg_color="transparent")
        crossfade_frame.pack(fill="x", pady=(15, 0))
        
        # Crossfade toggle
        crossfade_toggle_frame = ctk.CTkFrame(crossfade_frame, fg_color="transparent")
        crossfade_toggle_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            crossfade_toggle_frame,
            text="Ativar crossfade:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left")
        
        self.crossfade_enabled_var = ctk.BooleanVar(value=self.saved_crossfade_enabled)
        ctk.CTkSwitch(
            crossfade_toggle_frame,
            text="",
            variable=self.crossfade_enabled_var,
            command=self.toggle_crossfade_and_update_ui
        ).pack(side="right")
        
        # Crossfade duration
        self.crossfade_duration_frame = ctk.CTkFrame(crossfade_frame, fg_color="transparent")
        
        ctk.CTkLabel(
            self.crossfade_duration_frame,
            text="Duração do crossfade:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        
        self.crossfade_duration_var = ctk.IntVar(value=self.saved_crossfade_duration)
        ctk.CTkSlider(
            self.crossfade_duration_frame,
            from_=0,
            to=12,
            number_of_steps=12,
            variable=self.crossfade_duration_var,
            command=self.change_crossfade_duration
        ).pack(side="right", padx=(10, 0))
        
        self.crossfade_duration_label = ctk.CTkLabel(
            self.crossfade_duration_frame,
            text=f"{self.saved_crossfade_duration}s",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.crossfade_duration_label.pack(side="right", padx=(10, 0))
        
        # Show/hide duration frame
        if self.saved_crossfade_enabled:
            self.crossfade_duration_frame.pack(fill="x")
        
        # Description
        ctk.CTkLabel(
            crossfade_frame,
            text="O crossfade cria uma transição suave entre músicas,\nsobrepondo o final de uma com o início da próxima.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            justify="left"
        ).pack(anchor="w", pady=(10, 0))
    
    def create_downloads_section(self, parent: ctk.CTkFrame) -> None:
        """Create downloads section"""
        folder_frame = ctk.CTkFrame(parent, fg_color="transparent")
        folder_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            folder_frame,
            text="Pasta de downloads:",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=(0, 5))
        
        path_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
        path_frame.pack(fill="x")
        
        self.downloads_path_entry = ctk.CTkEntry(
            path_frame,
            placeholder_text="Caminho da pasta...",
            font=ctk.CTkFont(size=12)
        )
        self.downloads_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.downloads_path_entry.insert(0, str(self.context.downloads_dir))
        
        self.downloads_path_entry.bind("<FocusOut>", lambda e: self.auto_save_settings())
        self.downloads_path_entry.bind("<Return>", lambda e: self.auto_save_settings())
        
        ctk.CTkButton(
            path_frame,
            text="📁 Procurar",
            command=self.browse_downloads_folder,
            font=ctk.CTkFont(size=12),
            width=100
        ).pack(side="right")
    
    def create_about_section(self, parent: ctk.CTkFrame) -> None:
        """Create about section"""
        ctk.CTkLabel(
            parent,
            text="Melodia - Modern Music Player",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            parent,
            text="Versão 1.0.0",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            parent,
            text="https://github.com/devlohranbala/melodia/",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 15))
        
        ctk.CTkButton(
            parent,
            text="🔄 Restaurar Padrões",
            command=self.reset_settings,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors.warning,
            hover_color="#e68900"
        ).pack(anchor="w")
    
    def change_theme(self, theme: str) -> None:
        """Change theme"""
        ctk.set_appearance_mode(theme)
        self.saved_theme = theme
        self.auto_save_settings()
    
    def change_color_theme(self, color: str) -> None:
        """Change color theme"""
        ctk.set_default_color_theme(color)
        self.saved_color_theme = color
        self.auto_save_settings()
        messagebox.showinfo("Tema", "Reinicie a aplicação para aplicar a nova cor do tema.")
    
    def change_audio_output(self, device_name: str) -> None:
        """Change audio output device"""
        # Find device ID by name
        device_id = None
        for device in self.audio_devices:
            if device['name'] == device_name:
                device_id = device['id']
                break
        
        # Set the audio output device
        if set_audio_output_device(device_id):
            self.saved_audio_output = device_id
            self.auto_save_settings()
        else:
            # Show error message if setting failed
            from tkinter import messagebox
            messagebox.showerror("Erro", f"Não foi possível definir '{device_name}' como saída de áudio.")
    
    def change_default_volume(self, value: float) -> None:
        """Change default volume"""
        volume_percent = int(value)
        if self.volume_value_label:
            self.volume_value_label.configure(text=f"{volume_percent}%")
        
        # Update player volume
        self.event_bus.publish(Event('volume_changed', {'volume': volume_percent}))
        
        self.saved_default_volume = volume_percent
        self.auto_save_settings()
    
    def toggle_crossfade_and_update_ui(self) -> None:
        """Toggle crossfade and update UI"""
        if not self.crossfade_enabled_var:
            return
            
        enabled = self.crossfade_enabled_var.get()
        self.context.player.crossfade_enabled = enabled
        
        # Show/hide duration frame
        if self.crossfade_duration_frame:
            if enabled:
                self.crossfade_duration_frame.pack(fill="x")
            else:
                self.crossfade_duration_frame.pack_forget()
        
        self.auto_save_settings()
    
    def change_crossfade_duration(self, value: float) -> None:
        """Change crossfade duration"""
        duration = int(value)
        if self.crossfade_duration_label:
            self.crossfade_duration_label.configure(text=f"{duration}s")
        self.context.player.crossfade_duration = duration
        self.auto_save_settings()
    
    def browse_downloads_folder(self) -> None:
        """Browse downloads folder"""
        if folder := filedialog.askdirectory(title="Selecionar pasta de downloads"):
            if self.downloads_path_entry:
                self.downloads_path_entry.delete(0, "end")
                self.downloads_path_entry.insert(0, folder)
            self.auto_save_settings()
    
    def reset_settings(self) -> None:
        """Reset settings to defaults"""
        if messagebox.askyesno("Confirmar", "Restaurar todas as configurações para o padrão?"):
            if self.theme_var:
                self.theme_var.set("dark")
            if self.color_var:
                self.color_var.set("blue")
            if self.default_volume_var:
                self.default_volume_var.set(DEFAULT_VOLUME)
            if self.downloads_path_entry:
                self.downloads_path_entry.delete(0, "end")
                self.downloads_path_entry.insert(0, str(self.context.downloads_dir))
            
            # Reset audio output
            if self.audio_output_var and self.audio_devices:
                default_device_name = get_device_name_by_id(DEFAULT_AUDIO_OUTPUT)
                self.audio_output_var.set(default_device_name)
                set_audio_output_device(DEFAULT_AUDIO_OUTPUT)
            
            # Reset crossfade
            if self.crossfade_enabled_var:
                self.crossfade_enabled_var.set(DEFAULT_CROSSFADE_ENABLED)
                if self.crossfade_duration_frame:
                    if DEFAULT_CROSSFADE_ENABLED:
                        self.crossfade_duration_frame.pack(fill="x")
                    else:
                        self.crossfade_duration_frame.pack_forget()
            
            if self.crossfade_duration_var:
                self.crossfade_duration_var.set(DEFAULT_CROSSFADE_DURATION)
                if self.crossfade_duration_label:
                    self.crossfade_duration_label.configure(text=f"{DEFAULT_CROSSFADE_DURATION}s")
            
            ctk.set_appearance_mode("dark")
            
            # Update player
            self.event_bus.publish(Event('volume_changed', {'volume': DEFAULT_VOLUME}))
            
            self.auto_save_settings()
            messagebox.showinfo("Sucesso", "Configurações restauradas e salvas automaticamente!")
    
    def auto_save_settings(self) -> None:
        """Auto save settings"""
        try:
            # Update downloads directory
            if self.downloads_path_entry and (new_dir := self.downloads_path_entry.get().strip()):
                new_downloads_dir = Path(new_dir)
                if new_downloads_dir != self.context.downloads_dir:
                    new_downloads_dir.mkdir(exist_ok=True)
                    self.context.downloads_dir = new_downloads_dir
                    self.context.download_manager.downloads_dir = new_downloads_dir
            
            # Create settings dictionary
            settings: SettingsDict = {
                'theme': self.theme_var.get() if self.theme_var else 'dark',
                'color_theme': self.color_var.get() if self.color_var else 'blue',
                'default_volume': self.default_volume_var.get() if self.default_volume_var else DEFAULT_VOLUME,
                'downloads_dir': str(self.context.downloads_dir),
                'crossfade_enabled': self.crossfade_enabled_var.get() if self.crossfade_enabled_var else DEFAULT_CROSSFADE_ENABLED,
                'crossfade_duration': self.crossfade_duration_var.get() if self.crossfade_duration_var else DEFAULT_CROSSFADE_DURATION,
                'audio_output': self.saved_audio_output
            }
            
            # Save
            self.context.settings_manager.save_settings(settings)
            
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")