# resume-ats-docx-gen

A Python CLI tool that generates ATS-friendly resumes in DOCX format from JSON input.

## Architecture Overview

This repository provides three main components:

1. **CLI Tool** (`resume-gen`): Generate DOCX files directly from JSON
2. **MCP Server** (`resume-mcp`): Model Context Protocol server for AI agent integration
3. **FastAPI Server** (`resume-api`): REST API for frontend integration with AI agent workflows

## Frontend UI (Beta)

The repository now includes a Next.js App Router frontend (`frontend/`) that collects resume inputs, supports job-tuning context, and proxies requests to the workflow APIs. See [`frontend/README.md`](frontend/README.md) for setup instructions.

## Features

- **ATS-Optimized Format**: Single column layout optimized for Applicant Tracking Systems
- **Professional Typography**: Calibri font with proper sizing (11pt body, 16pt name, 12pt headers)
- **Structured Sections**: Header, Skills, Experience, Education, and Awards
- **Action-Oriented**: Experience bullets designed to start with strong action verbs
- **No Tables or Images**: Clean, parseable format without complex elements
- **Clickable Links**: Email, LinkedIn, and GitHub links are clickable in the generated document
- **Flexible Experience Format**: Support for both traditional bullets and organized subsections
- **Compact Spacing**: Professional, tight spacing that maximizes content on each page

## Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/EngineerNV/resume-ats-docx-gen.git
cd resume-ats-docx-gen

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install the package with all dependencies
pip install -e .

# Configure your OpenAI API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Verify Installation

```bash
# Test the CLI tool
resume-gen --help

# Test the MCP server imports correctly
python -c "from resume_mcp.server import mcp; print('✅ MCP server ready')"

# Test the API server
python test_api_integration.py
```

## Quick Start

### Option 1: CLI Tool (Direct JSON to DOCX)

Generate a resume from a JSON file:

```bash
resume-gen render --in draft.json --out resume.docx
```

### Option 2: FastAPI Server (Frontend Integration)

Start the API server for frontend integration:

```bash
# Start the FastAPI server
resume-api

# Or with auto-reload for development
uvicorn api.server:app --reload
```

The server will be available at `http://localhost:8000`

**API Endpoints:**
- `POST /api/workflow/json` - Get AI-optimized resume JSON suggestions
- `POST /api/workflow/docx` - Generate and download optimized DOCX resume

See [`api/README.md`](api/README.md) for detailed API documentation.

### Option 3: MCP Server (AI Agent Integration)

Run the MCP server for AI agent tools:

```bash
python -m resume_mcp.server
```

Configure your AI client (Claude, VS Code Copilot) to use the MCP server. See [MCP Server](#mcp-server) section below for details.

## Command Line Usage

### Command Options

- `--in`: Path to input JSON file (required)
- `--out`: Path to output DOCX file (required)

## JSON Format

The input JSON should follow this structure:

```json
{
  "header": {
    "name": "Your Name",
    "email": "your.email@example.com",
    "location": "City, State",
    "linkedin": "linkedin.com/in/yourprofile",
    "github": "github.com/yourusername"
  },
  "professional_summary": "Brief professional overview (optional)",
  "skills": {
    "Category 1": ["Skill 1", "Skill 2", "Skill 3"],
    "Category 2": ["Skill A", "Skill B"]
  },
  "experience": [
    {
      "role": "Job Title",
      "company": "Company Name",
      "dates": "Month Year - Present",
      "location": "City, State",
      "bullets": [
        "Action verb describing achievement with quantifiable results",
        "Another accomplishment starting with action verb"
      ]
    },
    {
      "role": "Another Job Title",
      "company": "Another Company",
      "dates": "Month Year - Month Year",
      "location": "City, State",
      "subsections": [
        {
          "header": "Category or Focus Area",
          "bullets": [
            "Achievement in this category",
            "Another achievement in this category"
          ]
        },
        {
          "header": "Another Category",
          "bullets": [
            "Achievement in different focus area"
          ]
        }
      ]
    }
  ],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "University Name",
      "dates": "Year - Year",
      "location": "City, State",
      "gpa": "3.X/4.0"
    }
  ],
  "awards": [
    "Award Name (Year)",
    {
      "title": "Award Title",
      "date": "Year",
      "description": "Brief description"
    }
  ]
}
```

See `example_resume.json` for a complete example with traditional bullets, or `john_doe_resume.json` for an example using subsections.

## Configuration

The tool uses a `config.json` file in the `resume_gen/` directory to control formatting and styling. You can customize:

- **Fonts**: Primary font, fallback font
- **Font Sizes**: Body text, name, section headers
- **Spacing**: Margins, paragraph spacing, bullet spacing
- **Colors**: Text color, hyperlink color
- **Formatting**: Underlines, italics, separators

To customize, edit `resume_gen/config.json` before running the tool.

## Advanced Features

### Professional Summary (Optional)

Add a professional summary section that appears before skills and experience:

```json
{
  "professional_summary": "Experienced software engineer with 5+ years building scalable web applications..."
}
```

Or use multiple paragraphs:

```json
{
  "professional_summary": [
    "First paragraph of summary...",
    "Second paragraph providing more detail..."
  ]
}
```

### Clickable Links

Email, LinkedIn, and GitHub URLs in the header section are automatically converted to clickable hyperlinks in the generated document. The tool automatically adds `https://` to LinkedIn and GitHub URLs if not already present.

### Experience Subsections (Optional)

For complex roles with multiple focus areas, you can organize bullets into subsections. This is completely optional - traditional `bullets` format still works perfectly.

**Traditional Format (still supported):**
```json
{
  "role": "Software Engineer",
  "company": "Tech Corp",
  "dates": "2021 - 2024",
  "location": "San Francisco, CA",
  "bullets": [
    "Built scalable APIs",
    "Improved performance by 40%"
  ]
}
```

**Subsections Format (new option):**
```json
{
  "role": "Full Stack Developer",
  "company": "Tech Corp",
  "dates": "2021 - 2024",
  "location": "San Francisco, CA",
  "subsections": [
    {
      "header": "Platform Modernization",
      "bullets": [
        "Led migration to modern stack",
        "Improved load times by 26%"
      ]
    },
    {
      "header": "AI Integration",
      "bullets": [
        "Built AI prototype replacing $100K vendor"
      ]
    }
  ]
}
```

Subsection headers are rendered in uppercase with proper spacing to organize your achievements by theme or category.

## Example

```bash
# Generate resume using the example file
resume-gen render --in example_resume.json --out my_resume.docx
```

## MCP Server

This project includes a Model Context Protocol (MCP) server that enables AI agents to generate resumes programmatically.

### Setup

The MCP server is automatically installed when you follow the [Installation](#installation) steps above. The package includes all necessary dependencies.

**Verify MCP server installation:**
```bash
# Activate your virtual environment first
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Test the server imports correctly
python -c "from resume_mcp.server import mcp; print('✅ MCP server ready')"
```

**Run the MCP server directly (for testing):**
```bash
python -m resume_mcp.server
```

### Integration with AI Clients

After completing the [Installation](#installation) steps, configure your AI client to use the MCP server:

#### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "resume-generator": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "resume_mcp.server"],
      "cwd": "/absolute/path/to/resume-ats-docx-gen"
    }
  }
}
```

**⚠️ Important:** Replace both `/absolute/path/to/` placeholders with your actual project path.

#### VS Code GitHub Copilot

The `.vscode/mcp.json` file is already configured. Just **restart VS Code** to activate the MCP server.

To manually configure, create or edit `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "resume-generator": {
      "command": "${workspaceFolder}/.venv/bin/python",
      "args": ["-m", "resume_mcp.server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

**📚 For more details on MCP configuration in VS Code, see the [official documentation](https://code.visualstudio.com/docs/copilot/customization/mcp-servers#_configuration-format).**

**Test in VS Code:**
1. Restart VS Code
2. Open Copilot Chat (Cmd+I or Ctrl+I)
3. Try: `@workspace Create a resume for a Python developer and save as test.docx`

### MCP Tools

**`generate_resume`** - Generate DOCX from JSON

```python
# Example usage from AI agent:
generate_resume(
    resume={
        "header": {"name": "John Doe", "email": "john@example.com"},
        "skills": {"Languages": ["Python", "JavaScript"]},
        "experience": [...]
    },
    filename="john_doe_resume.docx"
)
```

The tool provides:
- ✅ Strict validation with detailed error messages
- ✅ Automatic file saving to temp directory
- ✅ Access to generated files via `outbox://` resources

### MCP Resources

**Templates** - View example resume structures:
- `template://simple` - Minimal resume example
- `template://full` - Complete traditional format
- `template://with-summary` - Resume with professional summary

**Outbox** - Access generated files:
- `outbox://filename.docx` - Retrieve generated DOCX file

### Error Handling

The MCP server provides detailed, actionable error messages for common issues:

```
❌ Resume validation failed. Fix the following issues:
  • header.email: field required
  • experience[0].bullets: Must provide either 'bullets' or 'subsections'

Review the required schema. Use template:// resources to see valid examples.
```

### File Location

Generated resumes are saved to: `{temp_dir}/resume-mcp-outbox/`

On macOS/Linux, this is typically: `/tmp/resume-mcp-outbox/`

## Requirements

- Python 3.8+
- python-docx >= 0.8.11
- click >= 8.0.0
- mcp >= 1.0.0 (for MCP server)
- pydantic >= 2.0.0 (for validation)
- fastapi >= 0.100.0 (for API server)
- uvicorn >= 0.23.0 (for API server)
- openai >= 1.0.0 (for agent workflows)

All dependencies are automatically installed with `pip install -e .`

## FastAPI Server

The FastAPI server provides REST API endpoints for frontend integration. It orchestrates:

1. **Agent Workflows**: Uses OpenAI agents to optimize resumes based on job descriptions or general improvement
2. **MCP Integration**: Converts optimized JSON to DOCX using the MCP server tools
3. **CORS Support**: Configured for local frontend development

### Starting the Server

```bash
# Using the CLI command
resume-api

# Or with auto-reload for development
uvicorn api.server:app --reload --port 8000
```

### API Documentation

Once the server is running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

For detailed API documentation, see [`api/README.md`](api/README.md)

### Integration with Frontend

Configure your frontend `.env.local`:

```bash
USE_MOCK=false
PY_WORKFLOW_JSON_URL=http://localhost:8000/api/workflow/json
PY_WORKFLOW_DOCX_URL=http://localhost:8000/api/workflow/docx
```

## License

MIT
