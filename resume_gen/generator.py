"""Core resume generation logic using python-docx."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


class ResumeGenerator:
    """Generates ATS-friendly resumes in DOCX format from JSON input."""
    
    # Font and size constants
    FONT_NAME = "Calibri"
    BODY_FONT_SIZE = 11
    NAME_FONT_SIZE = 16
    SECTION_HEADER_FONT_SIZE = 12
    MARGIN_SIZE = 36  # 0.5 inch in points
    
    def __init__(self, json_data: Dict[str, Any]):
        """Initialize generator with JSON data.
        
        Args:
            json_data: Dictionary containing resume data
        """
        self.data = json_data
        self.doc = Document()
        self._setup_document()
    
    def _setup_document(self):
        """Setup document margins and default styles."""
        # Set narrow margins for better space usage (0.5 inches)
        sections = self.doc.sections
        for section in sections:
            section.top_margin = Pt(self.MARGIN_SIZE)
            section.bottom_margin = Pt(self.MARGIN_SIZE)
            section.left_margin = Pt(self.MARGIN_SIZE)
            section.right_margin = Pt(self.MARGIN_SIZE)
    
    def _add_paragraph(self, text: str, bold: bool = False, 
                      font_size: int = None, alignment: str = "left",
                      space_after: int = 6) -> None:
        """Add a formatted paragraph to the document.
        
        Args:
            text: Text content
            bold: Whether text should be bold
            font_size: Font size in points (defaults to BODY_FONT_SIZE)
            alignment: Text alignment (left, center, right)
            space_after: Space after paragraph in points
        """
        para = self.doc.add_paragraph()
        run = para.add_run(text)
        
        # Set font properties
        run.font.name = self.FONT_NAME
        run.font.size = Pt(font_size if font_size else self.BODY_FONT_SIZE)
        run.bold = bold
        run.font.color.rgb = RGBColor(0, 0, 0)
        
        # Set alignment
        if alignment == "center":
            para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        elif alignment == "right":
            para.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        else:
            para.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        
        # Set spacing
        para.paragraph_format.space_after = Pt(space_after)
        para.paragraph_format.space_before = Pt(0)
    
    def _add_header_section(self):
        """Add header section with name and contact information."""
        header_data = self.data.get("header", {})
        
        # Name - 16pt bold
        name = header_data.get("name", "")
        if name:
            self._add_paragraph(name, bold=True, font_size=self.NAME_FONT_SIZE, 
                              alignment="center", space_after=4)
        
        # Contact info - single line, centered
        contact_parts = []
        if "email" in header_data:
            contact_parts.append(header_data["email"])
        if "phone" in header_data:
            contact_parts.append(header_data["phone"])
        if "location" in header_data:
            contact_parts.append(header_data["location"])
        if "linkedin" in header_data:
            contact_parts.append(header_data["linkedin"])
        if "github" in header_data:
            contact_parts.append(header_data["github"])
        
        if contact_parts:
            contact_line = " | ".join(contact_parts)
            self._add_paragraph(contact_line, alignment="center", space_after=12)
    
    def _add_section_header(self, title: str):
        """Add a section header (uppercase, 12pt bold).
        
        Args:
            title: Section title
        """
        self._add_paragraph(title.upper(), bold=True, 
                          font_size=self.SECTION_HEADER_FONT_SIZE,
                          space_after=6)
    
    def _add_bullet_paragraph(self, text: str):
        """Add a bullet point paragraph with proper formatting.
        
        Args:
            text: Bullet point text
        """
        para = self.doc.add_paragraph(text, style='List Bullet')
        para.paragraph_format.space_after = Pt(2)
        para.paragraph_format.space_before = Pt(0)
        
        # Set font for bullet text
        for run in para.runs:
            run.font.name = self.FONT_NAME
            run.font.size = Pt(self.BODY_FONT_SIZE)
            run.font.color.rgb = RGBColor(0, 0, 0)
    
    def _add_skills_section(self):
        """Add skills section."""
        skills_data = self.data.get("skills", [])
        if not skills_data:
            return
        
        self._add_section_header("Skills")
        
        # Group skills by category if provided, otherwise show as list
        if isinstance(skills_data, dict):
            for category, skills in skills_data.items():
                if isinstance(skills, list):
                    skills_text = ", ".join(skills)
                else:
                    skills_text = skills
                self._add_paragraph(f"{category}: {skills_text}", space_after=4)
        elif isinstance(skills_data, list):
            skills_text = ", ".join(skills_data)
            self._add_paragraph(skills_text, space_after=8)
    
    def _add_experience_section(self):
        """Add experience section with roles, companies, dates, and bullets."""
        experience_data = self.data.get("experience", [])
        if not experience_data:
            return
        
        self._add_section_header("Experience")
        
        for i, job in enumerate(experience_data):
            # Job title and company - bold
            role = job.get("role", "")
            company = job.get("company", "")
            title_line = f"{role}, {company}" if role and company else role or company
            
            if title_line:
                self._add_paragraph(title_line, bold=True, space_after=2)
            
            # Dates and location
            dates = job.get("dates", "")
            location = job.get("location", "")
            date_line_parts = []
            if dates:
                date_line_parts.append(dates)
            if location:
                date_line_parts.append(location)
            
            if date_line_parts:
                date_line = " | ".join(date_line_parts)
                self._add_paragraph(date_line, space_after=4)
            
            # Bullet points (starting with action verbs)
            bullets = job.get("bullets", [])
            for bullet in bullets:
                self._add_bullet_paragraph(bullet)
            
            # Add space after each job (except the last one)
            if i < len(experience_data) - 1:
                self._add_paragraph("", space_after=6)
    
    def _add_education_section(self):
        """Add education section."""
        education_data = self.data.get("education", [])
        if not education_data:
            return
        
        self._add_section_header("Education")
        
        for edu in education_data:
            # Degree and institution - bold
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            title_line = f"{degree}, {institution}" if degree and institution else degree or institution
            
            if title_line:
                self._add_paragraph(title_line, bold=True, space_after=2)
            
            # Dates and location
            dates = edu.get("dates", "")
            location = edu.get("location", "")
            gpa = edu.get("gpa", "")
            
            detail_parts = []
            if dates:
                detail_parts.append(dates)
            if location:
                detail_parts.append(location)
            if gpa:
                detail_parts.append(f"GPA: {gpa}")
            
            if detail_parts:
                detail_line = " | ".join(detail_parts)
                self._add_paragraph(detail_line, space_after=8)
    
    def _add_awards_section(self):
        """Add awards and achievements section."""
        awards_data = self.data.get("awards", [])
        if not awards_data:
            return
        
        self._add_section_header("Awards")
        
        for award in awards_data:
            if isinstance(award, str):
                # Simple string award
                self._add_bullet_paragraph(award)
            elif isinstance(award, dict):
                # Award with details
                title = award.get("title", "")
                date = award.get("date", "")
                description = award.get("description", "")
                
                award_text = title
                if date:
                    award_text += f" ({date})"
                if description:
                    award_text += f" - {description}"
                
                self._add_bullet_paragraph(award_text)
    
    def generate(self, output_path: Path):
        """Generate the resume document.
        
        Args:
            output_path: Path where the DOCX file will be saved
        """
        # Add all sections in order
        self._add_header_section()
        self._add_skills_section()
        self._add_experience_section()
        self._add_education_section()
        self._add_awards_section()
        
        # Save the document
        self.doc.save(str(output_path))


def generate_resume_from_json(json_path: Path, output_path: Path):
    """Generate resume from JSON file.
    
    Args:
        json_path: Path to input JSON file
        output_path: Path to output DOCX file
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    generator = ResumeGenerator(data)
    generator.generate(output_path)
