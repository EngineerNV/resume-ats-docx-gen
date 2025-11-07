# Agent Guide for resume-ats-docx-gen

This document provides comprehensive guidance for AI agents working with the resume-ats-docx-gen project. It covers project structure, key concepts, common tasks, and best practices.

## Project Overview

**Purpose**: Generate ATS-friendly resumes in DOCX format from JSON input  
**Language**: Python 3.8+  
**Key Dependencies**: python-docx, click  
**Command**: `resume-gen render --in <json> --out <docx>`

## Project Structure

```
resume-ats-docx-gen/
├── resume_gen/
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Click-based CLI interface
│   └── generator.py         # Core resume generation logic
├── example_resume.json      # Traditional format example
├── nick_vaughn_resume.json  # Subsections format example
├── simple_resume.json       # Minimal example
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # User-facing documentation
├── AGENT.md                # This file - agent guidance
└── .venv/                  # Virtual environment (created on setup)
```

## Core Components

### 1. CLI Interface (`cli.py`)

**Purpose**: Command-line interface using Click framework  
**Main Function**: `render()`  
**Responsibilities**:
- Parse command-line arguments (`--in`, `--out`)
- Validate file paths
- Call generator with JSON data
- Handle errors and provide user feedback

**Key Code Pattern**:
```python
@click.command()
@click.option('--in', 'input_file', required=True)
@click.option('--out', 'output_file', required=True)
def render(input_file, output_file):
    # Validation and generation logic
```

### 2. Generator (`generator.py`)

**Purpose**: Core document generation logic  
**Main Class**: `ResumeGenerator`  
**Key Methods**:

- `__init__(json_data)`: Initialize with resume data
- `_setup_document()`: Configure margins and document settings
- `_add_paragraph()`: Low-level paragraph creation with formatting
- `_add_hyperlink()`: Create clickable links in document
- `_add_header_section()`: Generate name and contact info with hyperlinks
- `_add_section_header()`: Create uppercase, bold, underlined section headers
- `_add_bullet_paragraph()`: Create properly formatted bullet points
- `_add_skills_section()`: Render skills by category
- `_add_experience_section()`: Render work history (supports subsections)
- `_add_education_section()`: Render education entries
- `_add_awards_section()`: Render awards and achievements
- `generate(output_path)`: Main orchestration method

**Key Constants**:
```python
FONT_NAME = "Calibri"
BODY_FONT_SIZE = 11
NAME_FONT_SIZE = 16
SECTION_HEADER_FONT_SIZE = 12
MARGIN_SIZE = 36  # 0.5 inch
```

## JSON Schema

### Required Structure

```json
{
  "header": {
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "(555) 123-4567",
    "location": "City, State",
    "linkedin": "linkedin.com/in/username",
    "github": "github.com/username"
  },
  "skills": {
    "Category Name": ["Skill 1", "Skill 2"]
  },
  "experience": [...],
  "education": [...],
  "awards": [...]
}
```

### Experience Entry Formats

**Format 1: Traditional Bullets (backward compatible)**
```json
{
  "role": "Job Title",
  "company": "Company Name",
  "dates": "Month Year - Month Year",
  "location": "City, State",
  "bullets": [
    "Achievement with action verb",
    "Another achievement"
  ]
}
```

**Format 2: Subsections (new feature)**
```json
{
  "role": "Job Title",
  "company": "Company Name",
  "dates": "Month Year - Month Year",
  "location": "City, State",
  "subsections": [
    {
      "header": "Focus Area Name",
      "bullets": [
        "Achievement in this area",
        "Another achievement"
      ]
    }
  ]
}
```

**Backward Compatibility**: If `subsections` is present, it takes precedence over `bullets`. If `subsections` is absent, falls back to `bullets`.

### Education Entry

```json
{
  "degree": "Degree Name",
  "institution": "University Name",
  "dates": "Year - Year",
  "location": "City, State",
  "gpa": "3.X/4.0"  # Optional
}
```

### Awards Entry (Flexible)

String format:
```json
"Award Name (Year)"
```

Object format:
```json
{
  "title": "Award Name",
  "date": "Year",
  "description": "Brief description"
}
```

## FastAPI Integration

### Overview

The FastAPI server (`api/server.py`) is the **primary workflow orchestrator** that integrates OpenAI agent workflows with resume generation. It provides REST API endpoints for the frontend application.

### API Workflow

The resume generation flows through the FastAPI server in this sequence:

1. **JSON Endpoint** (`POST /api/workflow/json`)
   - Accepts resume text and optional job description
   - Runs agent workflow for optimization
   - Returns optimized resume JSON (no file generation)

2. **DOCX Endpoint** (`POST /api/workflow/docx`)
   - Full workflow: optimization → filename generation → DOCX creation
   - Returns downloadable DOCX file

### Filename Agent

Located in `app_agents/workflows/file_naming_agent.py`, the Filename Agent is responsible for intelligent document naming:

**Purpose**: Extract candidate name and generate professional, URL-safe filenames

**Functionality**:
- Reviews optimized resume JSON
- Intelligently extracts candidate name from `header.name`
- Handles edge cases (missing names, special characters, etc.)
- Generates URL-safe filenames (e.g., `jane_smith_resume.docx`)
- Provides fallback logic for malformed data

**Example Usage**:
```python
from app_agents.workflows.file_naming_agent import prepare_resume_for_mcp

# After agent workflow generates optimized JSON
result = prepare_resume_for_mcp(optimized_resume_json)

print(result.filename)      # "jane_smith_resume.docx"
print(result.resume_data)   # Full resume JSON
print(result.reasoning)     # Agent's explanation
```

**Output Structure**:
```python
class FilenameResult:
    filename: str          # e.g., "jane_smith_resume.docx"
    resume_data: dict      # Complete resume JSON
    reasoning: str         # Why this filename was chosen
```

### Direct Generation vs MCP Protocol

**Important**: The FastAPI workflow uses **direct function calls**, not the MCP protocol.

**Direct Generation Approach** (Current):
```python
from resume_mcp.tools import generate_resume_tool

# Direct function call
result = generate_resume_tool(
    resume_data=filename_result.resume_data,
    filename=filename_result.filename
)
```

**Benefits**:
- **Faster**: ~100ms performance improvement
- **Simpler**: Fewer moving parts, easier debugging
- **Reliable**: No inter-process communication overhead
- **Maintainable**: Single codebase, direct imports

**MCP Protocol** (Separate, Optional):
The standalone MCP server (`resume_mcp/server.py`) exists separately for AI client integration (Claude Desktop, VS Code Copilot). It uses the Model Context Protocol for external AI assistants but is **not used** by the FastAPI workflow.

### API Endpoints

**Health Check**:
```bash
GET /
```

**Generate JSON** (optimization only):
```bash
POST /api/workflow/json
Form Data:
  - mode: "resume" | "job"
  - resumeText: string
  - jobDescriptionText: string (optional)
  - atsKeywords: string (optional)
  - context: string (optional)
```

**Generate DOCX** (full workflow):
```bash
POST /api/workflow/docx
Form Data: (same as /api/workflow/json)
Response: application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

### Running the FastAPI Server

```bash
# Using CLI command
resume-api

# Using uvicorn directly
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload

# Test health check
curl http://localhost:8000/

# Test DOCX generation
curl -X POST http://localhost:8000/api/workflow/docx \
  -F 'mode=resume' \
  -F 'resumeText=...' \
  -o resume.docx
```

### Integration Flow

```
┌──────────┐     ┌──────────────┐     ┌────────────────┐
│ Frontend │────▶│ FastAPI      │────▶│ Agent Workflow │
│ (Next.js)│     │ Server       │     │ (OpenAI)       │
└──────────┘     └──────────────┘     └────────────────┘
                        │                      │
                        │                      ▼
                        │              ┌────────────────┐
                        │              │ Optimized JSON │
                        │              └────────────────┘
                        │                      │
                        │                      ▼
                        │              ┌────────────────┐
                        │              │ Filename Agent │
                        │              └────────────────┘
                        │                      │
                        │                      ▼
                        │              ┌────────────────┐
                        └─────────────▶│ Direct Gen     │
                                       │ (DOCX)         │
                                       └────────────────┘
```

## Common Tasks

### 1. Testing Changes

```bash
# Activate virtual environment
source .venv/bin/activate

# Test with traditional format
resume-gen render --in example_resume.json --out test_traditional.docx

# Test with subsections format
resume-gen render --in nick_vaughn_resume.json --out test_subsections.docx

# Test backward compatibility
resume-gen render --in simple_resume.json --out test_simple.docx
```

### 2. Adding a New Section Type

1. Add section data to JSON schema
2. Create `_add_<section>_section()` method in `ResumeGenerator`
3. Call method in `generate()` method
4. Update `README.md` with documentation
5. Add example to `example_resume.json`
6. Test generation

### 3. Modifying Spacing

**Location**: Various `space_after` parameters in `generator.py`

**Key Spacing Values** (in points):
- Header name spacing: `space_after=2`
- Contact info spacing: `space_after=8`
- Section header spacing: `space_after=4`
- Bullet spacing: `space_after=1`
- Inter-job spacing: `space_after=4`
- Skill category spacing: `space_after=2`
- Education detail spacing: `space_after=4`

**Pattern**: Smaller values = tighter spacing. ATS prefers compact layouts.

### 4. Adding Hyperlink Support to New Fields

**Pattern** (see `_add_header_section()` for reference):
```python
# Create paragraph
para = self.doc.add_paragraph()

# Add text before link
run = para.add_run("Text before: ")

# Add hyperlink
self._add_hyperlink(para, "Display Text", "https://url.com")

# Add text after link
run = para.add_run(" text after")
```

**URL Normalization**:
```python
url = text if text.startswith("http") else f"https://{text}"
```

### 5. Debugging Document Generation

**Common Issues**:
1. **Missing XML namespace**: Ensure proper namespace in `_add_hyperlink()`
2. **Spacing issues**: Check `space_after` and `space_before` values
3. **Font not applying**: Verify `run.font.name` is set after creating run
4. **Tab alignment**: Ensure tab stops are added to paragraph format

**Debugging Pattern**:
```python
# Add print statements in generator methods
print(f"Processing job: {job.get('company')}")

# Generate and inspect
generator.generate(output_path)

# Open in Word to verify formatting
```

## Python Best Practices in This Codebase

### 1. Type Hints
```python
def _add_paragraph(self, text: str, bold: bool = False, 
                  font_size: int = None) -> None:
```

### 2. Docstrings
```python
def method_name(self, param: str):
    """Brief description of method.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value (if applicable)
    """
```

### 3. Constants
- Use ALL_CAPS for class-level constants
- Group related constants together
- Document meaning with comments if not obvious

### 4. Error Handling
```python
try:
    # Operation
except SpecificException as e:
    # Specific handling
    raise click.ClickException(f"User-friendly message: {e}")
```

### 5. Code Organization
- Private methods start with `_`
- Public API methods have no underscore
- Group methods by section type
- Keep methods focused and single-purpose

## Development Workflow

### 1. Setup Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install in development mode
pip install -e .
```

### 2. Make Changes
1. Edit code in `resume_gen/` directory
2. Update docstrings and type hints
3. Maintain backward compatibility
4. Follow existing code style

### 3. Test Changes
```bash
# Run with test data
resume-gen render --in example_resume.json --out test.docx

# Open and verify in Word
open test.docx  # macOS
```

### 4. Update Documentation
1. Update `README.md` for user-facing changes
2. Update this `AGENT.md` for structural changes
3. Add examples to JSON files if needed

### 5. Clean Up
```bash
# Remove test files
rm test*.docx

# Deactivate virtual environment
deactivate
```

## Key Design Decisions

### 1. Why python-docx?
- No external dependencies (Word not required)
- Pure Python implementation
- Programmatic control over formatting
- ATS-compatible output

### 2. Why Click for CLI?
- Clean, declarative API
- Automatic help generation
- Good error handling
- Industry standard

### 3. Why Separate bullets/subsections?
- **Backward compatibility**: Existing JSON files still work
- **Flexibility**: Users can choose based on job complexity
- **Opt-in complexity**: Simple jobs use simple format
- **ATS safe**: Subsections are just formatted text

### 4. Why Clickable Links?
- **User experience**: Easy to verify contact info
- **Modern standard**: Expected in digital resumes
- **ATS compatible**: Modern ATS handle hyperlinks correctly

### 5. Spacing Philosophy
- **Compact > Spacious**: Maximizes content per page
- **Consistency**: Same spacing rules throughout
- **ATS priority**: Format optimized for parsing, not beauty

## Troubleshooting

### Issue: "command not found: resume-gen"
**Solution**: Activate virtual environment or use full path
```bash
source .venv/bin/activate
# or
/path/to/.venv/bin/resume-gen render --in file.json --out output.docx
```

### Issue: Links not clickable
**Check**:
1. URL has proper scheme (https://)
2. `_add_hyperlink()` is being called
3. XML namespace is correct in hyperlink element

### Issue: Spacing looks wrong
**Check**:
1. `space_after` values in relevant `_add_*` methods
2. Paragraph format settings
3. Line spacing vs paragraph spacing

### Issue: Font not applying
**Check**:
1. Font name set on `run.font.name`, not paragraph
2. Font set after creating run
3. Font name is exact ("Calibri", not "calibri")

### Issue: Bullets not indenting
**Check**:
1. Using `style='List Bullet'` in `add_paragraph()`
2. Bullet list style exists in document
3. Indentation settings in paragraph format

## Testing Checklist

When making changes, verify:

- [ ] Traditional bullets format still works (`example_resume.json`)
- [ ] Subsections format works (`nick_vaughn_resume.json`)
- [ ] Simple/minimal format works (`simple_resume.json`)
- [ ] Hyperlinks are clickable (email, LinkedIn, GitHub)
- [ ] Spacing is consistent and professional
- [ ] All sections render correctly
- [ ] Font and sizing are correct throughout
- [ ] Document opens without errors in Microsoft Word
- [ ] No Python errors or warnings during generation
- [ ] CLI help text is accurate (`resume-gen --help`)

## Future Enhancement Ideas

If asked to extend the project, consider:

1. **PDF Export**: Add `--format pdf` option
2. **Multiple Themes**: Support different visual styles
3. **Template System**: Allow custom section ordering
4. **Validation**: JSON schema validation on input
5. **Web Interface**: Flask/FastAPI web app
6. **Batch Processing**: Process multiple JSON files
7. **LinkedIn Import**: Fetch data from LinkedIn API
8. **Version Control**: Track resume versions
9. **A/B Testing**: Compare different formats
10. **Analytics**: Track which format performs best

## Contact & Resources

- **Repository**: EngineerNV/resume-ats-docx-gen
- **Python-docx docs**: https://python-docx.readthedocs.io/
- **Click docs**: https://click.palletsprojects.com/
- **ATS Guidelines**: Research current ATS best practices before making format changes

---

**Last Updated**: November 2, 2025  
**Agent Version Compatibility**: This guide is written for AI agents as of November 2025

## Quick Reference Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate && pip install -e .

# Generate resume
resume-gen render --in example_resume.json --out resume.docx

# Test all examples
resume-gen render --in example_resume.json --out test1.docx
resume-gen render --in nick_vaughn_resume.json --out test2.docx
resume-gen render --in simple_resume.json --out test3.docx

# Cleanup
rm test*.docx && deactivate
```
