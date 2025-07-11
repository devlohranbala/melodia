from typing import Optional, Callable
from contextlib import suppress

try:
    import customtkinter as ctk
except ImportError as e:
    print(f"Dependência não encontrada: {e}")
    print("Execute: pip install customtkinter")
    import sys
    sys.exit(1)

class UIComponents:
    """UI components with modern static methods"""
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 25) -> str:
        """Truncate text with f-string"""
        return f"{text[:max_length]}..." if len(text) > max_length else text
        
    @staticmethod
    def create_action_button(
        parent,
        text: str,
        command: Callable,
        *,
        width: int = 40,
        height: int = 30,
        **kwargs
    ) -> ctk.CTkButton:
        """Create standardized action button"""
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            font=ctk.CTkFont(size=12),
            width=width,
            height=height,
            **kwargs
        )
        
    @staticmethod
    def create_base_card(
        parent,
        row: Optional[int] = None,
        col: Optional[int] = None
    ) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
        """Create modern minimalist base card"""
        # Modern card with subtle shadow effect and rounded corners
        card = ctk.CTkFrame(
            parent, 
            corner_radius=20,
            border_width=1,
            border_color=("gray75", "gray25")
        )
        
        match (row, col):
            case (int() as r, int() as c):
                card.grid(row=r, column=c, padx=15, pady=15, sticky="nsew")
                parent.grid_columnconfigure(c, weight=1)
            case _:
                card.pack(fill="x", padx=15, pady=8)
                
        # Inner container with more refined spacing
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        return card, inner
        
    @staticmethod
    def clear_widget_children(widget) -> None:
        """Clear widget children safely"""
        if widget and hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                with suppress(Exception):
                    child.destroy()
                    
    @staticmethod
    def create_empty_state(
        parent, 
        icon: str, 
        title: str, 
        subtitle: str
    ) -> None:
        """Create empty state UI"""
        empty_frame = ctk.CTkFrame(parent, fg_color="transparent")
        empty_frame.pack(expand=True, pady=100)
        
        ctk.CTkLabel(empty_frame, text=icon, font=ctk.CTkFont(size=72)).pack()
        ctk.CTkLabel(
            empty_frame,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        ctk.CTkLabel(
            empty_frame,
            text=subtitle,
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack()
