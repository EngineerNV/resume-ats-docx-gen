#!/usr/bin/env python3
"""
Quick start script for the Resume ATS DOCX Generator API.

This script starts the FastAPI server with the OpenAI Agents SDK integration.
"""

import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def check_env():
    """Check if .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("Please create a .env file with your OpenAI API key:")
        print()
        print("OPENAI_API_KEY=your_key_here")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)


def main():
    """Start the server."""
    print("="*80)
    print("Resume ATS DOCX Generator API")
    print("OpenAI Agents SDK Integration")
    print("="*80)
    print()
    
    check_env()
    
    print("Starting server...")
    print("Server will be available at: http://localhost:8000")
    print()
    print("Endpoints:")
    print("  GET  /                      - Health check")
    print("  POST /api/workflow/json     - Get JSON suggestions")
    print("  POST /api/workflow/docx     - Generate DOCX file")
    print()
    print("Press Ctrl+C to stop the server")
    print("="*80)
    print()
    
    # Start uvicorn
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api.server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
