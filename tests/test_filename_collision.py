from pathlib import Path

import pytest

from app_agents.workflows import resume_orchestrator as ro


def test_generate_filename_includes_timestamp_for_name():
    orchestrator = ro.ResumeOrchestrator()
    resume = {"header": {"name": "Alice Liddell"}}
    filename, _ = orchestrator._generate_filename(resume)
    assert filename.endswith('.docx')
    assert 'alice_liddell_resume_' in filename or filename.startswith('alice_liddell_resume_')
    # timestamp parseable
    core = filename[:-5].rsplit('_', 1)[-1]
    from datetime import datetime
    fmt = '%Y%m%dT%H%M%SZ'
    datetime.strptime(core, fmt)


def test_generate_filename_for_empty_name_uses_resume_with_timestamp():
    orchestrator = ro.ResumeOrchestrator()
    resume = {"header": {}}
    filename, _ = orchestrator._generate_filename(resume)
    assert filename.endswith('.docx')
    assert filename.startswith('resume_')
    core = filename[:-5].rsplit('_', 1)[-1]
    from datetime import datetime
    fmt = '%Y%m%dT%H%M%SZ'
    datetime.strptime(core, fmt)
