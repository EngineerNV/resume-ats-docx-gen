"""
Test OpenAI Agents SDK workflow without DOCX generation.
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

async def main():
    load_env()
    
    print("\n=== OpenAI Agents SDK Test ===\n")
    
    orchestrator = ResumeOrchestrator()
    
    print("Running workflow (resume improvement mode)...")
    result = await orchestrator.run(resume_text=SAMPLE_RESUME)
    
    print(f"\n✅ SUCCESS!")
    print(f"Mode: {result.mode}")
    print(f"Filename: {result.filename}")
    print(f"\nOptimized Resume JSON:")
    print(json.dumps(result.optimized_resume_json, indent=2))
    
    # Save to file
    output_dir = Path("outbox")
    output_dir.mkdir(exist_ok=True)
    json_path = output_dir / result.filename.replace('.docx', '.json')
    
    with open(json_path, 'w') as f:
        json.dump(result.optimized_resume_json, f, indent=2)
    
    print(f"\n✅ Saved to: {json_path}")

if __name__ == "__main__":
    asyncio.run(main())
