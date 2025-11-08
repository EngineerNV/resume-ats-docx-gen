"""Command-line interface for resume generator."""

import sys
from pathlib import Path

import click

from resume_gen.generator import generate_resume_from_json


@click.group()
def cli():
    """ATS-friendly resume generator from JSON to DOCX."""
    pass


def _warn_if_non_json(path: Path) -> None:
    """Emit a friendly warning when inputs lack a .json extension."""
    if path.suffix.lower() != '.json':
        click.echo(f"Warning: Input file '{path}' does not have .json extension.")


@cli.command()
@click.option('--in', 'input_file', required=True, type=click.Path(exists=True),
              help='Input JSON file path')
@click.option('--out', 'output_file', required=True, type=click.Path(),
              help='Output DOCX file path')
def render(input_file, output_file):
    """Render a resume from JSON to DOCX format.
    
    Example:
        resume-gen render --in draft.json --out resume.docx
    """
    try:
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        _warn_if_non_json(input_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate resume
        click.echo(f"Generating resume from '{input_file}'...")
        generate_resume_from_json(input_path, output_path)
        click.echo(f"Resume successfully generated: '{output_file}'")
        
    except Exception as e:
        click.echo(f"Error generating resume: {str(e)}", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
