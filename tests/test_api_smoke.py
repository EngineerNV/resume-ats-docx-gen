"""
Smoke test for API server endpoints.
Tests that endpoints are wired correctly without calling OpenAI.
"""

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_health_check():
    """Test the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "2.0.0" in data["version"]
    print("✓ Health check passed")


def test_json_endpoint_validation():
    """Test JSON endpoint validates required fields."""
    # Missing resume text
    response = client.post("/api/workflow/json", data={
        "mode": "resume",
        "resumeText": "",
    })
    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False
    assert "resumeText" in str(data)
    print("✓ JSON endpoint validation works")


def test_json_endpoint_job_mode_validation():
    """Test JSON endpoint requires job description in job mode."""
    response = client.post("/api/workflow/json", data={
        "mode": "job",
        "resumeText": "Some resume text",
        "jobDescriptionText": "",
    })
    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False
    assert "jobDescription" in str(data)
    print("✓ JSON endpoint job mode validation works")


def test_docx_endpoint_exists():
    """Test DOCX endpoint exists and validates."""
    response = client.post("/api/workflow/docx", data={
        "mode": "resume",
        "resumeText": "",
    })
    # Should fail validation, not 404
    assert response.status_code != 404
    print("✓ DOCX endpoint exists")


if __name__ == "__main__":
    test_health_check()
    test_json_endpoint_validation()
    test_json_endpoint_job_mode_validation()
    test_docx_endpoint_exists()
    print("\n✅ All API smoke tests passed!")
