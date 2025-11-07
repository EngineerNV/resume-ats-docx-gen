#!/usr/bin/env python
"""
Comprehensive test for FastAPI server's integration with OpenAI Agents and DOCX generation.

Tests:
1. Server health check
2. JSON workflow endpoint (resume mode)
3. JSON workflow endpoint (job mode)
4. DOCX workflow endpoint (resume mode)
5. DOCX workflow endpoint (job mode)
6. Validation of generated DOCX files
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Optional
import subprocess
import sys

import httpx


# Test data
SAMPLE_RESUME = """
Jane Smith
jane.smith@example.com | San Francisco, CA
linkedin.com/in/janesmith | github.com/janesmith

PROFESSIONAL SUMMARY
Senior Software Engineer with 6+ years of experience building scalable web applications
and distributed systems. Expert in Python, JavaScript, and cloud infrastructure.

SKILLS
Languages: Python, JavaScript, TypeScript, Go
Frameworks: React, FastAPI, Django, Node.js
Cloud & DevOps: AWS, Docker, Kubernetes, Terraform, CI/CD
Databases: PostgreSQL, MongoDB, Redis

EXPERIENCE

Senior Software Engineer | TechCorp Inc. | San Francisco, CA | Jan 2021 - Present
- Lead development of microservices architecture serving 2M+ daily active users
- Reduced API response time by 45% through optimization and caching strategies
- Mentor team of 5 junior engineers on best practices and code reviews
- Implemented comprehensive monitoring and alerting using Datadog and PagerDuty

Software Engineer | StartupXYZ | San Jose, CA | Jun 2018 - Dec 2020
- Built React-based customer dashboard used by 10,000+ enterprise clients
- Designed and implemented RESTful APIs using Python FastAPI
- Created automated deployment pipeline reducing release time from 2 hours to 15 minutes
- Collaborated with product team to define technical requirements

Junior Developer | WebDev Solutions | Remote | Jan 2017 - May 2018
- Developed responsive websites using HTML, CSS, JavaScript
- Maintained and updated legacy codebases
- Participated in agile development processes

EDUCATION
B.S. Computer Science | University of California, Berkeley | 2013 - 2017
GPA: 3.8/4.0
Relevant Coursework: Algorithms, Data Structures, Distributed Systems, Machine Learning

PROJECTS
Open Source Contributor | GitHub
- Active contributor to popular Python and JavaScript open-source projects
- Contributed to FastAPI, React Query, and other major libraries

Personal Portfolio Site
- Built with Next.js and deployed on Vercel
- Showcases projects and technical blog posts
"""

SAMPLE_JOB_DESCRIPTION = """
Staff Software Engineer - Cloud Infrastructure

About the Role:
We're seeking an experienced Staff Software Engineer to join our Cloud Infrastructure team.
You'll lead the design and implementation of scalable cloud-native systems that power our platform.

Requirements:
- 5+ years of software engineering experience
- Strong expertise in Python and modern web frameworks (FastAPI, Django)
- Deep understanding of cloud platforms (AWS, GCP, or Azure)
- Experience with Kubernetes, Docker, and container orchestration
- Proven track record of building and scaling distributed systems
- Experience with Infrastructure as Code (Terraform, CloudFormation)
- Strong leadership and mentoring skills
- Excellent communication and collaboration abilities

Responsibilities:
- Design and implement highly scalable cloud infrastructure
- Lead technical initiatives and mentor engineering teams
- Build and maintain CI/CD pipelines and automation tools
- Ensure system reliability, security, and performance
- Collaborate with cross-functional teams on architecture decisions
- Drive best practices for code quality and testing

Nice to Have:
- Experience with Kubernetes operators and custom controllers
- Knowledge of observability tools (Prometheus, Grafana, Datadog)
- Background in Site Reliability Engineering (SRE)
- Open source contributions
- Experience with GraphQL and modern API design
"""


class FastAPITester:
    """Test runner for FastAPI server with agents and DOCX generation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.server_process: Optional[subprocess.Popen] = None
        # Get project root (parent of tests directory)
        self.project_root = Path(__file__).parent.parent
        self.output_dir = self.project_root / "outbox"
        self.output_dir.mkdir(exist_ok=True)
        
    def load_env(self):
        """Load environment variables from .env file."""
        env_path = self.project_root / ".env"
        if not env_path.exists():
            print("⚠️  Warning: .env file not found. Create one with OPENAI_API_KEY")
            return False
        
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        
        if not os.environ.get('OPENAI_API_KEY'):
            print("❌ OPENAI_API_KEY not found in .env file")
            return False
        
        print("✓ Loaded environment variables")
        return True
    
    def start_server(self) -> bool:
        """Start the FastAPI server in background."""
        print("\n🚀 Starting FastAPI server...")
        
        # Use the .venv python from project root
        venv_python = self.project_root / ".venv" / "bin" / "python"
        if not venv_python.exists():
            print(f"❌ Virtual environment not found at {venv_python}")
            return False
        
        # Start server using uvicorn
        cmd = [
            str(venv_python),
            "-m", "uvicorn",
            "api.server:app",
            "--host", "127.0.0.1",
            "--port", "8000",
        ]
        
        try:
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Wait for server to start
            print("⏳ Waiting for server to start...")
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = httpx.get(f"{self.base_url}/", timeout=2.0)
                    if response.status_code == 200:
                        print(f"✓ Server started successfully on {self.base_url}")
                        return True
                except (httpx.ConnectError, httpx.TimeoutException):
                    time.sleep(1)
                    if i % 5 == 0:
                        print(f"  Still waiting... ({i+1}s)")
            
            print("❌ Server failed to start within 30 seconds")
            self.stop_server()
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the FastAPI server."""
        if self.server_process:
            print("\n🛑 Stopping FastAPI server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            print("✓ Server stopped")
    
    async def test_health_check(self) -> bool:
        """Test server health check endpoint."""
        print("\n📋 Test 1: Health Check")
        print("-" * 60)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/")
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                    print("✅ Health check passed")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Health check error: {e}")
                return False
    
    async def test_json_workflow_resume_mode(self) -> bool:
        """Test JSON workflow endpoint in resume improvement mode."""
        print("\n📋 Test 2: JSON Workflow - Resume Mode")
        print("-" * 60)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/workflow/json",
                    data={
                        "mode": "resume",
                        "resumeText": SAMPLE_RESUME,
                        "context": "Looking to highlight leadership and cloud expertise",
                    }
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if not data.get("ok"):
                        print(f"❌ API returned error: {data}")
                        return False
                    
                    result = data.get("data", {})
                    print(f"Mode: {result.get('mode')}")
                    print(f"Filename: {result.get('filename')}")
                    
                    # Check optimized resume JSON
                    resume_json = result.get("optimized_resume_json", {})
                    if resume_json:
                        print(f"✓ Resume JSON contains:")
                        print(f"  - Header: {bool(resume_json.get('header'))}")
                        print(f"  - Skills: {bool(resume_json.get('skills'))}")
                        print(f"  - Experience: {bool(resume_json.get('experience'))}")
                        print(f"  - Education: {bool(resume_json.get('education'))}")
                        
                        # Verify structure
                        has_required = all([
                            resume_json.get('header'),
                            resume_json.get('skills'),
                            resume_json.get('experience'),
                            resume_json.get('education'),
                        ])
                        
                        if has_required:
                            print("✅ JSON workflow (resume mode) passed")
                            return True
                        else:
                            print("❌ Resume JSON missing required fields")
                            return False
                    else:
                        print("❌ No optimized_resume_json in response")
                        return False
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    print(f"Response: {response.text[:500]}")
                    return False
                    
            except Exception as e:
                print(f"❌ Test error: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    async def test_json_workflow_job_mode(self) -> bool:
        """Test JSON workflow endpoint in job tuning mode."""
        print("\n📋 Test 3: JSON Workflow - Job Mode")
        print("-" * 60)
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/workflow/json",
                    data={
                        "mode": "job",
                        "resumeText": SAMPLE_RESUME,
                        "jobDescriptionText": SAMPLE_JOB_DESCRIPTION,
                        "context": "Emphasize cloud infrastructure and leadership experience",
                    }
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if not data.get("ok"):
                        print(f"❌ API returned error: {data}")
                        return False
                    
                    result = data.get("data", {})
                    print(f"Mode: {result.get('mode')}")
                    print(f"Filename: {result.get('filename')}")
                    
                    # Check job research output
                    job_research = result.get("job_research_output")
                    if job_research:
                        print(f"✓ Job research output ({len(job_research)} chars)")
                        print(f"  Preview: {job_research[:200]}...")
                    
                    # Check optimized resume JSON
                    resume_json = result.get("optimized_resume_json", {})
                    if resume_json:
                        print(f"✓ Resume JSON contains:")
                        print(f"  - Header: {bool(resume_json.get('header'))}")
                        print(f"  - Skills: {bool(resume_json.get('skills'))}")
                        print(f"  - Experience: {bool(resume_json.get('experience'))}")
                        print(f"  - Education: {bool(resume_json.get('education'))}")
                        
                        # Verify structure
                        has_required = all([
                            resume_json.get('header'),
                            resume_json.get('skills'),
                            resume_json.get('experience'),
                            resume_json.get('education'),
                        ])
                        
                        if has_required:
                            print("✅ JSON workflow (job mode) passed")
                            return True
                        else:
                            print("❌ Resume JSON missing required fields")
                            return False
                    else:
                        print("❌ No optimized_resume_json in response")
                        return False
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    print(f"Response: {response.text[:500]}")
                    return False
                    
            except Exception as e:
                print(f"❌ Test error: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    async def test_docx_workflow_resume_mode(self) -> bool:
        """Test DOCX workflow endpoint in resume improvement mode."""
        print("\n📋 Test 4: DOCX Workflow - Resume Mode")
        print("-" * 60)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/workflow/docx",
                    data={
                        "mode": "resume",
                        "resumeText": SAMPLE_RESUME,
                        "context": "Looking to highlight leadership and cloud expertise",
                    }
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    # Check content type
                    content_type = response.headers.get("content-type", "")
                    print(f"Content-Type: {content_type}")
                    
                    if "officedocument" not in content_type.lower():
                        print(f"⚠️  Unexpected content type: {content_type}")
                    
                    # Get filename from headers
                    content_disp = response.headers.get("content-disposition", "")
                    print(f"Content-Disposition: {content_disp}")
                    
                    # Save file
                    filename = "test_resume_mode.docx"
                    output_path = self.output_dir / filename
                    
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    
                    file_size = output_path.stat().st_size
                    print(f"✓ DOCX file saved: {output_path}")
                    print(f"  File size: {file_size:,} bytes")
                    
                    if file_size > 1000:  # Should be at least 1KB
                        print("✅ DOCX workflow (resume mode) passed")
                        return True
                    else:
                        print("❌ DOCX file too small, likely corrupted")
                        return False
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    print(f"Response: {response.text[:500]}")
                    return False
                    
            except Exception as e:
                print(f"❌ Test error: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    async def test_docx_workflow_job_mode(self) -> bool:
        """Test DOCX workflow endpoint in job tuning mode."""
        print("\n📋 Test 5: DOCX Workflow - Job Mode")
        print("-" * 60)
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/workflow/docx",
                    data={
                        "mode": "job",
                        "resumeText": SAMPLE_RESUME,
                        "jobDescriptionText": SAMPLE_JOB_DESCRIPTION,
                        "context": "Emphasize cloud infrastructure and leadership experience",
                    }
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    # Check content type
                    content_type = response.headers.get("content-type", "")
                    print(f"Content-Type: {content_type}")
                    
                    if "officedocument" not in content_type.lower():
                        print(f"⚠️  Unexpected content type: {content_type}")
                    
                    # Get filename from headers
                    content_disp = response.headers.get("content-disposition", "")
                    print(f"Content-Disposition: {content_disp}")
                    
                    # Save file
                    filename = "test_job_mode.docx"
                    output_path = self.output_dir / filename
                    
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    
                    file_size = output_path.stat().st_size
                    print(f"✓ DOCX file saved: {output_path}")
                    print(f"  File size: {file_size:,} bytes")
                    
                    if file_size > 1000:  # Should be at least 1KB
                        print("✅ DOCX workflow (job mode) passed")
                        return True
                    else:
                        print("❌ DOCX file too small, likely corrupted")
                        return False
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    print(f"Response: {response.text[:500]}")
                    return False
                    
            except Exception as e:
                print(f"❌ Test error: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    async def run_all_tests(self) -> bool:
        """Run all tests in sequence."""
        print("=" * 70)
        print("FastAPI + Agents + DOCX Generation Test Suite")
        print("=" * 70)
        
        # Load environment
        if not self.load_env():
            print("\n❌ Environment setup failed")
            return False
        
        # Start server
        if not self.start_server():
            print("\n❌ Server startup failed")
            return False
        
        try:
            # Run tests
            results = []
            
            results.append(("Health Check", await self.test_health_check()))
            results.append(("JSON Resume Mode", await self.test_json_workflow_resume_mode()))
            results.append(("JSON Job Mode", await self.test_json_workflow_job_mode()))
            results.append(("DOCX Resume Mode", await self.test_docx_workflow_resume_mode()))
            results.append(("DOCX Job Mode", await self.test_docx_workflow_job_mode()))
            
            # Print summary
            print("\n" + "=" * 70)
            print("Test Summary")
            print("=" * 70)
            
            for test_name, passed in results:
                status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"{test_name:30} {status}")
            
            total = len(results)
            passed = sum(1 for _, p in results if p)
            
            print(f"\nTotal: {passed}/{total} tests passed")
            
            if passed == total:
                print("\n🎉 All tests passed!")
                return True
            else:
                print(f"\n⚠️  {total - passed} test(s) failed")
                return False
            
        finally:
            self.stop_server()


async def main():
    """Main entry point."""
    tester = FastAPITester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
