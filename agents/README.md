# Agent Workspace

This directory now contains the Python implementation of the agent workflows that support resume planning and generation. The workflows mirror the OpenAI Agent Builder exports provided by the product team and feed JSON output directly into the MCP resume generator.

## Components

- `config.py` – Pydantic settings wrapper used to read `OPENAI_API_KEY` (and optional `OPENAI_BASE_URL`) from environment variables.
- `client.py` – Helper that constructs an `OpenAI` client configured with the project settings.
- `workflows/` – Collection of reusable workflow entry points:
  - `resume_context_extractor.py` – Wraps the **Resume/Context Extractor** agent workflow.
  - `resume_json_creator.py` – Orchestrates the **Resume Flow Manager**, **Tune Resume to JD**, **Improve Current Resume**, **Personal Statement**, **Resume JSON Builder**, and **Judge for Improvement** agents. This module wires the outputs so they can be consumed by the MCP server.

## Usage

1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (and `OPENAI_BASE_URL` if you are targeting a non-default endpoint).
2. Instantiate the workflow in Python:

   ```python
   from agents.workflows import ResumeJsonWorkflow

   workflow = ResumeJsonWorkflow()
   result = workflow.run(
       resume_text="""...raw resume text...""",
       job_description="""...job description...""",
       ats_keywords=["python", "aws"],
       mode="job_tuning",  # or "resume_improvement" / "auto"
       additional_context={"linkedin_summary": "..."},
   )

   print(result.optimized_resume_json.parsed)
   ```

3. The returned `ResumeJsonWorkflowResult` bundles the outputs of every agent call. Feed `result.optimized_resume_json.parsed` directly into the MCP server’s `generate_resume` tool to produce DOCX files.

4. For quick manual testing (including the smoke scenarios requested by product), run the helper script which wraps the workflow with sample data:

   ```bash
   python -m agents.scripts.run_resume_workflow --mode job_tuning
   python -m agents.scripts.run_resume_workflow --mode resume_improvement
   ```

   Use `--resume-file`, `--job-description-file`, or `--ats-keywords` to supply custom inputs, and `--output <path>` to persist the aggregated response JSON for inspection.

   When the OpenAI SDK is unavailable or network access is restricted, you can replay recorded agent outputs with `--mock-run`. For example, the `jordan_resume_improvement` recording validates the resume-improvement branch using the fictional Jordan Reynolds resume that product provided:

   ```bash
   python -m agents.scripts.run_resume_workflow \
     --mode resume_improvement \
     --resume-file tests/fixtures/jordan_resume.txt \
     --mock-run jordan_resume_improvement \
     --output jordan_resume_improvement_output.json
   ```

## Notes

- The workflows assume the OpenAI Python SDK ≥ `1.0`. Make sure to install project dependencies (`pip install -e .`) before running.
- `ResumeJsonWorkflow.run` automatically executes the resume/context extraction workflow before orchestrating the remaining agents, ensuring each downstream call receives the structured context it needs.
- Set `mode="job_tuning"` to explicitly force job-alignment behavior (skip the flow manager decision) or `mode="resume_improvement"` to focus on general polishing. Leave the default `mode="auto"` to reuse the flow manager’s decision logic.
