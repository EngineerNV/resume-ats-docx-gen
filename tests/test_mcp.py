#!/usr/bin/env python
"""
Quick test script to verify MCP server functionality.
"""

import json
from resume_mcp.tools import generate_resume_tool

# Load an example resume
with open('example_resume.json', 'r') as f:
    resume_data = json.load(f)

# Test the generate_resume tool
print("Testing generate_resume tool...")
print("=" * 60)

result = generate_resume_tool(
    resume_data=resume_data,
    filename="test_mcp_output.docx"
)

print(json.dumps(result, indent=2))
print("=" * 60)

if result["success"]:
    print(f"\n✅ Success! Resume generated at:")
    print(f"   {result['path']}")
    print(f"\n📄 Access via MCP resource:")
    print(f"   {result['uri']}")
else:
    print(f"\n❌ Error: {result['error']}")
    print(f"   {result['message']}")
