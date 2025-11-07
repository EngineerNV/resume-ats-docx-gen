#!/usr/bin/env python
"""
Test the simplified DOCX generation without MCP server.

This script tests that:
1. The filename agent determines intelligent filenames
2. The generation tool is called directly (no MCP server)
3. DOCX files are created successfully
"""

import sys
import json
from pathlib import Path

def test_direct_generation():
    """Test direct DOCX generation without MCP server."""
    print("=" * 70)
    print("Direct DOCX Generation Test (No MCP Server)")
    print("=" * 70)
    print()
    
    try:
        # Import required modules
        from app_agents.workflows import prepare_resume_for_mcp
        from resume_mcp.tools import generate_resume_tool
        from app_agents.testing.fake_openai import FakeOpenAI, MockResponseSpec
        
        # Load example resume
        example_path = Path(__file__).parent / "example_resume.json"
        with open(example_path) as f:
            resume_data = json.load(f)
        
        print("Step 1: Testing filename agent...")
        print("-" * 70)
        
        # Create a mock response for the filename agent
        mock_filename_response = {
            "filename": "john_doe_resume.docx",
            "resume_data": resume_data,
            "mcp_server_ready": True,
            "reasoning": "Generated filename from candidate name."
        }
        
        # Create a fake OpenAI client with the mock response
        mock_specs = [
            MockResponseSpec(kind="parse", parsed=mock_filename_response)
        ]
        fake_client = FakeOpenAI.from_specs(mock_specs)
        
        # Run the filename agent
        filename_result = prepare_resume_for_mcp(resume_data, client=fake_client)
        
        print(f"✅ Filename determined: {filename_result.filename}")
        print(f"   Reasoning: {filename_result.reasoning}")
        print()
        
        print("Step 2: Testing direct generation (no MCP server)...")
        print("-" * 70)
        
        # Call the generation tool directly
        generation_result = generate_resume_tool(
            resume_data=filename_result.resume_data,
            filename=filename_result.filename
        )
        
        if generation_result["success"]:
            print(f"✅ DOCX generated: {generation_result['path']}")
            print(f"   Message: {generation_result['message']}")
            
            # Verify file exists
            docx_path = Path(generation_result["path"])
            if docx_path.exists():
                print(f"✅ File verified: {docx_path}")
            else:
                print(f"❌ File not found: {docx_path}")
                return False
        else:
            print(f"❌ Generation failed: {generation_result['message']}")
            return False
        
        print()
        print("=" * 70)
        print("✅ All tests passed!")
        print()
        print("Summary:")
        print("  - Filename agent determines intelligent names")
        print("  - Generation tool called directly (no MCP server)")
        print("  - DOCX file created successfully")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    if test_direct_generation():
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
