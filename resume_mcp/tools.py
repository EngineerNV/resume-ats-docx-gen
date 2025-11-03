"""
Tool implementations for MCP server.

Provides the generate_resume tool that creates DOCX files from JSON data.
"""

from pathlib import Path
from typing import Any, Dict

from pydantic import ValidationError

from resume_gen.generator import ResumeGenerator
from resume_mcp.models import Resume


def generate_resume_tool(resume_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """
    Generate ATS-friendly resume DOCX from validated JSON data.
    
    This function is called by the MCP server after Pydantic validation.
    It directly uses the resume_gen.generator module (no CLI wrapper).
    
    Args:
        resume_data: Validated resume dictionary
        filename: Output filename (must end with .docx)
        
    Returns:
        Success: {
            "success": True,
            "path": "/path/to/file.docx",
            "uri": "outbox://file.docx",
            "message": "Resume generated successfully",
            "filename": "file.docx"
        }
        
        Error: {
            "success": False,
            "error": "error_type",
            "message": "Human-readable error message",
            "details": "Additional context for debugging"
        }
    """
    # Create outbox directory in the project root
    # Get the project root (parent of resume_mcp directory)
    project_root = Path(__file__).parent.parent
    outbox = project_root / "outbox"
    outbox.mkdir(exist_ok=True)
    
    output_path = outbox / filename
    
    try:
        # Validate resume data using Pydantic model
        # This provides strict validation with detailed errors
        resume = Resume(**resume_data)
        
        # Convert back to dict for generator (generator expects dict, not Pydantic model)
        validated_data = resume.model_dump()
        
        # Generate DOCX using direct generator call (no CLI!)
        generator = ResumeGenerator(validated_data)
        generator.generate(output_path)
        
        # Return success with full details
        return {
            "success": True,
            "path": str(output_path),
            "uri": f"outbox://{filename}",
            "message": f"✅ Resume generated successfully: {filename}",
            "filename": filename,
        }
        
    except ValidationError as e:
        # Pydantic validation failed - return structured errors
        errors = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error['loc'])
            errors.append(f"  • {field}: {error['msg']}")
        
        error_details = "\n".join(errors)
        
        return {
            "success": False,
            "error": "validation_failed",
            "message": "❌ Resume validation failed. Fix the following issues:",
            "details": error_details,
            "suggestion": "Review the required schema. Use template:// resources to see valid examples.",
        }
        
    except KeyError as e:
        # Missing required field in data that passed Pydantic but failed in generator
        return {
            "success": False,
            "error": "missing_field",
            "message": f"❌ Missing required field: {str(e)}",
            "details": "Required fields: header.name, header.email, and at least one of (experience, education, skills)",
        }
        
    except ValueError as e:
        # Invalid value in data
        return {
            "success": False,
            "error": "invalid_value",
            "message": f"❌ Invalid value: {str(e)}",
            "details": str(e),
        }
        
    except PermissionError as e:
        # File system permission issue
        return {
            "success": False,
            "error": "permission_denied",
            "message": f"❌ Cannot write to output directory: {outbox}",
            "details": str(e),
        }
        
    except Exception as e:
        # Catch-all for unexpected errors
        return {
            "success": False,
            "error": "generation_failed",
            "message": f"❌ Resume generation failed: {str(e)}",
            "details": f"Error type: {type(e).__name__}\nMessage: {str(e)}",
            "suggestion": "Check that your resume JSON matches the required schema.",
        }


def get_outbox_location() -> str:
    """
    Get the current outbox directory path.
    
    Returns:
        Absolute path to outbox directory
    """
    project_root = Path(__file__).parent.parent
    outbox = project_root / "outbox"
    return str(outbox)
