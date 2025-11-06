"""
MCP client for communicating with the resume MCP server.

This module provides functionality to connect to a running MCP server
and call its tools to generate resume DOCX files.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession


class MCPResumeClient:
    """Client for communicating with the resume MCP server."""
    
    def __init__(self, server_command: Optional[str] = None, server_args: Optional[list] = None):
        """
        Initialize the MCP client.
        
        Args:
            server_command: Command to spawn the MCP server (default: python)
            server_args: Arguments to pass to the server (default: ["-m", "resume_mcp.server"])
        """
        self.server_command = server_command or "python"
        self.server_args = server_args or ["-m", "resume_mcp.server"]
        
    @asynccontextmanager
    async def connect(self):
        """
        Connect to the MCP server and yield a session.
        
        This spawns the MCP server process and establishes a connection.
        """
        server_params = StdioServerParameters(
            command=self.server_command,
            args=self.server_args,
            env=None,
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                yield session
    
    async def generate_resume(self, resume_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """
        Generate a resume DOCX file using the MCP server.
        
        Args:
            resume_data: Complete resume data as a dictionary
            filename: Output filename for the DOCX file
            
        Returns:
            Dictionary with result information:
            - success: Boolean indicating success/failure
            - path: Path to generated file (if successful)
            - uri: MCP resource URI (if successful)
            - message: Success/error message
            - error: Error code (if failed)
            - details: Additional error details (if failed)
        """
        try:
            async with self.connect() as session:
                # Call the generate_resume tool on the MCP server
                result = await session.call_tool(
                    "generate_resume",
                    arguments={
                        "resume": resume_data,
                        "filename": filename
                    }
                )
                
                # Parse the result
                if result.content:
                    # The MCP server returns text content with the result
                    content_text = result.content[0].text if result.content else ""
                    
                    # Check if it was successful
                    if "✅" in content_text or "generated successfully" in content_text.lower():
                        # Parse the path and URI from the response
                        lines = content_text.split("\n")
                        path = None
                        uri = None
                        
                        for line in lines:
                            if "File location:" in line:
                                path = line.split("File location:")[-1].strip()
                            elif "Access via:" in line:
                                uri = line.split("Access via:")[-1].strip()
                        
                        return {
                            "success": True,
                            "message": content_text.split("\n")[0],
                            "path": path,
                            "uri": uri,
                            "filename": filename,
                        }
                    else:
                        # Parse error details
                        return {
                            "success": False,
                            "error": "mcp_tool_error",
                            "message": content_text.split("\n")[0] if content_text else "MCP tool failed",
                            "details": content_text,
                        }
                else:
                    return {
                        "success": False,
                        "error": "no_response",
                        "message": "MCP server returned no response",
                        "details": str(result),
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": "mcp_connection_error",
                "message": f"Failed to communicate with MCP server: {str(e)}",
                "details": f"Error type: {type(e).__name__}\n{str(e)}",
            }


def generate_resume_via_mcp(resume_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for generating a resume via the MCP server.
    
    This function creates an event loop and calls the async MCP client.
    
    Args:
        resume_data: Complete resume data as a dictionary
        filename: Output filename for the DOCX file
        
    Returns:
        Dictionary with result information (same as MCPResumeClient.generate_resume)
    """
    client = MCPResumeClient()
    
    # Run the async function in a new event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(client.generate_resume(resume_data, filename))
