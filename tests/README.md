# Test Suite

Comprehensive test suite for the Resume ATS DOCX Generator.

## Test Organization

All tests follow the `test_*.py` naming convention for compatibility with pytest and other test runners.

## Test Files

### Integration Tests

#### `test_fastapi_agents_docx.py` ⭐ (Recommended)
**Complete end-to-end integration test**
- Starts FastAPI server
- Tests all API endpoints (health, JSON workflow, DOCX workflow)
- Tests both resume improvement and job tuning modes
- Verifies DOCX file generation
- Validates file content

**Run:**
```bash
python tests/test_fastapi_agents_docx.py
```

**Coverage:**
- ✅ FastAPI server startup
- ✅ Health check endpoint
- ✅ JSON workflow (resume mode)
- ✅ JSON workflow (job mode)
- ✅ DOCX generation (resume mode)
- ✅ DOCX generation (job mode)
- ✅ File validation

---

### Workflow Tests

#### `test_agent_workflow.py`
Tests the OpenAI Agents SDK workflow components.
- Resume context extraction
- Resume JSON creation
- Job research agent
- File naming agent

#### `test_resume_workflow.py`
Tests the complete resume workflow orchestration.
- ResumeOrchestrator
- Workflow coordination
- Result validation

#### `test_simple.py`
Simple workflow test with minimal setup.
- Basic resume optimization
- Quick validation

---

### API Tests

#### `test_api_integration.py`
Tests FastAPI integration with agents.
- API endpoint functionality
- Request/response validation

#### `test_api_smoke.py`
Quick smoke test for API health.
- Server availability
- Basic endpoint checks

---

### Agent Tests

#### `test_agents_only.py`
Isolated tests for individual agents.
- Agent initialization
- Agent execution
- Output validation

#### `test_job_mode.py`
Specific tests for job tuning mode.
- Job description processing
- ATS keyword extraction
- Resume alignment

---

### MCP Tests

#### `test_mcp.py`
Tests MCP server functionality.
- MCP protocol compliance
- Tool registration
- Resource handling

#### `test_mcp_resume_agent.py`
Tests MCP integration with resume agents.
- Agent-MCP communication
- DOCX generation via MCP

---

### Direct Generation Tests

#### `test_direct_generation.py`
Tests direct DOCX generation without MCP protocol.
- Direct function calls
- Performance comparison
- Output validation

---

## Running Tests

### Run All Tests (Recommended)
```bash
# Using pytest
pytest tests/

# Or run specific test
pytest tests/test_fastapi_agents_docx.py -v
```

### Run Individual Tests
```bash
# FastAPI integration (most comprehensive)
python tests/test_fastapi_agents_docx.py

# Simple workflow test
python tests/test_simple.py

# Job mode test
python tests/test_job_mode.py

# Agent workflow test
python tests/test_agent_workflow.py
```

### Quick Test Script
```bash
# From project root
./run_fastapi_test.sh
```

---

## Test Requirements

### Environment Setup
1. **Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   pip install -e .
   ```

2. **Environment Variables:**
   Create `.env` file in project root:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Dependencies:**
   - `openai-agents`
   - `fastapi`
   - `uvicorn`
   - `httpx`
   - `python-docx`
   - `pytest` (optional, for test discovery)

---

## Test Fixtures

### `fixtures/jordan_resume.txt`
Sample resume data for testing.

---

## Expected Outputs

Tests generate DOCX files in the `outbox/` directory:
- `test_resume_mode.docx` - Resume improvement mode output
- `test_job_mode.docx` - Job tuning mode output
- `test_integration.docx` - Integration test output
- Various other test outputs

---

## CI/CD Integration

### GitHub Actions (Example)
```yaml
- name: Run Tests
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    pytest tests/ -v
```

### Local Pre-commit Hook
```bash
#!/bin/bash
# Run quick tests before commit
python tests/test_simple.py
```

---

## Test Coverage

To run with coverage:
```bash
pytest tests/ --cov=app_agents --cov=api --cov=resume_gen --cov-report=html
```

---

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"
**Solution:** Create `.env` file with your API key

### Issue: "Server failed to start"
**Solution:** Check if port 8000 is available, or kill existing processes:
```bash
lsof -ti:8000 | xargs kill -9
```

### Issue: "ModuleNotFoundError"
**Solution:** Install package in development mode:
```bash
pip install -e .
```

### Issue: Tests timeout
**Solution:** Increase timeout values or check OpenAI API status

---

## Best Practices

1. **Always run from project root:**
   ```bash
   python tests/test_name.py
   ```

2. **Use virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

3. **Check .env file exists:**
   ```bash
   ls -la .env
   ```

4. **Clean up old outputs:**
   ```bash
   rm -f outbox/test_*.docx
   ```

5. **Run comprehensive test before PR:**
   ```bash
   python tests/test_fastapi_agents_docx.py
   ```

---

## Test Naming Convention

All test files follow the pattern: `test_<description>.py`

This ensures:
- ✅ pytest auto-discovery
- ✅ Clear test organization
- ✅ Standard Python testing conventions
- ✅ Easy IDE integration

---

## Contributing

When adding new tests:
1. Name files as `test_<feature>.py`
2. Place in `tests/` directory
3. Add description to this README
4. Include docstrings in test functions
5. Follow existing test patterns
6. Ensure tests clean up after themselves

---

## See Also

- [TEST_RESULTS.md](../TEST_RESULTS.md) - Latest test run results
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [README.md](../README.md) - Project documentation
