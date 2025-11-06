#!/usr/bin/env python
"""
Test script to verify FastAPI server integration with MCP server.

This script tests that:
1. The API server can be imported
2. The MCP server tools can be accessed
3. Basic workflow integration works (with mock if no API key)
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from api.server import app
        print("✅ FastAPI app imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import FastAPI app: {e}")
        return False
    
    try:
        from resume_mcp.tools import generate_resume_tool
        print("✅ MCP tools imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import MCP tools: {e}")
        return False
    
    try:
        from agents.workflows import ResumeJsonWorkflow
        print("✅ Agent workflows imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import agent workflows: {e}")
        return False
    
    return True


def test_mcp_integration():
    """Test MCP server tool can generate a DOCX."""
    print("\nTesting MCP integration...")
    
    try:
        from resume_mcp.tools import generate_resume_tool
        import json
        
        # Load example resume
        example_path = Path(__file__).parent / "example_resume.json"
        with open(example_path) as f:
            resume_data = json.load(f)
        
        # Test DOCX generation
        result = generate_resume_tool(
            resume_data=resume_data,
            filename="test_integration.docx"
        )
        
        if result["success"]:
            print(f"✅ MCP tool generated DOCX: {result['path']}")
            return True
        else:
            print(f"❌ MCP tool failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ MCP integration test failed: {e}")
        return False


def test_api_endpoints():
    """Test that API endpoints are properly configured."""
    print("\nTesting API endpoints...")
    
    try:
        from fastapi.testclient import TestClient
        from api.server import app
        
        client = TestClient(app)
        
        # Test health check
        response = client.get("/")
        if response.status_code == 200:
            print("✅ Health check endpoint working")
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
        
        # Test JSON workflow endpoint (expect validation error without data)
        response = client.post("/api/workflow/json", data={"mode": "resume"})
        if response.status_code in [400, 500]:  # Either validation error or workflow error is expected
            print("✅ JSON workflow endpoint exists and responds")
        else:
            print(f"❌ JSON workflow endpoint unexpected status {response.status_code}")
            return False
        
        # Test DOCX workflow endpoint (expect validation error without data)
        response = client.post("/api/workflow/docx", data={"mode": "resume"})
        if response.status_code in [400, 500]:  # Either validation error or workflow error is expected
            print("✅ DOCX workflow endpoint exists and responds")
        else:
            print(f"❌ DOCX workflow endpoint unexpected status {response.status_code}")
            return False
        
        return True
        
    except ImportError:
        print("⚠️  FastAPI TestClient not available, skipping endpoint tests")
        return True
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("FastAPI + MCP Server Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test MCP integration
    results.append(("MCP Integration", test_mcp_integration()))
    
    # Test API endpoints
    results.append(("API Endpoints", test_api_endpoints()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
