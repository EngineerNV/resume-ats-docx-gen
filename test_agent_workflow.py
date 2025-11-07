"""
Test the unified OpenAI Agents SDK resume generation workflow.

This demonstrates the complete end-to-end workflow from resume text to DOCX file.
"""

import asyncio
from pathlib import Path

from app_agents.workflows import ResumeOrchestrator
from resume_gen.generator import ResumeGenerator


# Sample resume
SAMPLE_RESUME = """
John Smith
john.smith@email.com
San Francisco, CA
linkedin.com/in/johnsmith

Experienced software engineer with 5+ years in full-stack development.

SKILLS
Python, JavaScript, React, Node.js, AWS, Docker, PostgreSQL

EXPERIENCE
Senior Software Engineer - Tech Corp
San Francisco, CA | Jan 2021 - Present
- Led development of microservices serving 1M+ users
- Reduced API latency by 40%
- Mentored 3 junior engineers

Software Engineer - StartupCo  
San Francisco, CA | Jun 2019 - Dec 2020
- Built React SaaS frontend
- Implemented REST APIs with Django
- Deployed on AWS with Docker

EDUCATION
B.S. Computer Science - UC Berkeley
2015 - 2019, GPA: 3.7
"""

# Sample job description
SAMPLE_JOB = """
Senior Full Stack Engineer

Requirements:
- 5+ years software development
- Python and JavaScript proficiency
- React experience
- AWS/cloud platform experience
- Microservices architecture
- Strong problem-solving

Responsibilities:
- Design scalable web applications
- Collaborate cross-functionally
- Mentor engineers
- Drive technical decisions
"""


async def test_resume_improvement():
    """Test: Resume improvement (no job description)"""
    print("\n" + "="*70)
    print("TEST 1: Resume Improvement Mode")
    print("="*70)
    
    orchestrator = ResumeOrchestrator()
    
    print("\nRunning OpenAI Agents SDK workflow...")
    result = await orchestrator.run(
        resume_text=SAMPLE_RESUME,
        additional_context="Focus on technical skills and achievements"
    )
    
    print(f"\n✓ Mode: {result.mode}")
    print(f"✓ Filename: {result.filename}")
    print(f"✓ Reasoning: {result.reasoning}")
    
    # Generate DOCX
    output_dir = Path("outbox")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / result.filename
    
    generator = ResumeGenerator(result.optimized_resume_json)
    generator.generate(output_path)
    
    print(f"\n✓ DOCX generated: {output_path}")
    print(f"  Size: {output_path.stat().st_size:,} bytes")
    
    return result


async def test_job_tuning():
    """Test: Job tuning (with job description)"""
    print("\n" + "="*70)
    print("TEST 2: Job Tuning Mode")
    print("="*70)
    
    orchestrator = ResumeOrchestrator()
    
    print("\nRunning OpenAI Agents SDK workflow with job description...")
    result = await orchestrator.run(
        resume_text=SAMPLE_RESUME,
        job_description=SAMPLE_JOB,
        additional_context="Optimize for this role"
    )
    
    print(f"\n✓ Mode: {result.mode}")
    print(f"✓ Filename: {result.filename}")
    print(f"✓ Reasoning: {result.reasoning}")
    
    if result.job_research_output:
        print(f"✓ Job research completed")
    
    # Generate DOCX
    output_dir = Path("outbox")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"job_tuned_{result.filename}"
    
    generator = ResumeGenerator(result.optimized_resume_json)
    generator.generate(output_path)
    
    print(f"\n✓ DOCX generated: {output_path}")
    print(f"  Size: {output_path.stat().st_size:,} bytes")
    
    return result


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("OpenAI Agents SDK Resume Generation - End-to-End Test")
    print("="*70)
    
    try:
        result1 = await test_resume_improvement()
        result2 = await test_job_tuning()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)
        print(f"\nGenerated files in outbox/:")
        print(f"  - {result1.filename}")
        print(f"  - job_tuned_{result2.filename}")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*70)
        print("✗ TEST FAILED")
        print("="*70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))



# Sample resume text
SAMPLE_RESUME = """
John Smith
john.smith@email.com
San Francisco, CA
linkedin.com/in/johnsmith
github.com/johnsmith

SUMMARY
Experienced software engineer with 5 years of experience in full-stack development.
Strong background in Python, JavaScript, and cloud technologies.

SKILLS
- Programming Languages: Python, JavaScript, TypeScript, Java
- Frameworks: React, Node.js, Django, Flask
- Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes
- Databases: PostgreSQL, MongoDB, Redis
- Tools: Git, Jenkins, CircleCI

EXPERIENCE

Senior Software Engineer - Tech Corp
San Francisco, CA | Jan 2021 - Present
- Led development of microservices architecture serving 1M+ users
- Reduced API response time by 40% through optimization
- Mentored team of 3 junior engineers

Software Engineer - StartupCo
San Francisco, CA | Jun 2019 - Dec 2020
- Built React frontend for SaaS application
- Implemented RESTful APIs using Django
- Deployed applications on AWS using Docker

EDUCATION
B.S. Computer Science - University of California, Berkeley
Berkeley, CA | 2015 - 2019
GPA: 3.7/4.0

AWARDS
- Dean's List (2017-2019)
- Best Capstone Project Award (2019)
"""

# Sample job description
SAMPLE_JOB_DESCRIPTION = """
Senior Full Stack Engineer

We are looking for an experienced Full Stack Engineer to join our team.

Requirements:
- 5+ years of professional software development experience
- Strong proficiency in Python and JavaScript
- Experience with React and modern frontend frameworks
- Cloud platform experience (AWS, Azure, or GCP)
- Experience with microservices architecture
- Strong problem-solving skills
- Excellent communication skills

Nice to have:
- Experience with Kubernetes
- DevOps experience
- Open source contributions

Responsibilities:
- Design and develop scalable web applications
- Collaborate with cross-functional teams
- Mentor junior engineers
- Participate in code reviews
- Drive technical decisions
"""


async def test_resume_improvement_mode():
    """Test resume improvement mode (no job description)."""
    print("\n" + "="*80)
    print("TEST 1: Resume Improvement Mode")
    print("="*80 + "\n")
    
    orchestrator = ResumeOrchestrator()
    
    print("Running workflow...")
    result = await orchestrator.run_complete_workflow(
        resume_text=SAMPLE_RESUME,
        job_description=None,
        additional_context="Please focus on technical skills and quantifiable achievements."
    )
    
    print(f"\nMode: {result.mode}")
    print(f"Filename: {result.filename}")
    print(f"Reasoning: {result.reasoning}")
    
    print("\nOptimized Resume JSON:")
    print(json.dumps(result.optimized_resume_json, indent=2)[:500] + "...")
    
    # Generate DOCX
    print("\nGenerating DOCX...")
    output_dir = Path("outbox")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / result.filename
    generator = ResumeGenerator(result.optimized_resume_json)
    generator.generate(output_path)
    
    print(f"✓ DOCX generated: {output_path}")
    print(f"  File size: {output_path.stat().st_size} bytes")
    
    return result


async def test_job_tuning_mode():
    """Test job tuning mode (with job description)."""
    print("\n" + "="*80)
    print("TEST 2: Job Tuning Mode")
    print("="*80 + "\n")
    
    orchestrator = ResumeOrchestrator()
    
    print("Running workflow...")
    result = await orchestrator.run_complete_workflow(
        resume_text=SAMPLE_RESUME,
        job_description=SAMPLE_JOB_DESCRIPTION,
        additional_context="Optimize for this specific role."
    )
    
    print(f"\nMode: {result.mode}")
    print(f"Filename: {result.filename}")
    print(f"Reasoning: {result.reasoning}")
    
    if result.job_research_data:
        print("\nJob Research Data:")
        print(json.dumps(result.job_research_data, indent=2)[:300] + "...")
    
    print("\nOptimized Resume JSON:")
    print(json.dumps(result.optimized_resume_json, indent=2)[:500] + "...")
    
    # Generate DOCX
    print("\nGenerating DOCX...")
    output_dir = Path("outbox")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / f"job_tuned_{result.filename}"
    generator = ResumeGenerator(result.optimized_resume_json)
    generator.generate(output_path)
    
    print(f"✓ DOCX generated: {output_path}")
    print(f"  File size: {output_path.stat().st_size} bytes")
    
    return result


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("OpenAI Agents SDK Resume Generation Workflow Tests")
    print("="*80)
    
    try:
        # Test 1: Resume improvement mode
        result1 = await test_resume_improvement_mode()
        
        # Test 2: Job tuning mode
        result2 = await test_job_tuning_mode()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nSummary:")
        print(f"  - Resume Improvement: {result1.filename}")
        print(f"  - Job Tuning: job_tuned_{result2.filename}")
        print(f"\nOutput files in: outbox/")
        
    except Exception as e:
        print("\n" + "="*80)
        print("ERROR OCCURRED")
        print("="*80)
        print(f"\nError: {str(e)}")
        import traceback
        print("\nTraceback:")
        print(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
