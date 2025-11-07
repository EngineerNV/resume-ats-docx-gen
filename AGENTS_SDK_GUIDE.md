# OpenAI Agents SDK Integration Guide

This guide explains how the OpenAI Agents SDK is integrated into the resume generation workflow.

## Architecture Overview

The system uses OpenAI's Agents SDK to create a multi-agent workflow that:
1. Analyzes resumes and job descriptions
2. Optimizes resume content for ATS systems
3. Generates professional DOCX files

### Key Components

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│  (api/server.py or api/server_v2.py)                    │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│              ResumeOrchestrator                          │
│  (app_agents/workflows/resume_orchestrator.py)          │
│  - Coordinates all agent workflows                       │
│  - Manages state and data flow                          │
└─────┬───────────────────────────┬───────────────────────┘
      │                           │
      ▼                           ▼
┌──────────────────┐    ┌────────────────────────┐
│ Job Research     │    │ Resume Optimization    │
│ Workflow         │    │ Workflow               │
│ (optional)       │    │ (always runs)          │
└──────┬───────────┘    └─────────┬──────────────┘
       │                          │
       └──────────┬───────────────┘
                  │
                  ▼
          ┌───────────────┐
          │ Result:       │
          │ - JSON        │
          │ - Filename    │
          │ - Metadata    │
          └───────┬───────┘
                  │
                  ▼
          ┌───────────────┐
          │ ResumeGenerator│
          │ (generator.py) │
          │ - Creates DOCX │
          └────────────────┘
```

## File Structure

```
resume-ats-docx-gen/
├── app_agents/
│   ├── workflows/
│   │   ├── resume_orchestrator.py       # Main orchestrator
│   │   ├── resume_json_creator.py       # OpenAI Agents SDK workflow
│   │   ├── job_research_agent.py        # Job analysis workflow
│   │   ├── workflow_compat.py           # Compatibility layer
│   │   └── __init__.py                  # Exports
│   ├── client.py                        # OpenAI client creation
│   ├── config.py                        # Configuration management
│   └── prompts.py                       # Agent instructions
├── api/
│   ├── server.py                        # Original FastAPI server
│   └── server_v2.py                     # New OpenAI Agents SDK server
├── resume_gen/
│   └── generator.py                     # DOCX generation
└── test_agent_workflow.py               # Integration tests
```

## Agent Workflows

### 1. Resume Flow Manager
**Purpose**: Determines workflow mode (job tuning vs. improvement)

**Input**: Resume text + optional job description
**Output**: Boolean (true = job tuning, false = improvement)

### 2. Tune Resume to JD Agent
**Purpose**: Analyzes job description and provides optimization guidance

**Input**: Resume + job description + ATS keywords
**Output**: Structured JSON with optimization instructions

**Features**:
- Web search for ATS insights
- Reasoning capabilities (o4-mini model)
- Structured guidance for downstream agents

### 3. Improve Current Resume Agent
**Purpose**: Provides general resume improvement suggestions

**Input**: Resume text only
**Output**: Structured JSON with improvement instructions

**Features**:
- Analyzes resume structure
- Identifies missing sections
- Suggests formatting improvements

### 4. Personal Statement Agent
**Purpose**: Generates professional summary

**Input**: Resume data + context
**Output**: Personalized professional summary

### 5. Resume JSON Builder Agent
**Purpose**: Normalizes data into standard JSON schema

**Input**: Structured/semi-structured resume data
**Output**: Validated resume JSON

**Features**:
- Field normalization
- Schema validation
- Deduplication

### 6. Judge for Improvement
**Purpose**: Final optimization and polishing

**Input**: Resume JSON
**Output**: Optimized resume JSON

**Features**:
- ATS optimization
- Language improvement
- Quality assurance

## Usage

### Option 1: Using the Orchestrator (Recommended)

```python
from app_agents.workflows import ResumeOrchestrator
from resume_gen.generator import ResumeGenerator
from pathlib import Path

# Create orchestrator
orchestrator = ResumeOrchestrator()

# Run workflow
result = await orchestrator.run_complete_workflow(
    resume_text="...",
    job_description="...",  # optional
    additional_context="...",  # optional
)

# Generate DOCX
generator = ResumeGenerator(result.optimized_resume_json)
generator.generate(Path("output") / result.filename)
```

### Option 2: Using FastAPI Endpoint

```bash
# Start server
python -m api.server_v2

# Or use uvicorn
uvicorn api.server_v2:app --reload
```

```bash
# Generate DOCX
curl -X POST http://localhost:8000/api/workflow/docx \
  -F "mode=resume" \
  -F "resumeText=..." \
  -F "context=..." \
  --output resume.docx

# Or with job tuning
curl -X POST http://localhost:8000/api/workflow/docx \
  -F "mode=job" \
  -F "resumeText=..." \
  -F "jobDescriptionText=..." \
  --output resume.docx
```

### Option 3: Compatibility Wrapper

```python
from app_agents.workflows import ResumeJsonWorkflow

# Uses the same interface as before
workflow = ResumeJsonWorkflow()
result = workflow.run(
    mode="job_tuning",
    resume_text="...",
    job_description="...",
)

# result.optimized_resume_json.parsed - ready for DOCX generation
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # optional
```

### Agent Configuration

Agents are configured in `resume_json_creator.py`:

```python
Agent(
    name="Agent Name",
    instructions="...",
    model="gpt-4o",  # or "o4-mini", "gpt-4.1", etc.
    tools=[web_search_preview],  # optional
    output_type=Schema,  # Pydantic model
    model_settings=ModelSettings(
        temperature=0.7,
        reasoning=Reasoning(effort="medium")  # for reasoning models
    )
)
```

## Testing

### Run Integration Tests

```bash
# Test the complete workflow
python test_agent_workflow.py
```

This will:
1. Test resume improvement mode
2. Test job tuning mode
3. Generate sample DOCX files
4. Verify file generation

### Run API Tests

```bash
# Start the server
python -m api.server_v2

# In another terminal, run tests
python -m pytest api/test_fastapi_smoke.py
```

## Workflow Modes

### Resume Improvement Mode
- Input: Resume text only
- Process: Analyzes and improves resume structure
- Output: Optimized resume JSON

### Job Tuning Mode
- Input: Resume text + job description
- Process: 
  1. Analyzes job description for ATS keywords
  2. Researches company leadership values
  3. Optimizes resume for specific role
- Output: Role-optimized resume JSON

## Data Flow

### Input Processing
```
User Input → FastAPI → Orchestrator
                         ↓
                    Text Combination
                         ↓
                    Mode Detection
```

### Agent Execution
```
Resume Flow Manager → Decision (job tuning vs. improvement)
         ↓
    ┌────┴────┐
    ↓         ↓
Job Tuning   Resume
Path         Improvement
    ↓         ↓
    └────┬────┘
         ↓
Personal Statement Agent
         ↓
Resume JSON Builder
         ↓
Judge for Improvement
         ↓
    Final JSON
```

### Output Generation
```
Final JSON → Filename Generation
              ↓
         ResumeGenerator
              ↓
          DOCX File
```

## Error Handling

The system includes comprehensive error handling:

1. **Input Validation**: Required fields, format checking
2. **Agent Errors**: Retry logic, fallbacks
3. **Schema Validation**: Pydantic models ensure correct structure
4. **File Generation**: Error messages with traceback

## Best Practices

### 1. Use the Orchestrator
The `ResumeOrchestrator` handles all complexity:
- State management
- Workflow coordination
- Error handling

### 2. Validate Inputs
Always validate user inputs before passing to the workflow:
```python
if not resume_text or not resume_text.strip():
    raise ValueError("Resume text is required")
```

### 3. Handle Async Properly
The workflows are async. Use proper async/await:
```python
async def my_function():
    result = await orchestrator.run_complete_workflow(...)
```

### 4. Monitor API Usage
The workflow makes multiple OpenAI API calls:
- Resume Flow Manager: 1 call
- Tune/Improve Agent: 1-2 calls (may use web search)
- Personal Statement: 1 call
- JSON Builder: 1 call
- Judge: 1 call

Total: 5-7 API calls per workflow run

## Troubleshooting

### Common Issues

**Issue**: Import errors for `agents` module
**Solution**: Ensure `openai-agents` package is installed:
```bash
pip install openai-agents
```

**Issue**: Async event loop errors
**Solution**: Use the synchronous wrapper:
```python
from app_agents.workflows import run_resume_orchestrator
result = run_resume_orchestrator(...)
```

**Issue**: Schema validation errors
**Solution**: Check that all required fields are present in the JSON

**Issue**: DOCX generation fails
**Solution**: Verify the resume JSON matches the expected schema

## Performance Optimization

### 1. Caching
Consider caching job research results:
```python
# Cache ATS keywords for similar job descriptions
cache_key = hash(job_description[:100])
```

### 2. Parallel Execution
Some agents can run in parallel:
```python
# Run job research and resume analysis in parallel
results = await asyncio.gather(
    run_job_research(...),
    run_resume_analysis(...)
)
```

### 3. Model Selection
Choose appropriate models:
- `gpt-4o`: Fast, good quality
- `o4-mini`: Better reasoning, slower
- `gpt-4.1`: High quality, expensive

## Next Steps

1. **Add Monitoring**: Track agent performance and costs
2. **Improve Caching**: Cache common patterns
3. **Add Validation**: More robust input validation
4. **Extend Agents**: Add specialized agents for specific industries
5. **UI Enhancement**: Better visualization of agent workflow

## Support

For issues or questions:
1. Check the workflow logs
2. Review agent instructions
3. Verify API key and configuration
4. Test with sample data from `test_agent_workflow.py`
