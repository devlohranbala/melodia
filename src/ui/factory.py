from typing import Callable
import customtkinter as ctk
from .components import UIComponents


class UIFactory:
    """Factory for creating UI components"""
    
    @staticmethod
    def create_nav_button(
        parent: ctk.CTkFrame,
        icon: str,
        text: str,
        command: Callable[[], None]
    ) -> ctk.CTkButton:
        """Create navigation button"""
        btn = ctk.CTkButton(
            parent,
            text=f"{icon} {text}",
            command=command,
            font=ctk.CTkFont(size=14),
            height=40,
            anchor="w",
            fg_color="transparent"
        )
        btn.pack(fill="x", pady=5)
        return btn
    
    @staticmethod
    def create_content_header(parent: ctk.CTkFrame, title: str, subtitle: str) -> ctk.CTkFrame:
        """Create content area header"""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text=subtitle,
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(anchor="w", pady=(5, 0))
        
        return header
    
    @staticmethod
    def create_scrollable_view(
        parent: ctk.CTkFrame,
        title: str,
        subtitle: str
    ) -> ctk.CTkScrollableFrame:
        """Create scrollable view with header"""
        UIComponents.clear_widget_children(parent)
        UIFactory.create_content_header(parent, title, subtitle)
        
        scroll = ctk.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        return scroll