"""Tests for security module."""

import pytest
from pathlib import Path

from cedarscript_mcp.security import PathValidator, SecurityError


def test_path_traversal_blocked(validator):
    """Test that path traversal attacks are blocked."""
    with pytest.raises(SecurityError, match="Path escape attempt"):
        validator.validate_path("../../../etc/passwd")


def test_relative_path_resolution(validator, temp_project_root):
    """Test that relative paths are properly resolved."""
    resolved = validator.validate_path("myfile.py")
    assert resolved == temp_project_root / "myfile.py"


def test_absolute_path_within_root(validator, temp_project_root):
    """Test that absolute paths within root are allowed."""
    abs_path = str(temp_project_root / "myfile.py")
    resolved = validator.validate_path(abs_path)
    assert resolved == temp_project_root / "myfile.py"


def test_absolute_path_outside_root(validator):
    """Test that absolute paths outside root are blocked."""
    with pytest.raises(SecurityError, match="Path escape"):
        validator.validate_path("/etc/passwd")


def test_denylist_git_directory(validator):
    """Test that .git directory is denied."""
    with pytest.raises(SecurityError, match="denylist"):
        validator.validate_path(".git/config")


def test_denylist_env_file(validator):
    """Test that .env files are denied."""
    with pytest.raises(SecurityError, match="denylist"):
        validator.validate_path(".env")

    with pytest.raises(SecurityError, match="denylist"):
        validator.validate_path("config.env")


def test_denylist_credentials(validator):
    """Test that credential files are denied."""
    with pytest.raises(SecurityError, match="denylist"):
        validator.validate_path("credentials.json")


def test_read_only_mode_blocks_writes(temp_project_root):
    """Test that read-only mode blocks write operations."""
    validator = PathValidator(temp_project_root, read_only=True)

    # Reading should work
    validator.validate_path("myfile.py", for_write=False)

    # Writing should fail
    with pytest.raises(SecurityError, match="read-only mode"):
        validator.validate_path("myfile.py", for_write=True)


def test_file_size_limits(temp_project_root):
    """Test file size limit enforcement."""
    # Create large file
    large_file = temp_project_root / "large.txt"
    large_file.write_bytes(b"x" * (11 * 1024 * 1024))  # 11MB

    validator = PathValidator(temp_project_root, max_file_size=10 * 1024 * 1024)

    # Should raise error when reading large file
    with pytest.raises(SecurityError, match="exceeds maximum size"):
        validator.validate_path("large.txt")


def test_nested_path_validation(validator, temp_project_root):
    """Test validation of nested directory paths."""
    resolved = validator.validate_path("src/utils.py")
    assert resolved == temp_project_root / "src" / "utils.py"


def test_symlink_resolution(validator, temp_project_root):
    """Test that symlinks are resolved and validated."""
    # Create symlink
    link = temp_project_root / "link_to_myfile.py"
    target = temp_project_root / "myfile.py"
    link.symlink_to(target)

    resolved = validator.validate_path("link_to_myfile.py")
    assert resolved == target


def test_validate_root_nonexistent(temp_project_root):
    """Test that nonexistent root directory raises error."""
    validator = PathValidator(temp_project_root)

    with pytest.raises(SecurityError, match="does not exist"):
        validator.validate_root("/nonexistent/path")


def test_validate_root_not_directory(temp_project_root):
    """Test that file path as root raises error."""
    validator = PathValidator(temp_project_root)

    file_path = str(temp_project_root / "myfile.py")
    with pytest.raises(SecurityError, match="not a directory"):
        validator.validate_root(file_path)


def test_custom_denylist(temp_project_root):
    """Test custom denylist patterns."""
    validator = PathValidator(temp_project_root, denylist=["*.tmp", "cache/**"])

    # Default patterns should not apply
    validator.validate_path(".env")  # Should NOT raise (custom denylist)

    # Custom patterns should apply
    with pytest.raises(SecurityError, match="denylist"):
        validator.validate_path("tempfile.tmp")

    with pytest.raises(SecurityError, match="denylist"):
        validator.validate_path("cache/data.json")
