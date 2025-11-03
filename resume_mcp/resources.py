"""
Resource handlers for MCP server.

Provides access to:
- template:// - Example resume JSON files
- outbox:// - Generated DOCX files
"""

import json
from pathlib import Path
from typing import Optional


def get_template_resource(name: str) -> Optional[str]:
    """
    Get example resume template by name.
    
    Args:
        name: Template name (simple, full, with-summary)
        
    Returns:
        JSON string of template, or None if not found
    """
    # Map template names to files
    template_map = {
        "simple": "simple_resume.json",
        "full": "example_resume.json",
        "with-summary": "example_with_summary.json",
    }
    
    if name not in template_map:
        return None
    
    # Get project root (parent of mcp/)
    project_root = Path(__file__).parent.parent
    template_path = project_root / template_map[name]
    
    if not template_path.exists():
        return None
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Return formatted JSON
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return None


def list_templates() -> dict:
    """
    List available resume templates.
    
    Returns:
        Dictionary mapping template names to descriptions
    """
    return {
        "simple": "Minimal resume example with basic sections",
        "full": "Complete resume with traditional bullet format",
        "with-summary": "Resume with professional summary and subsections",
    }


def get_outbox_file(filename: str, outbox_dir: Path) -> Optional[bytes]:
    """
    Get generated DOCX file from outbox.
    
    Args:
        filename: Name of the DOCX file
        outbox_dir: Directory where files are stored
        
    Returns:
        Binary content of DOCX file, or None if not found
    """
    file_path = outbox_dir / filename
    
    if not file_path.exists() or not file_path.is_file():
        return None
    
    if not file_path.suffix.lower() == '.docx':
        return None
    
    try:
        return file_path.read_bytes()
    except Exception:
        return None


def list_outbox_files(outbox_dir: Path) -> list:
    """
    List all DOCX files in outbox.
    
    Args:
        outbox_dir: Directory to list files from
        
    Returns:
        List of filenames
    """
    if not outbox_dir.exists():
        return []
    
    try:
        return [
            f.name
            for f in outbox_dir.iterdir()
            if f.is_file() and f.suffix.lower() == '.docx'
        ]
    except Exception:
        return []
