# resume-ats-docx-gen

A Python CLI tool that generates ATS-friendly resumes in DOCX format from JSON input.

## Features

- **ATS-Optimized Format**: Single column layout optimized for Applicant Tracking Systems
- **Professional Typography**: Calibri font with proper sizing (11pt body, 16pt name, 12pt headers)
- **Structured Sections**: Header, Skills, Experience, Education, and Awards
- **Action-Oriented**: Experience bullets designed to start with strong action verbs
- **No Tables or Images**: Clean, parseable format without complex elements

## Installation

```bash
pip install -e .
```

## Usage

Generate a resume from a JSON file:

```bash
resume-gen render --in draft.json --out resume.docx
```

### Command Options

- `--in`: Path to input JSON file (required)
- `--out`: Path to output DOCX file (required)

## JSON Format

The input JSON should follow this structure:

```json
{
  "header": {
    "name": "Your Name",
    "email": "your.email@example.com",
    "phone": "(555) 123-4567",
    "location": "City, State",
    "linkedin": "linkedin.com/in/yourprofile",
    "github": "github.com/yourusername"
  },
  "skills": {
    "Category 1": ["Skill 1", "Skill 2", "Skill 3"],
    "Category 2": ["Skill A", "Skill B"]
  },
  "experience": [
    {
      "role": "Job Title",
      "company": "Company Name",
      "dates": "Month Year - Present",
      "location": "City, State",
      "bullets": [
        "Action verb describing achievement with quantifiable results",
        "Another accomplishment starting with action verb"
      ]
    }
  ],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "University Name",
      "dates": "Year - Year",
      "location": "City, State",
      "gpa": "3.X/4.0"
    }
  ],
  "awards": [
    "Award Name (Year)",
    {
      "title": "Award Title",
      "date": "Year",
      "description": "Brief description"
    }
  ]
}
```

See `example_resume.json` for a complete example.

## Example

```bash
# Generate resume using the example file
resume-gen render --in example_resume.json --out my_resume.docx
```

## Requirements

- Python 3.8+
- python-docx >= 0.8.11
- click >= 8.0.0

## License

MIT
