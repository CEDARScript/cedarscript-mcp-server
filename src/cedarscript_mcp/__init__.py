"""CEDARScript MCP Server - AI-assisted code transformations."""

from cedarscript_mcp._version import __version__

from .adapters import MCPError, translate_exception
from .security import PathValidator, SecurityError
from .server import main
from .tools import (
    apply_cedarscript_tool,
    list_capabilities_tool,
    parse_cedarscript_tool,
)

__all__ = [
    "main",
    "parse_cedarscript_tool",
    "apply_cedarscript_tool",
    "list_capabilities_tool",
    "PathValidator",
    "SecurityError",
    "translate_exception",
    "MCPError",
]
