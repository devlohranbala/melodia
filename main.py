import sys

try:
    import customtkinter as ctk
except ImportError as e:
    print(f"Dependência não encontrada: {e}")
    print("Execute: pip install customtkinter")
    sys.exit(1)

# Import the main application class
from src.music_app import MusicApp

# Configure customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ====================
# Application Entry Point
# ====================

def main() -> None:
    """Main entry point"""
    root = ctk.CTk()
    app = MusicApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()