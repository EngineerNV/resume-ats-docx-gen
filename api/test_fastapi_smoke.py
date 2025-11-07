from fastapi.testclient import TestClient
from api.server import app

# Monkeypatch OpenAI client to use recorded mock outputs
import app_agents.client as agent_client
import app_agents.workflows.resume_json_creator as rjc
import app_agents.workflows.file_naming_agent as mra
from app_agents.testing.fake_openai import FakeOpenAI
from app_agents.testing.mock_runs import mock_run

agent_client.create_openai_client = lambda *args, **kwargs: FakeOpenAI.from_specs(mock_run("jordan_resume_improvement"))
# Also patch the imported symbol used inside resume_json_creator
rjc.create_openai_client = agent_client.create_openai_client
from app_agents.testing.fake_openai import MockResponseSpec
mra.create_openai_client = lambda *args, **kwargs: FakeOpenAI.from_specs([
    MockResponseSpec(kind="parse", parsed={
        "filename": "jordan_m_reynolds_resume.docx",
        "resume_data": {
            "header": {"name": "Jordan M. Reynolds", "email": "jordan.reynolds@example.com"},
            "skills": {"Programming Languages": ["Python", "Go"]}
        },
        "mcp_server_ready": True,
        "reasoning": "Generated filename from header.name; included minimal resume data for generation."
    })
])

client = TestClient(app)

# Health check
r = client.get("/")
print("GET /:", r.status_code, r.json())

# JSON workflow (resume improvement)
form_data = {
    "mode": "resume",
    "resumeText": "Jane Doe\nEmail: jane@example.com\nExperience: ...",
}
rj = client.post("/api/workflow/json", data=form_data)
print("POST /api/workflow/json:", rj.status_code)
print(rj.json())

# DOCX workflow (resume improvement)
rd = client.post("/api/workflow/docx", data=form_data)
print("POST /api/workflow/docx:", rd.status_code)
print("Content-Type:", rd.headers.get("content-type"))
if rd.headers.get("content-type", "").startswith("application/json"):
    print(rd.json())
else:
    print("Content-Disposition:", rd.headers.get("content-disposition"))
    print("Body size:", len(rd.content))
