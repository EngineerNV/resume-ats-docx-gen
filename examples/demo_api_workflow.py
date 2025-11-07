#!/usr/bin/env python
"""
Example script demonstrating the FastAPI + MCP integration workflow.

This script shows how the FastAPI server orchestrates:
1. OpenAI agent workflow for resume optimization
2. MCP server tool for DOCX generation
"""

import json
import os
from pathlib import Path

# Sample resume text
SAMPLE_RESUME = """
John Doe
Email: john.doe@example.com
Phone: (555) 123-4567
Location: San Francisco, CA
LinkedIn: linkedin.com/in/johndoe
GitHub: github.com/johndoe

SUMMARY
Software Engineer with 5 years of experience building scalable web applications.

EXPERIENCE
Senior Software Engineer, Tech Corp (2020-Present)
- Developed microservices architecture handling 1M+ requests/day
- Led team of 4 engineers on payment processing system
- Improved API response time by 40%

Software Engineer, StartupXYZ (2018-2020)
- Built React frontend for customer dashboard
- Implemented CI/CD pipeline reducing deployment time by 60%
- Collaborated with product team on feature specifications

EDUCATION
B.S. Computer Science, University of California (2014-2018)
GPA: 3.7/4.0

SKILLS
Languages: Python, JavaScript, Go
Frameworks: React, FastAPI, Django
Tools: Docker, Kubernetes, AWS
"""

SAMPLE_JOB_DESCRIPTION = """
Software Engineer - Google Cloud Platform

We're looking for a Software Engineer to join our Google Cloud Platform team.

Requirements:
- 3+ years of software development experience
- Strong proficiency in Python and Go
- Experience with Kubernetes and containerization
- Knowledge of distributed systems and microservices
- Experience with cloud platforms (GCP, AWS, or Azure)
- Strong communication and collaboration skills

Responsibilities:
- Design and implement large-scale distributed systems
- Build reliable cloud-native services
- Collaborate with cross-functional teams
- Ensure solutions meet security and reliability standards
"""


def demo_workflow_integration():
    """Demonstrate the workflow without actually calling OpenAI APIs."""
    print("=" * 70)
    print("FastAPI + MCP Integration Demo")
    print("=" * 70)
    print()
    
    print("This demo shows how the FastAPI server orchestrates:")
    print("1. Resume text input from user")
    print("2. OpenAI agent workflow (optimizes resume)")
    print("3. MCP server tool (generates DOCX)")
    print()
    
    # Show the inputs
    print("📄 Input Resume Text:")
    print("-" * 70)
    print(SAMPLE_RESUME[:200] + "...\n")
    
    print("💼 Job Description (for job-tuning mode):")
    print("-" * 70)
    print(SAMPLE_JOB_DESCRIPTION[:200] + "...\n")
    
    # Explain the workflow
    print("🔄 Workflow Process:")
    print("-" * 70)
    print("1. Frontend sends POST request to /api/workflow/json or /api/workflow/docx")
    print("2. FastAPI server validates input and determines mode (job/resume)")
    print("3. Agent workflow (ResumeJsonWorkflow) processes the resume:")
    print("   - Extracts structured context")
    print("   - Generates optimized JSON")
    print("   - Aligns with job description (if provided)")
    print("4. MCP server tool (generate_resume_tool) creates DOCX")
    print("5. FastAPI returns JSON suggestions or DOCX file\n")
    
    # Show MCP integration
    print("🔗 MCP Integration:")
    print("-" * 70)
    print("The FastAPI server calls MCP tools directly (no separate server needed):")
    print()
    print("```python")
    print("from resume_mcp.tools import generate_resume_tool")
    print()
    print("result = generate_resume_tool(")
    print("    resume_data=optimized_json,")
    print("    filename='resume.docx'")
    print(")")
    print("```")
    print()
    
    # Test MCP tool
    print("🧪 Testing MCP Tool:")
    print("-" * 70)
    
    try:
        from resume_mcp.tools import generate_resume_tool
        
        # Load example resume for testing
        example_path = Path(__file__).parent.parent / "example_resume.json"
        with open(example_path) as f:
            resume_data = json.load(f)
        
        result = generate_resume_tool(
            resume_data=resume_data,
            filename="demo_output.docx"
        )
        
        if result["success"]:
            print(f"✅ MCP tool successfully generated: {result['path']}")
            print(f"📦 Access via MCP resource: {result['uri']}")
        else:
            print(f"❌ MCP tool failed: {result['message']}")
    
    except Exception as e:
        print(f"⚠️  Could not test MCP tool: {e}")
    
    print()
    
    # Show API endpoints
    print("🌐 API Endpoints:")
    print("-" * 70)
    print("Health Check:")
    print("  GET http://localhost:8000/")
    print()
    print("Get JSON Suggestions:")
    print("  POST http://localhost:8000/api/workflow/json")
    print("  Form Data: mode=resume|job, resumeText=..., jobDescriptionText=...")
    print()
    print("Generate DOCX:")
    print("  POST http://localhost:8000/api/workflow/docx")
    print("  Form Data: mode=resume|job, resumeText=..., jobDescriptionText=...")
    print()
    
    # Show how to start
    print("🚀 Quick Start:")
    print("-" * 70)
    print("1. Set OPENAI_API_KEY in .env file")
    print("2. Start the server: resume-api")
    print("3. Visit http://localhost:8000/docs for interactive API testing")
    print("4. Or configure frontend to use the API endpoints")
    print()
    
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("For full integration testing with OpenAI:")
    print("  1. Set up .env with your OPENAI_API_KEY")
    print("  2. Run: python -m app_agents.scripts.run_resume_workflow --mode job_tuning")
    print()


if __name__ == "__main__":
    demo_workflow_integration()
