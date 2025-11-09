"""pytest configuration for this repo.

Loads environment variables from the project `.env` file early so tests
that depend on env settings (for agent clients, API keys, etc.) run the
same way whether executed under pytest or via other runners.

This import runs at pytest collection time.
"""
try:
    # Prefer find_dotenv/load_dotenv helpers for robust project-root discovery
    from dotenv import load_dotenv, find_dotenv
    # locate .env (search upwards) and load it if found; don't error if missing
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)
    else:
        # fallback: try to load a .env in the repo root
        try:
            load_dotenv('.env')
        except Exception:
            pass
except Exception:
    # If python-dotenv isn't installed, don't fail the test run; env vars
    # will simply not be loaded from a file.
    pass
"""
Pytest configuration for resume-ats-docx-gen tests.
"""

import os
import sys
from pathlib import Path

import pytest


# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Return the project root directory path."""
    return project_root


@pytest.fixture(scope="session")
def outbox_dir(project_root_path):
    """Return the outbox directory for test outputs."""
    outbox = project_root_path / "outbox"
    outbox.mkdir(exist_ok=True)
    return outbox


@pytest.fixture(scope="session")
def load_env(project_root_path):
    """Load environment variables from .env file."""
    env_path = project_root_path / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    # Verify API key is present
    if not os.environ.get('OPENAI_API_KEY'):
        pytest.skip("OPENAI_API_KEY not found in environment")


@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing."""
    return """
John Smith
john.smith@email.com | San Francisco, CA | linkedin.com/in/johnsmith

Experienced software engineer with 5+ years in full-stack development.

SKILLS: Python, JavaScript, React, Node.js, AWS, Docker

EXPERIENCE
Senior Software Engineer - Tech Corp (Jan 2021 - Present)
- Led microservices development serving 1M+ users
- Reduced API latency by 40%

EDUCATION
B.S. Computer Science - UC Berkeley (2015-2019)
"""


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
Staff Software Engineer - Cloud Infrastructure

Requirements:
- 5+ years of software engineering experience
- Strong expertise in Python and modern web frameworks
- Deep understanding of cloud platforms (AWS, GCP, or Azure)
- Experience with Kubernetes, Docker, and container orchestration

Responsibilities:
- Design and implement highly scalable cloud infrastructure
- Lead technical initiatives and mentor engineering teams
- Build and maintain CI/CD pipelines and automation tools
"""


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (may be slow)"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test (requires server)"
    )
    config.addinivalue_line(
        "markers", "agents: mark test as agent workflow test (requires OpenAI API)"
    )
    config.addinivalue_line(
        "markers", "mcp: mark test as MCP server test"
    )
