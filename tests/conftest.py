"""Pytest fixtures for CEDARScript MCP Server tests."""

import pytest
from pathlib import Path


@pytest.fixture
def temp_project_root(tmp_path):
    """Create temporary project directory with sample files."""
    project = tmp_path / "test_project"
    project.mkdir()

    # Create sample Python file
    (project / "myfile.py").write_text(
        "import sys\n\ndef calculate(x):\n    return x + 1\n"
    )

    # Create sample README
    (project / "README.md").write_text("# Test Project\n")

    # Create nested directory with file
    nested = project / "src"
    nested.mkdir()
    (nested / "utils.py").write_text("def helper():\n    pass\n")

    yield project

    # Cleanup handled by tmp_path fixture


@pytest.fixture
def validator(temp_project_root):
    """Create PathValidator for tests."""
    from cedarscript_mcp.security import PathValidator

    return PathValidator(temp_project_root)


@pytest.fixture
def sample_cedarscript_commands():
    """Sample CEDARScript commands for testing."""
    return {
        "simple_update": r'''
UPDATE FILE "main.something" DELETE LINE 'risus cursus';
''',
    }
