"""Adapters for CEDARScript <-> MCP protocol translation."""

import traceback
from typing import Any

from cedarscript_editor.cedarscript_editor import CEDARScriptEditorException


class MCPError:
    """MCP JSON-RPC error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Application errors
    SECURITY_ERROR = -32001
    PARSE_ERROR_CEDAR = -32002
    EXECUTION_ERROR = -32003


def translate_exception(exc: Exception, request_id: Any = None) -> dict:
    """
    Translate Python exceptions to MCP error responses.

    Args:
        exc: Exception to translate
        request_id: JSON-RPC request ID

    Returns:
        MCP error response dict
    """
    from .security import SecurityError

    if isinstance(exc, SecurityError):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": MCPError.SECURITY_ERROR,
                "message": "Security violation",
                "data": {
                    "type": "SecurityError",
                    "details": str(exc),
                    "suggestions": [
                        "Verify the path is within the project root",
                        "Check file patterns against denylist",
                        "Ensure server is not in read-only mode (if writing)",
                    ],
                },
            },
        }

    elif isinstance(exc, CEDARScriptEditorException):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": MCPError.EXECUTION_ERROR,
                "message": "CEDARScript execution failed",
                "data": {
                    "type": "ExecutionError",
                    "command_index": getattr(exc, "ordinal", None),
                    "details": str(exc),
                    "suggestions": _parse_suggestions_from_exception(exc),
                },
            },
        }

    elif isinstance(exc, ValueError):
        # Likely a CEDARScript parse error
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": MCPError.PARSE_ERROR_CEDAR,
                "message": "CEDARScript parse error",
                "data": {
                    "type": "ParseError",
                    "details": str(exc),
                    "suggestions": [
                        "Check CEDARScript syntax",
                        "Valid commands: UPDATE, CREATE, DELETE, MOVE",
                        "Use parse_cedarscript tool to validate before applying",
                    ],
                },
            },
        }

    else:
        # Generic internal error
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": MCPError.INTERNAL_ERROR,
                "message": "Internal server error",
                "data": {
                    "type": exc.__class__.__name__,
                    "details": str(exc),
                    "traceback": traceback.format_exc(),
                },
            },
        }


def _parse_suggestions_from_exception(exc: CEDARScriptEditorException) -> list[str]:
    """Extract actionable suggestions from CEDARScript exception."""
    suggestions = []
    exc_str = str(exc)

    # Common patterns in CEDARScript exceptions
    if "file not found" in exc_str.lower():
        suggestions.extend(
            [
                "Verify the file path is correct",
                "Check if file exists in project root",
                "Consider using CREATE command if file should be created",
            ]
        )
    elif "marker not found" in exc_str.lower():
        suggestions.extend(
            [
                "Re-analyze the file structure (it may have changed)",
                "Use line numbers instead of markers if structure is unstable",
                "Verify the function/class name is correct",
            ]
        )
    else:
        suggestions.append("Re-run parse_cedarscript to validate command syntax")

    return suggestions


def serialize_command(command: Any) -> dict:
    """
    Serialize CEDARScript AST Command to JSON-serializable dict.

    Args:
        command: CEDARScript Command AST node

    Returns:
        JSON-serializable dict representation
    """
    # Simplified serialization - expand based on actual AST structure
    result = {
        "type": command.__class__.__name__,
    }

    # Add common fields if they exist
    for attr in ["target", "action", "content", "segment"]:
        if hasattr(command, attr):
            value = getattr(command, attr)
            # Convert to serializable form
            if isinstance(value, (str, int, float, bool, type(None))):
                result[attr] = value
            elif isinstance(value, list):
                result[attr] = [str(v) for v in value]
            else:
                result[attr] = str(value)

    return result


def generate_diff(original: list[str], modified: list[str], filename: str) -> str:
    """
    Generate unified diff between original and modified content.

    Args:
        original: Original file lines
        modified: Modified file lines
        filename: File name for diff header

    Returns:
        Unified diff string
    """
    import difflib

    diff = difflib.unified_diff(
        original, modified, fromfile=f"a/{filename}", tofile=f"b/{filename}", lineterm=""
    )

    return "\n".join(diff)
