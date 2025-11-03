"""
Quick reference for testing the MCP server with Copilot.

Copy-paste these examples into VS Code Copilot Chat to test the resume generator.
"""

# Example 1: Minimal Resume
minimal_resume = {
    "header": {
        "name": "Alex Johnson",
        "email": "alex@example.com",
        "linkedin": "linkedin.com/in/alexj",
        "github": "github.com/alexj"
    },
    "skills": {
        "Languages": ["Python", "JavaScript", "Go"],
        "Cloud": ["AWS", "GCP", "Azure"]
    },
    "experience": [{
        "role": "Software Engineer",
        "company": "Tech Startup",
        "dates": "2022 - Present",
        "location": "San Francisco, CA",
        "bullets": [
            "Built scalable microservices handling 5M+ requests daily",
            "Reduced cloud costs by 35% through optimization"
        ]
    }],
    "education": [{
        "degree": "BS Computer Science",
        "institution": "Stanford University",
        "dates": "2018 - 2022",
        "gpa": "3.9/4.0"
    }]
}

# Example 2: Resume with Subsections (Complex)
advanced_resume = {
    "header": {
        "name": "Sarah Martinez",
        "email": "sarah.martinez@email.com",
        "phone": "(555) 123-4567",
        "location": "Austin, TX",
        "linkedin": "linkedin.com/in/sarahmartinez",
        "github": "github.com/smartinez"
    },
    "professional_summary": "Full-stack engineer with 5+ years building AI-powered products",
    "skills": {
        "Languages": ["Python", "TypeScript", "Rust"],
        "AI/ML": ["PyTorch", "LangChain", "OpenAI API"],
        "Infrastructure": ["Kubernetes", "Terraform", "PostgreSQL"]
    },
    "experience": [{
        "role": "Senior Software Engineer",
        "company": "AI Innovations Inc",
        "dates": "2021 - Present",
        "location": "Austin, TX",
        "subsections": [{
            "header": "AI Platform Development",
            "bullets": [
                "Architected RAG system processing 100K+ documents with 95% accuracy",
                "Led team of 4 engineers building production ML pipelines"
            ]
        }, {
            "header": "Infrastructure & Scale",
            "bullets": [
                "Migrated monolith to microservices, improving deployment speed 10x",
                "Reduced cloud costs $50K/month through optimization"
            ]
        }]
    }],
    "education": [{
        "degree": "M.S. Computer Science",
        "institution": "UT Austin",
        "dates": "2019 - 2021",
        "gpa": "4.0/4.0"
    }],
    "awards": [
        "Employee of the Year (2023)",
        {"title": "Best AI Innovation", "date": "2022", "description": "Internal hackathon"}
    ]
}

# Copilot Chat Prompts to Try:

PROMPT_1 = """
@workspace Generate a resume using this data and save as alex_johnson.docx:
{minimal_resume}
"""

PROMPT_2 = """
@workspace Create a software engineering resume for Sarah Martinez.
Use subsections to organize her AI and Infrastructure work.
Include: Python, TypeScript, PyTorch, LangChain, Kubernetes
Save as sarah_martinez.docx
"""

PROMPT_3 = """
@workspace Show me what resume templates are available using the template:// resource
"""

PROMPT_4 = """
@workspace I need to create a resume for a senior data scientist role.
Name: David Chen
Email: david.chen@email.com
Skills: Python, SQL, Tableau, Spark
5 years of experience in fintech
Save it as david_chen_data_scientist.docx
"""

PROMPT_5 = """
@workspace Generate a resume highlighting my backend development skills.
Focus on microservices, databases, and API design.
Make it ATS-friendly.
"""

# After generation, access the file:
ACCESS_EXAMPLE = """
@workspace Can you read the resume we just generated from outbox://alex_johnson.docx
and summarize what's in it?
"""
