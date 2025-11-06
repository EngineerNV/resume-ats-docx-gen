#!/usr/bin/env python
"""
Test the MCP Resume Agent workflow.

This script tests that the agent can:
1. Review optimized resume JSON
2. Determine an appropriate filename
3. Prepare data for MCP server communication
"""

import sys
import json
from pathlib import Path

def test_mcp_resume_agent():
    """Test the MCP Resume Agent functionality."""
    print("=" * 70)
    print("MCP Resume Agent Test")
    print("=" * 70)
    print()
    
    try:
        # Import required modules
        from agents.workflows import prepare_resume_for_mcp
        from agents.testing.fake_openai import FakeOpenAI, MockResponseSpec
        
        # Load example resume
        example_path = Path(__file__).parent / "example_resume.json"
        with open(example_path) as f:
            resume_data = json.load(f)
        
        print("Testing MCP Resume Agent with mock OpenAI...")
        print("-" * 70)
        
        # Create a mock response for the agent
        mock_response = {
            "filename": "john_doe_resume.docx",
            "resume_data": resume_data,
            "mcp_server_ready": True,
            "reasoning": "Generated filename from candidate name following professional naming conventions."
        }
        
        # Create a fake OpenAI client with the mock response
        mock_specs = [
            MockResponseSpec(kind="parse", parsed=mock_response)
        ]
        fake_client = FakeOpenAI.from_specs(mock_specs)
        
        # Run the MCP Resume Agent
        result = prepare_resume_for_mcp(resume_data, client=fake_client)
        
        print(f"Filename: {result.filename}")
        print(f"MCP Server Ready: {result.mcp_server_ready}")
        print(f"Reasoning: {result.reasoning}")
        print()
        
        # Verify the results
        assert result.filename.endswith('.docx'), "Filename should end with .docx"
        assert result.mcp_server_ready == True, "MCP server should be ready"
        assert result.resume_data is not None, "Resume data should be present"
        assert len(result.reasoning) > 0, "Reasoning should be provided"
        
        print("✅ MCP Resume Agent test passed!")
        print()
        print("The agent successfully:")
        print("  - Reviewed the optimized resume JSON")
        print("  - Determined an appropriate filename")
        print("  - Prepared data for MCP server communication")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ MCP Resume Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    if test_mcp_resume_agent():
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
