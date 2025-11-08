"""
MCP Server for Resume Generation.

This FastMCP server enables AI agents to generate ATS-friendly resumes
in DOCX format from JSON data.

Key Features:
- Tool: generate_resume - Create DOCX from JSON with strict validation
- Resources: template:// - Access example resume templates
- Resources: outbox:// - Retrieve generated DOCX files
- STDIO transport for local MCP clients (Claude Desktop, VS Code)

Usage:
    # Run with MCP dev tool
    mcp dev mcp/server.py
    
    # Run directly
    python -m mcp.server
"""

from pathlib import Path
from typing import Union

from mcp.server.fastmcp import FastMCP
from mcp.types import BlobResourceContents, TextContent

from resume_mcp.models import ResumeGenerateRequest
from resume_mcp.tools import generate_resume_tool, get_outbox_location
from resume_mcp.resources import (
    get_template_resource,
    list_templates,
    get_outbox_file,
    list_outbox_files,
)


PROJECT_ROOT = Path(__file__).parent.parent
OUTBOX_DIR = PROJECT_ROOT / "outbox"
OUTBOX_DIR.mkdir(exist_ok=True)


# Initialize FastMCP server
mcp = FastMCP(
    name="resume-generator",
)


# Tool: Generate Resume
@mcp.tool()
def generate_resume(resume: dict, filename: str) -> str:
    """
    Generate an ATS-friendly resume DOCX file from JSON data.
    
    This tool creates a professionally formatted resume document optimized
    for Applicant Tracking Systems (ATS). It validates the input data strictly
    and provides detailed error messages if validation fails.
    
    Args:
        resume: Complete resume data including header, experience, education, etc.
                Must include: header.name, header.email, and at least one of
                (experience, education, skills)
        filename: Output filename (must end with .docx). Example: "john_doe_swe.docx"
    
    Returns:
        Success message with file location, or detailed error information
    
    Examples:
        See template:// resources for valid resume structure examples.
    
    Required Structure:
        {
            "header": {"name": "...", "email": "..."},
            "skills": {"Category": ["skill1", "skill2"]},
            "experience": [...],
            "education": [...]
        }
    """
    # Call tool implementation
    result = generate_resume_tool(resume, filename)
    
    # Format response for LLM
    if result["success"]:
        return (
            f"{result['message']}\n\n"
            f"File location: {result['path']}\n"
            f"Access via: {result['uri']}\n\n"
            f"You can retrieve the file using the outbox:// resource."
        )
    else:
        error_msg = [
            result["message"],
            "",
            result["details"],
        ]
        if "suggestion" in result:
            error_msg.append("")
            error_msg.append(result["suggestion"])
        
        return "\n".join(error_msg)


# Resource: Templates
@mcp.resource("template://{name}")
def get_template(name: str) -> str:
    """
    Get example resume template JSON.
    
    Available templates:
    - template://simple - Minimal resume example
    - template://full - Complete resume with traditional bullets
    - template://with-summary - Resume with professional summary and subsections
    
    Use these as reference when creating resume JSON.
    """
    content = get_template_resource(name)
    
    if content is None:
        available = ", ".join(list_templates().keys())
        return f"Template '{name}' not found. Available: {available}"
    
    return content


# Resource: Outbox Files
@mcp.resource("outbox://{filename}")
def get_outbox(filename: str) -> Union[BlobResourceContents, TextContent]:
    """
    Retrieve a generated DOCX file from the outbox.

    Example: outbox://john_doe_resume.docx
    """
    file_data = get_outbox_file(filename, OUTBOX_DIR)

    if file_data is None:
        available = list_outbox_files(OUTBOX_DIR)
        if available:
            files_list = "\n".join(f"  - {f}" for f in available)
            message = f"File '{filename}' not found in outbox.\n\nAvailable files:\n{files_list}"
        else:
            message = f"File '{filename}' not found. Outbox is empty."

        return TextContent(type="text", text=message)

    return BlobResourceContents(
        blob=file_data.decode('latin-1'),  # FastMCP expects string, not bytes
        mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# Entry point for direct execution
def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
