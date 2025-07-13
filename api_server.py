#!/usr/bin/env python3
"""
Melodia Music API Server

This is the standalone API server for Melodia Music Player.
It provides a REST API that can be used independently of the GUI frontend.
"""

import sys
import argparse
from pathlib import Path

try:
    import uvicorn
except ImportError:
    print("FastAPI dependencies not found. Install with:")
    print("pip install fastapi uvicorn")
    sys.exit(1)

from src.api.main import create_api


def main():
    """Main entry point for the API server"""
    parser = argparse.ArgumentParser(description="Melodia Music API Server")
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="Host to bind the server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--downloads-dir", 
        type=Path,
        default=Path.home() / "melodia",
        help="Directory for music downloads (default: ~/melodia)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level", 
        default="info", 
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level (default: info)"
    )
    
    args = parser.parse_args()
    
    # Ensure downloads directory exists
    args.downloads_dir.mkdir(exist_ok=True)
    
    print(f"Starting Melodia Music API Server...")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Downloads Directory: {args.downloads_dir}")
    print(f"API Documentation: http://{args.host}:{args.port}/docs")
    print(f"API Redoc: http://{args.host}:{args.port}/redoc")
    print("\nPress Ctrl+C to stop the server")
    
    # Create the FastAPI app
    app = create_api(args.downloads_dir)
    
    # Run the server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()