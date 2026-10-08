#!/usr/bin/env python3
"""
Run the BookBot API server.
"""
import os
import sys

import uvicorn

# Resolve api:app relative to this script, even when launched from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    environment = os.getenv("ENVIRONMENT", "development").lower()
    reload = environment == "development"

    print("Starting BookBot API server...")
    print(f"API will be available at: http://localhost:{port}")
    print(f"Docs (Swagger UI): http://localhost:{port}/docs")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=port,
            reload=reload,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
