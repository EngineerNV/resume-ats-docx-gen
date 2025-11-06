import json
import sys
import types
import unittest


if "openai" not in sys.modules:
    fake_openai = types.ModuleType("openai")

    class _StubOpenAI:  # pragma: no cover - construction guard
        def __init__(self, *args, **kwargs):  # noqa: D401 - simple guard
            raise RuntimeError(
                "Tests should inject a fake OpenAI client instead of creating one"
            )

    fake_openai.OpenAI = _StubOpenAI  # type: ignore[attr-defined]
    sys.modules["openai"] = fake_openai


if "pydantic" not in sys.modules:
    fake_pydantic = types.ModuleType("pydantic")

    class _FakeBaseSettings:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    def _fake_field(default=None, **_kwargs):
        return default

    fake_pydantic.BaseSettings = _FakeBaseSettings  # type: ignore[attr-defined]
    fake_pydantic.Field = _fake_field  # type: ignore[attr-defined]
    sys.modules["pydantic"] = fake_pydantic


from agents.workflows.resume_json_creator import ResumeJsonWorkflow


FAKE_RESUME_TEXT = """John Doe\nEmail: john.doe@example.com\nLinkedIn: linkedin.com/in/johndoe\nExperience: Built data pipelines in Python and GCP."""

FAKE_JOB_DESCRIPTION = """Software Engineer, Google Cloud Platform\nResponsibilities include building reliable distributed systems, collaborating with cross-functional teams, and scaling products to millions of users."""

FAKE_ATS_KEYWORDS = ["Python", "GCP", "distributed systems"]


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.output_text = text


class FakeResponsesAPI:
    def __init__(self) -> None:
        self.calls = []

    def create(self, **request):
        system_text = request["input"][0]["content"][0]["text"]
        self.calls.append(system_text)

        if system_text.startswith("You are an intelligent Resume Extraction Agent"):
            payload = {
                "header": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "location": "Mountain View, CA",
                    "linkedin": "https://linkedin.com/in/johndoe",
                    "github": "https://github.com/johndoe",
                },
                "skills": {"Programming Languages": ["Python"], "Technologies": ["GCP"], "Tools": ["Git"]},
                "experience": [
                    {
                        "role": "Software Engineer",
                        "company": "Tech Labs",
                        "dates": "2021-Present",
                        "location": "Mountain View, CA",
                        "bullets": ["Implemented ETL pipelines handling 2TB daily."],
                    }
                ],
                "education": [
                    {
                        "degree": "B.S. Computer Science",
                        "institution": "Stanford University",
                        "dates": "2017-2021",
                        "location": "Stanford, CA",
                        "gpa": "3.8/4.0",
                    }
                ],
                "awards": ["Employee of the Quarter (2023)"]
            }
            return FakeResponse(json.dumps(payload))

        if system_text.startswith("You are an automated decision-making agent optimized"):
            return FakeResponse(json.dumps({"output": True}))

        if system_text.startswith("You are the Resume Planning & Alignment Orchestrator Agent"):
            payload = {
                "target_role_priorities": {
                    "key_competencies": ["Scalable backend systems"],
                    "technical_focus": ["Python", "GCP"],
                    "soft_skills_or_domain_focus": ["Cross-functional collaboration"],
                    "critical_ats_keywords": ["distributed systems", "Kubernetes"],
                },
                "coverage_comparison": {
                    "covered_strong": ["Python", "GCP"],
                    "covered_but_needs_emphasis": ["distributed systems"],
                    "missing_or_unclear_pending_verification": ["Kubernetes"],
                },
                "section_guidance": {
                    "header": {
                        "status": "present",
                        "reasoning": "Contact details captured in resume context.",
                        "instructions_for_editor_agent": ["Ensure LinkedIn and GitHub remain prominent."],
                    },
                    "skills": {
                        "status": "present",
                        "reasoning": "Skills captured but need alignment to JD buckets.",
                        "instructions_for_editor_agent": ["Add distributed systems tooling."],
                        "skill_bucket_adjustments": {
                            "Programming Languages": {"add": ["Go"], "de_emphasize": []},
                            "Technologies": {"add": ["Kubernetes"], "de_emphasize": []},
                            "Tools": {"add": ["Terraform"], "de_emphasize": []},
                        },
                    },
                    "experience": {
                        "status": "present",
                        "reasoning": "Current role includes relevant GCP work.",
                        "instructions_for_editor_agent": ["Highlight scale and reliability outcomes."],
                        "bullet_improvement_guidelines": [
                            "Emphasize measurable impact before describing actions.",
                            "Add quantification placeholders (e.g., [X%]) for latency improvements.",
                        ],
                    },
                    "education": {
                        "status": "present",
                        "reasoning": "Degree information complete.",
                        "instructions_for_editor_agent": ["Retain GPA and honors if relevant."],
                    },
                },
                "potential_add_pending_verification": ["Experience with Kubernetes"],
                "orchestrator_priority_actions": [
                    "Surface distributed systems ownership in bullets.",
                    "Add Kubernetes experience in Technologies bucket.",
                    "Quantify reliability improvements from pipelines.",
                ],
            }
            return FakeResponse(json.dumps(payload))

        if system_text.startswith("You are the Resume Planning & Structuring Orchestrator Agent"):
            payload = {
                "section_guidance": {
                    "header": {
                        "status": "present",
                        "reasoning": "Resume context includes name, email, and links.",
                        "instructions_for_editor_agent": [
                            "Confirm contact info is formatted on a single line.",
                            "Add location clarity (city, state).",
                        ],
                    },
                    "skills": {
                        "status": "present",
                        "reasoning": "Skills list provided but lacks grouping nuances.",
                        "instructions_for_editor_agent": [
                            "Separate cloud tooling from programming languages.",
                            "Add automation tooling references where supported.",
                        ],
                        "skill_bucket_adjustments": {
                            "Programming Languages": {"add": ["SQL"], "de_emphasize": []},
                            "Technologies": {"add": ["Airflow"], "de_emphasize": []},
                            "Tools": {"add": ["Looker"], "de_emphasize": []},
                        },
                    },
                    "experience": {
                        "status": "present",
                        "reasoning": "Employment history includes role, company, and bullets.",
                        "instructions_for_editor_agent": [
                            "Rework bullets to follow impact → action → context.",
                            "Add quantification for pipeline throughput and reliability.",
                        ],
                        "bullet_improvement_guidelines": [
                            "Convert bullets to result → action → context form",
                            "Add quantification placeholders (e.g., [X%]/[Xms]/[X$])",
                            "Remove filler verbs such as 'helped', 'worked on'",
                        ],
                    },
                    "education": {
                        "status": "present",
                        "reasoning": "Degree details clearly extracted.",
                        "instructions_for_editor_agent": ["Include academic honors if available."],
                    },
                },
                "potential_add_pending_verification": ["Certifications for cloud security"],
                "orchestrator_priority_actions": [
                    "Tighten bullet phrasing with measurable outcomes.",
                    "Group skills into ATS-friendly buckets.",
                    "Highlight leadership within data engineering initiatives.",
                ],
            }
            return FakeResponse(json.dumps(payload))

        if system_text.startswith("Your task is to generate a personal summary section"):
            payload = [
                {
                    "agent_id": "resume_applicant",
                    "personal_summary": (
                        "I am a software engineer who builds reliable data pipelines on GCP, partnering with product teams to scale features for millions of users. "
                        "I specialize in Python automation, infrastructure-as-code, and distributed processing."
                    ),
                }
            ]
            return FakeResponse(json.dumps(payload))

        if system_text.startswith("Create a resume builder agent that takes structured data"):
            payload = {
                "header": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "location": "Mountain View, CA",
                    "linkedin": "https://linkedin.com/in/johndoe",
                    "github": "https://github.com/johndoe",
                },
                "professional_summary": "Software engineer building reliable GCP data platforms.",
                "skills": {
                    "Programming Languages": ["Python", "SQL"],
                    "Technologies": ["GCP", "Kubernetes"],
                    "Tools": ["Git", "Terraform"],
                },
                "experience": [
                    "Software Engineer at Tech Labs (2021-Present): Designed pipelines supporting 2TB daily throughput.",
                ],
                "education": [
                    {
                        "degree": "B.S. Computer Science",
                        "institution": "Stanford University",
                        "dates": "2017-2021",
                        "location": "Stanford, CA",
                        "gpa": "3.8/4.0",
                    }
                ],
                "awards": ["Employee of the Quarter (2023)"],
            }
            return FakeResponse(json.dumps(payload))

        if system_text.startswith("You are to optimize a resume provided in JSON format"):
            payload = {
                "header": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "location": "Mountain View, CA",
                    "linkedin": "https://linkedin.com/in/johndoe",
                    "github": "https://github.com/johndoe",
                },
                "professional_summary": "Software engineer delivering resilient GCP platforms and cross-team solutions.",
                "skills": {
                    "Programming Languages": ["Python", "SQL"],
                    "Technologies": ["GCP", "Kubernetes"],
                    "Tools": ["Git", "Terraform"],
                },
                "experience": [
                    "Boosted pipeline throughput by 35% through Python automation and GCP orchestration.",
                ],
                "education": [
                    {
                        "degree": "B.S. Computer Science",
                        "institution": "Stanford University",
                        "dates": "2017-2021",
                        "location": "Stanford, CA",
                        "gpa": "3.8/4.0",
                    }
                ],
                "awards": ["Employee of the Quarter (2023)"],
            }
            return FakeResponse(json.dumps(payload))

        raise AssertionError(f"Unexpected system prompt: {system_text[:60]}...")

    def parse(self, **request):
        """Mimic the Responses API `.parse` helper by delegating to `.create`."""

        return self.create(**request)


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses = FakeResponsesAPI()


class ResumeWorkflowSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_client = FakeOpenAIClient()

    def test_job_tuning_mode_runs_alignment_branch(self):
        workflow = ResumeJsonWorkflow(client=self.fake_client)
        result = workflow.run(
            resume_text=FAKE_RESUME_TEXT,
            job_description=FAKE_JOB_DESCRIPTION,
            ats_keywords=FAKE_ATS_KEYWORDS,
            mode="job_tuning",
            additional_context={"source": "linkedin"},
        )

        self.assertTrue(result.should_align_to_job)
        self.assertIsNone(result.resume_improvement_guidance)
        self.assertIsNotNone(result.job_alignment_guidance)
        self.assertEqual(
            result.optimized_resume_json.parsed["professional_summary"],
            "Software engineer delivering resilient GCP platforms and cross-team solutions.",
        )

    def test_resume_improvement_mode_skips_job_agents(self):
        workflow = ResumeJsonWorkflow(client=FakeOpenAIClient())
        result = workflow.run(
            resume_text=FAKE_RESUME_TEXT,
            mode="resume_improvement",
        )

        self.assertFalse(result.should_align_to_job)
        self.assertIsNone(result.job_alignment_guidance)
        self.assertIsNotNone(result.resume_improvement_guidance)
        self.assertIn(
            "impact → action → context",
            result.resume_improvement_guidance.parsed["section_guidance"]["experience"]["instructions_for_editor_agent"][0],
        )


if __name__ == "__main__":
    unittest.main()
