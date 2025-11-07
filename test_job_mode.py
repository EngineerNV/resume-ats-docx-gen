"""
Test OpenAI Agents SDK workflow with job description (job mode).
"""

import asyncio
import json
import os
from pathlib import Path
from app_agents.workflows import ResumeOrchestrator


def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


SAMPLE_RESUME = """
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

# Real Google job description for Senior Software Engineer
JOB_DESCRIPTION = """
Senior Software Engineer, Cloud Infrastructure

Google - Mountain View, CA

Minimum qualifications:
• Bachelor's degree in Computer Science or equivalent practical experience
• 5 years of experience with software development in one or more programming languages (e.g., Python, C, C++, Java, JavaScript)
• 3 years of experience with data structures or algorithms
• 3 years of experience with full software development life cycle, including coding standards, code reviews, source control management, build processes, testing, and operations

Preferred qualifications:
• Master's degree or PhD in Computer Science or related technical field
• Experience developing accessible technologies
• Experience with distributed systems and cloud infrastructure
• Strong understanding of containerization (Docker, Kubernetes)
• Experience with Infrastructure as Code (Terraform, CloudFormation)

About the job:
Google's software engineers develop the next-generation technologies that change how billions of users connect, explore, and interact with information and one another. We're looking for engineers who bring fresh ideas from all areas, including distributed computing, large-scale system design, networking, data storage, security, artificial intelligence, UI design and mobile.

As a Senior Software Engineer on the Cloud Infrastructure team, you will work on critical projects that power Google Cloud Platform. You'll design, develop, test, deploy, maintain, and enhance software solutions that enable our customers to build and scale their applications.

Responsibilities:
• Write product or system development code
• Participate in, or lead design reviews with peers and stakeholders to decide amongst available technologies
• Review code developed by other developers and provide feedback to ensure best practices
• Contribute to existing documentation or educational content and adapt content based on product/program updates and user feedback
• Triage product or system issues and debug/track/resolve by analyzing the sources of issues and the impact on hardware, network, or service operations and quality
"""

async def main():
    load_env()
    
    print("\n=== OpenAI Agents SDK Test (JOB MODE) ===\n")
    
    orchestrator = ResumeOrchestrator()
    
    print("Running workflow with job description...")
    print(f"Job: Senior Software Engineer at Google\n")
    
    result = await orchestrator.run(
        resume_text=SAMPLE_RESUME,
        job_description=JOB_DESCRIPTION
    )
    
    print(f"\n✅ SUCCESS!")
    print(f"Mode: {result.mode}")
    print(f"Filename: {result.filename}")
    
    if result.job_research_output:
        print(f"\n📊 Job Research Output (first 500 chars):")
        print(result.job_research_output[:500] + "...")
    
    print(f"\n📄 Full Optimized Resume JSON:")
    print(json.dumps(result.optimized_resume_json, indent=2))
    
    # Save to file
    output_dir = Path("outbox")
    output_dir.mkdir(exist_ok=True)
    json_path = output_dir / result.filename.replace('.docx', '_job_mode.json')
    
    with open(json_path, 'w') as f:
        json.dump({
            "mode": result.mode,
            "filename": result.filename,
            "job_research": result.job_research_output,
            "optimized_resume": result.optimized_resume_json
        }, f, indent=2)
    
    print(f"\n✅ Saved to: {json_path}")

if __name__ == "__main__":
    asyncio.run(main())
