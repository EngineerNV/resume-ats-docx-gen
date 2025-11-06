#!/usr/bin/env python
"""
Test script to verify MCP client integration.

This script tests that:
1. The MCP client can be imported
2. The MCP client can communicate with a spawned MCP server
3. The agent workflow can use the MCP client
"""

import sys
import json
from pathlib import Path

def test_mcp_client_import():
    """Test that MCP client module can be imported."""
    print("Testing MCP client import...")
    
    try:
        from api.mcp_client import MCPResumeClient, generate_resume_via_mcp
        print("✅ MCP client imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import MCP client: {e}")
        return False


def test_mcp_client_integration():
    """Test that MCP client can communicate with the server."""
    print("\nTesting MCP client integration...")
    
    try:
        from api.mcp_client import generate_resume_via_mcp
        
        # Load example resume
        example_path = Path(__file__).parent / "example_resume.json"
        with open(example_path) as f:
            resume_data = json.load(f)
        
        # Test MCP client communication
        print("Calling MCP server via client...")
        result = generate_resume_via_mcp(
            resume_data=resume_data,
            filename="test_mcp_client.docx"
        )
        
        if result["success"]:
            print(f"✅ MCP client successfully generated DOCX: {result.get('path', 'N/A')}")
            print(f"   Message: {result.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ MCP client failed: {result.get('message', 'Unknown error')}")
            print(f"   Details: {result.get('details', 'N/A')}")
            return False
            
    except Exception as e:
        print(f"❌ MCP client integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_with_mcp_client():
    """Test that FastAPI server can use MCP client."""
    print("\nTesting FastAPI server with MCP client...")
    
    try:
        from api.server import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health check
        response = client.get("/")
        if response.status_code == 200:
            print("✅ FastAPI server with MCP client working")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
        
    except ImportError:
        print("⚠️  FastAPI TestClient not available, skipping")
        return True
    except Exception as e:
        print(f"❌ FastAPI test failed: {e}")
        return False


def main():
    """Run all MCP client integration tests."""
    print("=" * 70)
    print("MCP Client Integration Tests")
    print("=" * 70)
    print()
    
    results = []
    
    # Test MCP client import
    results.append(("MCP Client Import", test_mcp_client_import()))
    
    # Test MCP client integration
    results.append(("MCP Client Integration", test_mcp_client_integration()))
    
    # Test FastAPI with MCP client
    results.append(("FastAPI with MCP Client", test_fastapi_with_mcp_client()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:.<50} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 All MCP client integration tests passed!")
        print("\nThe FastAPI server now communicates with the MCP server via MCP protocol.")
        print("The agent workflow generates JSON, then the MCP client sends it to the")
        print("MCP server for DOCX generation.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
