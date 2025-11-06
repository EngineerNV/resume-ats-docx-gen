# MCP Resume Agent Implementation

## Overview

The MCP Resume Agent is a new OpenAI agent added to the workflow that coordinates the handoff between the resume optimization workflow and the MCP server for DOCX generation.

## What It Does

The MCP Resume Agent:

1. **Reviews the Optimized Resume JSON** - Takes the complete, optimized resume JSON from previous agents
2. **Determines Intelligent Filenames** - Generates professional, URL-safe filenames based on the candidate's name
   - Format: `firstname_lastname_resume.docx`
   - Example: "Jane Smith" → `jane_smith_resume.docx`
   - Fallback to `resume.docx` if name is missing/invalid
3. **Prepares MCP Communication** - Structures the data for sending to the MCP server
4. **Returns Metadata** - Provides reasoning about filename choice and confirms readiness

## Architecture Flow

### Before (Without MCP Resume Agent)
```
FastAPI → Agent Workflow → JSON → MCP Client (hardcoded "resume.docx") → MCP Server → DOCX
```

### After (With MCP Resume Agent)
```
FastAPI → Agent Workflow → Optimized JSON 
  → MCP Resume Agent (determines filename intelligently)
  → MCP Client → MCP Server → DOCX
```

## Agent Prompt

The agent uses the `MCP_RESUME_AGENT_INSTRUCTIONS` prompt which instructs it to:
- Extract the candidate's name from `resume.header.name`
- Generate a clean, professional filename
- Pass through the resume JSON unchanged
- Provide brief reasoning for the filename choice

## Implementation Files

### New Files Created

1. **`agents/workflows/mcp_resume_agent.py`**
   - Contains `prepare_resume_for_mcp()` function
   - Defines `MCPResumeAgentResult` dataclass
   - Implements the agent workflow logic

2. **`test_mcp_resume_agent.py`**
   - Test suite for the MCP Resume Agent
   - Validates filename generation and data preparation

### Modified Files

1. **`agents/prompts.py`**
   - Added `MCP_RESUME_AGENT_INSTRUCTIONS` prompt
   - Added to `__all__` exports

2. **`agents/workflows/__init__.py`**
   - Exported `prepare_resume_for_mcp` function
   - Exported `MCPResumeAgentResult` dataclass

3. **`api/server.py`**
   - Imported `prepare_resume_for_mcp`
   - Updated `/api/workflow/docx` endpoint to use MCP Resume Agent
   - Agent-determined filename now used in response

## Usage Example

```python
from agents.workflows import prepare_resume_for_mcp

# After getting optimized resume from workflow
optimized_resume = result.optimized_resume_json.parsed

# Use MCP Resume Agent to prepare for DOCX generation
mcp_agent_result = prepare_resume_for_mcp(optimized_resume)

print(f"Filename: {mcp_agent_result.filename}")
# Output: Filename: jane_smith_resume.docx

print(f"Reasoning: {mcp_agent_result.reasoning}")
# Output: Reasoning: Generated filename from candidate name 'Jane Smith' following professional naming conventions.

# Send to MCP server
mcp_result = generate_resume_via_mcp(
    resume_data=mcp_agent_result.resume_data,
    filename=mcp_agent_result.filename
)
```

## Benefits

1. **Agent Controls Filename** - The agent, not hardcoded logic, determines the filename
2. **Intelligent Naming** - Names reflect the actual candidate's name
3. **Professional Format** - Follows URL-safe, professional naming conventions
4. **Extensible** - Easy to add more logic (e.g., job title in filename, date stamps, etc.)
5. **Better Error Messages** - Agent reasoning included in error responses
6. **Separation of Concerns** - MCP coordination logic is in a dedicated agent

## Future Enhancements

Potential improvements to the MCP Resume Agent:

- Include job title or company in filename (e.g., `jane_smith_google_swe_resume.docx`)
- Add timestamp for version tracking
- Support multiple output formats (PDF, HTML)
- Intelligent file organization (folders by date, role, etc.)
- Resume versioning and comparison

## Testing

Run the test suite:
```bash
python test_mcp_resume_agent.py
```

Expected output:
```
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
