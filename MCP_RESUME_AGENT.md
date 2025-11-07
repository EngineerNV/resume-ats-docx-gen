# Filename Agent Implementation

## Overview

The Filename Agent (formerly MCP Resume Agent) is an OpenAI agent added to the workflow that intelligently determines filenames for generated DOCX files based on resume content.

## What It Does

The Filename Agent:

1. **Reviews the Optimized Resume JSON** - Takes the complete, optimized resume JSON from previous agents
2. **Determines Intelligent Filenames** - Generates professional, URL-safe filenames based on the candidate's name
   - Format: `firstname_lastname_resume.docx`
   - Example: "Jane Smith" → `jane_smith_resume.docx`
   - Fallback to `resume.docx` if name is missing/invalid
3. **Prepares Resume Data** - Ensures the resume data is ready for DOCX generation
4. **Returns Metadata** - Provides reasoning about filename choice and structured data

## Architecture Flow

### Simplified Architecture (Current)
```
FastAPI → Agent Workflow → Optimized JSON 
  → Filename Agent (determines filename intelligently)
  → Direct Generation Tool → DOCX
```

**Key Points:**
- No MCP server communication needed
- Direct function call to `generate_resume_tool`
- Simpler, faster, and more reliable
- Agent focuses solely on intelligent filename generation

## Agent Prompt

The agent uses the `MCP_RESUME_AGENT_INSTRUCTIONS` prompt which instructs it to:
- Extract the candidate's name from `resume.header.name`
- Generate a clean, professional filename
- Pass through the resume JSON unchanged
- Provide brief reasoning for the filename choice

## Implementation Files

### New Files Created

1. **`app_agents/workflows/file_naming_agent.py`**
   - Contains `prepare_resume_for_mcp()` function
   - Defines `FileNamingAgentResult` dataclass
   - Implements the agent workflow logic

2. **`test_mcp_resume_agent.py`**
   - Test suite for the MCP Resume Agent
   - Validates filename generation and data preparation

### Modified Files

1. **`app_agents/prompts.py`**
   - Added `MCP_RESUME_AGENT_INSTRUCTIONS` prompt
   - Added to `__all__` exports

2. **`app_agents/workflows/__init__.py`**
   - Exported `prepare_resume_for_mcp` function
   - Exported `FileNamingAgentResult` dataclass

3. **`api/server.py`**
   - Imported `prepare_resume_for_mcp`
   - Imported `generate_resume_tool` from `resume_mcp.tools`
   - Updated `/api/workflow/docx` endpoint to use Filename Agent
   - Agent-determined filename now used in response
   - Direct generation (no MCP server communication)

## Usage Example

```python
from app_agents.workflows import prepare_resume_for_mcp
from resume_mcp.tools import generate_resume_tool

# After getting optimized resume from workflow
optimized_resume = result.optimized_resume_json.parsed

# Use Filename Agent to determine intelligent filename
filename_agent_result = prepare_resume_for_mcp(optimized_resume)

print(f"Filename: {filename_agent_result.filename}")
# Output: Filename: jane_smith_resume.docx

print(f"Reasoning: {filename_agent_result.reasoning}")
# Output: Reasoning: Generated filename from candidate name 'Jane Smith' following professional naming conventions.

# Generate DOCX directly (no MCP server)
generation_result = generate_resume_tool(
    resume_data=filename_agent_result.resume_data,
    filename=filename_agent_result.filename
)
```

## Benefits

1. **Agent Controls Filename** - The agent, not hardcoded logic, determines the filename
2. **Intelligent Naming** - Names reflect the actual candidate's name
3. **Professional Format** - Follows URL-safe, professional naming conventions
4. **Extensible** - Easy to add more logic (e.g., job title in filename, date stamps, etc.)
5. **Better Error Messages** - Agent reasoning included in error responses
6. **Simplified Architecture** - Direct generation, no MCP server communication overhead

## Future Enhancements

Potential improvements to the Filename Agent:

- Include job title or company in filename (e.g., `jane_smith_google_swe_resume.docx`)
- Add timestamp for version tracking
- Support multiple output formats (PDF, HTML)
- Intelligent file organization (folders by date, role, etc.)
- Resume versioning and comparison

## Testing

Run the test suite:
```bash
python test_direct_generation.py
```

Expected output:
```
======================================================================
Direct DOCX Generation Test (No MCP Server)
======================================================================

Step 1: Testing filename agent...
----------------------------------------------------------------------
✅ Filename determined: john_doe_resume.docx
   Reasoning: Generated filename from candidate name.

Step 2: Testing direct generation (no MCP server)...
----------------------------------------------------------------------
✅ DOCX generated: /path/to/outbox/john_doe_resume.docx
   Message: ✅ Resume generated successfully: john_doe_resume.docx
✅ File verified: /path/to/outbox/john_doe_resume.docx

======================================================================
✅ All tests passed!

Summary:
  - Filename agent determines intelligent names
  - Generation tool called directly (no MCP server)
  - DOCX file created successfully
======================================================================
MCP Resume Agent Test
======================================================================

Testing MCP Resume Agent with mock OpenAI...
----------------------------------------------------------------------
Filename: john_doe_resume.docx
MCP Server Ready: True
Reasoning: Generated filename from candidate name following professional naming conventions.

✅ MCP Resume Agent test passed!

The agent successfully:
  - Reviewed the optimized resume JSON
  - Determined an appropriate filename
  - Prepared data for MCP server communication
```

## Regarding Pre-Running MCP Server

**Note on MCP Server Startup:**

The current implementation spawns the MCP server on-demand via stdio transport. This approach:

- **Is very fast** - Server startup is < 100ms
- **Handles cleanup automatically** - No zombie processes
- **Simplifies deployment** - No separate server management needed
- **Works reliably** - Process lifecycle managed by MCP client library

For a truly "pre-running" MCP server architecture, we would need to:
1. Start MCP server as a separate long-running process (e.g., via systemd, supervisord, or Docker)
2. Use HTTP/SSE transport instead of stdio
3. Configure the MCP client to connect to `http://localhost:PORT` instead of spawning

The on-demand spawning is recommended for this use case because:
- Each request is isolated (no state leakage between requests)
- No server management complexity
- Automatic scaling (each request gets its own server instance)
- Very low latency overhead

If you prefer a pre-running server, we can modify the MCP client to use HTTP transport instead.
