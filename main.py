import sys
import threading
import time
from pathlib import Path

try:
    import customtkinter as ctk
except ImportError as e:
    print(f"Dependência não encontrada: {e}")
    print("Execute: pip install customtkinter")
    sys.exit(1)

try:
    import uvicorn
except ImportError as e:
    print(f"Dependência não encontrada: {e}")
    print("Execute: pip install fastapi uvicorn")
    sys.exit(1)

# Import the main application class
from src.music_app import MusicApp
from src.api.main import create_api
from src.api.client import get_api_client

# Configure customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def start_api_server(downloads_dir: Path, host: str = "127.0.0.1", port: int = 8000):
    """Start the API server in a separate thread"""
    app = create_api(downloads_dir)
    
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="warning",  # Reduce log noise
        access_log=False
    )
    
    server = uvicorn.Server(config)
    server.run()


def wait_for_api(max_attempts: int = 30, delay: float = 0.5) -> bool:
    """Wait for API to be available"""
    client = get_api_client()
    
    for attempt in range(max_attempts):
        try:
            if client.is_api_available():
                print("✅ API is ready!")
                return True
        except Exception:
            pass
        
        print(f"⏳ Waiting for API... (attempt {attempt + 1}/{max_attempts})")
        time.sleep(delay)
    
    return False


def main() -> None:
    """Main entry point that starts both API and GUI"""
    print("🎵 Starting Melodia Music Player with API...")
    
    # Setup directories
    downloads_dir = Path.home() / "melodia"
    downloads_dir.mkdir(exist_ok=True)
    
    # API configuration
    api_host = "127.0.0.1"
    api_port = 8000
    api_url = f"http://{api_host}:{api_port}"
    
    print(f"🚀 Starting API server at {api_url}")
    
    # Start API server in background thread
    api_thread = threading.Thread(
        target=start_api_server,
        args=(downloads_dir, api_host, api_port),
        daemon=True
    )
    api_thread.start()
    
    # Wait for API to be ready
    if not wait_for_api():
        print("❌ Failed to start API server. Exiting...")
        sys.exit(1)
    
    print(f"🎨 Starting GUI frontend...")
    print(f"📖 API Documentation available at: {api_url}/docs")
    
    # Start GUI
    try:
        root = ctk.CTk()
        app = MusicApp(root, api_url=api_url)
        
        print("✅ Melodia is ready! Enjoy your music! 🎵")
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down Melodia...")
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()