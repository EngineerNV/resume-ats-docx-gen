# Resume MCP Server

This is a Model Context Protocol (MCP) server for generating ATS-friendly resumes in DOCX format.

## Quick Start

### Installation

```bash
# Install dependencies (in virtual environment)
source .venv/bin/activate
pip install -e .
```

### Testing Locally

```bash
# Run the test script
python test_mcp.py

# Or test with MCP Inspector (if you have it installed)
mcp dev resume_mcp/server.py
```

### Integration with AI Clients

#### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "resume-generator": {
      "command": "python",
      "args": ["-m", "resume_mcp.server"],
      "cwd": "/absolute/path/to/resume-ats-docx-gen",
      "env": {
        "PATH": "/absolute/path/to/resume-ats-docx-gen/.venv/bin:/usr/bin:/bin"
      }
    }
  }
}
```

## Architecture

```
resume_mcp/
├── __init__.py       # Package initialization
├── server.py         # FastMCP server with tool and resource registration
├── models.py         # Pydantic validation models (strict schema enforcement)
├── tools.py          # generate_resume tool implementation
└── resources.py      # template:// and outbox:// resource handlers
```

## Features

### Tool: `generate_resume`

Generates a DOCX resume from JSON data with strict validation.

**Parameters:**
- `resume` (dict): Resume data matching the schema
- `filename` (str): Output filename (must end with .docx)

**Returns:**
- Success: File path and URI to access generated DOCX
- Error: Detailed validation errors with suggestions

**Example:**
```python
generate_resume(
    resume={
        "header": {"name": "John Doe", "email": "john@example.com"},
        "skills": {"Languages": ["Python", "JavaScript"]},
        "experience": [...]
    },
    filename="john_doe_resume.docx"
)
```

### Resources

**Templates** - View example resume structures:
- `template://simple` - Minimal resume
- `template://full` - Complete traditional format
- `template://with-summary` - With professional summary

**Outbox** - Access generated files:
- `outbox://filename.docx` - Retrieve generated DOCX

## Key Design Decisions

### 1. **Direct Generator Integration**
- Uses `resume_gen.generator` directly (no CLI wrapper)
- Provides structured error messages instead of parsing stdout/stderr
- Better performance and cleaner error handling

### 2. **Strict Validation**
- Pydantic models enforce schema compliance
- Fails fast with detailed error messages
- Tells LLMs exactly what's wrong and how to fix it

### 3. **Project Outbox for Output**
- Generated files are saved to `<repo>/outbox/`
- Accessible via `outbox://` resources

### 4. **Filename Required**
- LLMs must provide explicit filename
- Prevents auto-naming conflicts
- Clear intent from the agent

## Error Handling

The server provides detailed, actionable errors:

```
❌ Resume validation failed. Fix the following issues:
  • header.email: field required
  • experience[0].bullets: Must provide either 'bullets' or 'subsections'

Review the required schema. Use template:// resources to see valid examples.
```

## Testing

```bash
# Test tool directly
python test_mcp.py

# Expected output:
# ✅ Success! Resume generated at:
#    /var/folders/.../resume-mcp-outbox/test_mcp_output.docx
#
# 📄 Access via MCP resource:
#    outbox://test_mcp_output.docx
```

## Known Limitations

1. **Optional fields in generator**: The original `generator.py` assumes `linkedin` and `github` are either present or not used (doesn't handle `None` gracefully). Use `example_resume.json` as a template which has these fields.

2. **Skills format flexibility**: Supports both `["skill1", "skill2"]` and `{"Category": ["skill1"]}` formats to match the existing generator capabilities.

## Future Enhancements

- [ ] Add validation-only tool (dry-run without generation)
- [ ] Add prompt templates for resume building
- [ ] Support config overrides via tool parameters
- [ ] Add SSE transport for web-based clients
- [ ] Add resume comparison/diff tool
- [ ] PDF export option

## Troubleshooting

### Import Error: `'mcp.server' is not a package`

**Problem**: Package naming conflict with installed `mcp` package.

**Solution**: We renamed to `resume_mcp` to avoid conflict.

### Validation Failed: "field required"

**Problem**: Missing required fields in resume JSON.

**Solution**: Check error message for specific missing fields. Use `template://` resources to see valid examples.

### Permission Denied

**Problem**: Cannot write to output directory.

**Solution**: Check temp directory permissions. On macOS, this should work by default.

## Contributing

When adding new features:

1. Update Pydantic models in `models.py` for new fields
2. Add tool logic in `tools.py`
3. Update server registration in `server.py`
4. Add tests in `test_mcp.py`
5. Update this README

## License

MIT (same as parent project)
