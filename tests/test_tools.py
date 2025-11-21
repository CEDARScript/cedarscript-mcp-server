"""Tests for MCP tools."""

import pytest

from cedarscript_mcp.tools import list_capabilities_tool
from cedarscript_mcp.security import SecurityError


def test_list_capabilities():
    """Test capabilities listing."""
    caps = list_capabilities_tool()

    assert "server" in caps
    assert caps["server"] == "cedarscript-mcp-server"
    assert "version" in caps
    assert "features" in caps
    assert "security" in caps

    # Check features
    assert "UPDATE" in caps["features"]["commands"]
    assert "CREATE" in caps["features"]["commands"]
    assert "DELETE" in caps["features"]["commands"]

    # Check security features
    assert caps["security"]["path_validation"] is True
    assert caps["security"]["read_only_mode"] is True


# NOTE: Previously skipped tests have been enabled - they now use
# sample CEDARScript commands from conftest.py fixtures.

def test_parse_valid_cedarscript(sample_cedarscript_commands):
    """Test parsing valid CEDARScript commands."""
    from cedarscript_mcp.tools import parse_cedarscript_tool

    result = parse_cedarscript_tool(sample_cedarscript_commands["simple_update"])

    assert result["success"] is True
    assert result["count"] >= 1


def test_apply_cedarscript_fenced_removed(sample_cedarscript_commands, temp_project_root, validator):
    """Test applying CEDARScript without fenced parameter."""
    from cedarscript_mcp.tools import apply_cedarscript_tool

    result = apply_cedarscript_tool(
        commands=sample_cedarscript_commands["simple_update"],
        root=str(temp_project_root),
        dry_run=True,
        validator=validator,
    )

    assert result["success"] is True
    assert result["dry_run"] is True




def test_apply_invalid_root():
    """Test that invalid root path raises error."""
    from cedarscript_mcp.tools import apply_cedarscript_tool

    with pytest.raises(SecurityError, match="does not exist"):
        apply_cedarscript_tool(
            commands="",  # Empty commands to test root validation first
            root="/nonexistent/path",
            dry_run=True,
        )
