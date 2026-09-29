#!/usr/bin/env python3
"""
Simple script to run the BookBot API server.
Supports the $PORT environment variable for cloud hosting platforms
(Render, Railway, Fly.io, etc.)
"""
import uvicorn
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

if __name__ == "__main__":
    # Read PORT from environment — required by most cloud platforms.
    # Default to 8000 for local development.
    port = int(os.environ.get("PORT", 8000))
    is_dev = os.environ.get("ENVIRONMENT", "production") == "development"

    print("Starting BookBot API server...")
    print(f"Listening on: http://0.0.0.0:{port}")
    if is_dev:
        print(f"Swagger UI: http://localhost:{port}/docs")
    print("-" * 50)

    try:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=port,
            reload=is_dev,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
