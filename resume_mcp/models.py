"""
Pydantic validation models for resume data.

These models enforce strict validation matching the existing JSON schema
used by the resume generator.
"""

from typing import Optional, Dict, List, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class Header(BaseModel):
    """Contact information header."""
    
    name: str = Field(..., min_length=1, description="Full name")
    email: str = Field(..., min_length=3, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="City, State")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")


class Subsection(BaseModel):
    """Experience subsection with header and bullets."""
    
    header: str = Field(..., min_length=1, description="Subsection header (e.g., 'BACKEND DEVELOPMENT')")
    bullets: List[str] = Field(..., min_items=1, description="Achievement bullets for this subsection")


class ExperienceEntry(BaseModel):
    """Work experience entry."""
    
    role: str = Field(..., min_length=1, description="Job title")
    company: str = Field(..., min_length=1, description="Company name")
    dates: str = Field(..., min_length=1, description="Employment dates (e.g., 'Jan 2020 - Present')")
    location: Optional[str] = Field(None, description="City, State")
    bullets: Optional[List[str]] = Field(None, description="Achievement bullets (use this OR subsections)")
    subsections: Optional[List[Subsection]] = Field(None, description="Organized subsections (use this OR bullets)")
    
    @model_validator(mode='after')
    def check_bullets_or_subsections(self):
        """Ensure either bullets or subsections is provided."""
        if not self.bullets and not self.subsections:
            raise ValueError(
                "Experience entry must include either 'bullets' or 'subsections'. "
                "Provide at least one to describe your achievements."
            )
        return self


class EducationEntry(BaseModel):
    """Education entry."""
    
    degree: str = Field(..., min_length=1, description="Degree name (e.g., 'Bachelor of Science in Computer Science')")
    institution: str = Field(..., min_length=1, description="University or institution name")
    dates: str = Field(..., min_length=1, description="Years attended (e.g., '2015 - 2019')")
    location: Optional[str] = Field(None, description="City, State")
    gpa: Optional[str] = Field(None, description="GPA (e.g., '3.8/4.0')")


class AwardDetail(BaseModel):
    """Detailed award entry."""
    
    title: str = Field(..., min_length=1, description="Award title")
    date: Optional[str] = Field(None, description="Date received")
    description: Optional[str] = Field(None, description="Award description")


class Resume(BaseModel):
    """Complete resume data structure.
    
    This model validates the entire resume JSON and ensures all required
    fields are present with appropriate values.
    """
    
    header: Header = Field(..., description="Contact information")
    professional_summary: Optional[Union[str, List[str]]] = Field(
        None, 
        description="Professional summary (single string or list of paragraphs)"
    )
    skills: Optional[Union[Dict[str, List[str]], List[str]]] = Field(
        None,
        description="Skills as categories dict (e.g., {'Languages': ['Python']}) or simple list"
    )
    experience: Optional[List[ExperienceEntry]] = Field(None, description="Work experience entries")
    education: Optional[List[EducationEntry]] = Field(None, description="Education entries")
    awards: Optional[List[Union[str, AwardDetail]]] = Field(
        None,
        description="Awards (simple strings or detailed objects)"
    )
    
    @model_validator(mode='after')
    def check_at_least_one_section(self):
        """Ensure resume has at least one content section."""
        if not any([self.experience, self.education, self.skills]):
            raise ValueError(
                "Resume must include at least one of: 'experience', 'education', or 'skills'. "
                "A resume cannot be empty."
            )
        return self
    
    @field_validator('skills')
    @classmethod
    def validate_skills_not_empty(cls, v):
        """Ensure skills categories are not empty."""
        if v is not None:
            if isinstance(v, dict):
                for category, skills in v.items():
                    if not skills:
                        raise ValueError(f"Skills category '{category}' cannot be empty")
            elif isinstance(v, list):
                if not v:
                    raise ValueError("Skills list cannot be empty")
        return v


class ResumeGenerateRequest(BaseModel):
    """Request model for generate_resume tool."""
    
    resume: Resume = Field(..., description="Complete resume data")
    filename: str = Field(
        ...,
        min_length=1,
        description="Output filename (e.g., 'john_doe_swe.docx'). Must end with .docx",
        pattern=r"^[\w\-. ]+\.docx$"
    )
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        """Ensure filename has .docx extension."""
        if not v.endswith('.docx'):
            raise ValueError("Filename must end with .docx extension")
        # Basic sanitization
        if any(char in v for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            raise ValueError("Filename contains invalid characters")
        return v
