"""MCP tool definitions for CEDARScript operations."""

from pathlib import Path
from typing import Annotated, Optional

from cedarscript_editor import CEDARScriptEditor, find_commands

from .adapters import generate_diff, serialize_command
from .security import PathValidator, SecurityError


def parse_cedarscript_tool(
    content: Annotated[str, "CEDARScript commands to parse"],
) -> dict:
    """
    Parse and validate CEDARScript commands without execution.

    This tool validates syntax and returns the parsed AST commands.
    Use this for dry-run validation before applying changes.

    Args:
        content: CEDARScript command string

    Returns:
        dict with success status and parsed commands

    Raises:
        ValueError: If parsing fails
    """
    try:
        parsed = list(find_commands(content))
        return {
            "success": True,
            "count": len(parsed),
            "commands": [serialize_command(cmd) for cmd in parsed],
        }
    except ValueError as e:
        raise ValueError(f"CEDARScript parse error: {e}")


def apply_cedarscript_tool(
    commands: Annotated[str, "CEDARScript commands to apply"],
    root: Annotated[str, "Project root directory path"],
    dry_run: Annotated[bool, "Preview changes without writing"] = True,
    validator: Optional[PathValidator] = None,  # Injected by server
) -> dict:
    """
    Apply CEDARScript transformations to code files.

    By default, runs in dry-run mode (preview only, no file writes).
    Set dry_run=False to execute changes.

    Args:
        commands: CEDARScript command string
        root: Absolute path to project root
        dry_run: If True, preview changes; if False, execute
        validator: PathValidator instance (injected)

    Returns:
        dict with results, diffs (if dry_run), affected files

    Raises:
        SecurityError: If path validation fails
        ValueError: If parsing fails
        CEDARScriptEditorException: If execution fails
    """
    # Validate root
    if validator is None:
        validator = PathValidator(Path(root))

    root_path = validator.validate_root(root)

    # Parse commands
    parsed = list(find_commands(commands))

    if dry_run:
        # Dry-run: Generate preview
        # Note: Full diff generation would require intercepting file writes
        # This is a simplified version
        return {
            "success": True,
            "dry_run": True,
            "preview": {
                "command_count": len(parsed),
                "commands": [serialize_command(cmd) for cmd in parsed],
                "note": "Dry-run mode: Commands parsed successfully. Full diff generation requires execution context.",
            },
        }
    else:
        # Execute: Apply changes
        if validator.read_only:
            raise SecurityError("Write operation rejected: server in read-only mode")

        editor = CEDARScriptEditor(str(root_path))
        results = editor.apply_commands(parsed)

        return {
            "success": True,
            "dry_run": False,
            "results": results,
            "command_count": len(parsed),
        }


def list_capabilities_tool() -> dict:
    """
    List CEDARScript MCP server capabilities.

    Returns supported CEDARScript features and server version.

    Returns:
        dict with capabilities and version info
    """
    return {
        "server": "cedarscript-mcp-server",
        "version": "0.1.0",
        "cedarscript_editor_version": _get_cedarscript_version(),
        "features": {
            "commands": ["UPDATE", "CREATE", "DELETE", "MOVE"],
            "segments": ["imports", "functions", "classes", "methods"],
            "actions": ["INSERT", "DELETE", "REPLACE", "MOVE"],
            "dry_run": True,
            "tree_sitter": True,
        },
        "security": {
            "path_validation": True,
            "read_only_mode": True,
            "file_size_limits": True,
        },
    }


def _get_cedarscript_version() -> str:
    """Get cedarscript-editor version."""
    try:
        import cedarscript_editor

        return getattr(cedarscript_editor, "__version__", "unknown")
    except Exception:
        return "unknown"
