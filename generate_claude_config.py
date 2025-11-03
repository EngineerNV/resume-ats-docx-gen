#!/usr/bin/env python3
"""
Helper script to generate Claude Desktop configuration for this MCP server.

Usage:
    python generate_claude_config.py

This will print the configuration snippet you can add to:
    ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
    %APPDATA%/Claude/claude_desktop_config.json (Windows)
"""

import json
import os
import sys
from pathlib import Path

def get_config():
    """Generate Claude Desktop MCP server configuration."""
    
    # Get absolute path to project
    project_root = Path(__file__).parent.absolute()
    
    # Get python path in venv
    venv_python = project_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = sys.executable
    
    # Get system PATH
    current_path = os.environ.get("PATH", "/usr/bin:/bin")
    venv_bin = str(project_root / ".venv" / "bin")
    enhanced_path = f"{venv_bin}:{current_path}"
    
    config = {
        "mcpServers": {
            "resume-generator": {
                "command": str(venv_python),
                "args": ["-m", "resume_mcp.server"],
                "cwd": str(project_root),
                "env": {
                    "PATH": enhanced_path
                }
            }
        }
    }
    
    return config

def main():
    config = get_config()
    
    print("=" * 70)
    print("Claude Desktop MCP Server Configuration")
    print("=" * 70)
    print()
    print("Add this to your Claude Desktop config file:")
    print()
    
    if sys.platform == "darwin":
        config_path = "~/Library/Application Support/Claude/claude_desktop_config.json"
    elif sys.platform == "win32":
        config_path = "%APPDATA%/Claude/claude_desktop_config.json"
    else:
        config_path = "~/.config/claude/claude_desktop_config.json"
    
    print(f"Config file location: {config_path}")
    print()
    print(json.dumps(config, indent=2))
    print()
    print("=" * 70)
    print()
    print("After adding this config:")
    print("1. Restart Claude Desktop")
    print("2. The 'resume-generator' tool will be available in chat")
    print("3. Try asking: 'Generate a resume for a software engineer'")
    print()

if __name__ == "__main__":
    main()
