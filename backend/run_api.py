#!/usr/bin/env python3
"""
Simple script to run the BookBot API server
"""
import uvicorn
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

if __name__ == "__main__":
    print("🚀 Starting BookBot API server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 Frontend should connect to: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # Auto-reload on code changes
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
