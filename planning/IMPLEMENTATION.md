# CEDARScript MCP Server - Implementation Guide

## Implementation Phases

This document provides a detailed, step-by-step implementation guide for building the CEDARScript MCP Server.

---

## Phase 1: Project Foundation

### Step 1.1: Directory Structure Creation
```bash
cedarscript-mcp-server/
├── planning/
│   ├── ARCHITECTURE.md          # ✅ Created
│   ├── IMPLEMENTATION.md        # ✅ This document
│   └── MAKEFILE_DESIGN.md       # Next
├── src/cedarscript_mcp/
│   ├── __init__.py
│   ├── server.py
│   ├── tools.py
│   ├── adapters.py
│   └── security.py
├── tests/
│   ├── conftest.py
│   ├── test_protocol.py
│   ├── test_tools.py
│   ├── test_security.py
│   └── test_integration.py
├── examples/
│   ├── claude_desktop.json
│   ├── vscode_mcp.json
│   └── quickstart.md
├── Makefile
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

### Step 1.2: Create .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Distribution
*.whl
```

### Step 1.3: Create LICENSE
```
Apache License 2.0
(Match parent project: cedarscript-editor-python)
```

---

## Phase 2: Configuration Files

### Step 2.1: pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "cedarscript-mcp-server"
version = "0.1.0"
description = "MCP server for AI-assisted code transformations via CEDARScript"
authors = [{ name = "Elifarley", email = "cedarscript@orgecc.com" }]
readme = "README.md"
license = {text = "Apache-2.0"}
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Code Generators",
]
keywords = ["mcp", "model-context-protocol", "cedarscript", "code-editing", "ai-assisted-development"]
dependencies = [
    "cedarscript-editor>=0.7.0,<1.0.0",
    "mcp>=1.0.0",
]
requires-python = ">=3.11"

[project.urls]
Homepage = "https://github.com/CEDARScript/cedarscript-mcp-server"
Documentation = "https://github.com/CEDARScript/cedarscript-mcp-server#readme"
Repository = "https://github.com/CEDARScript/cedarscript-mcp-server.git"
"Bug Tracker" = "https://github.com/CEDARScript/cedarscript-mcp-server/issues"

[project.scripts]
cedarscript-mcp = "cedarscript_mcp.server:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.0",
    "pytest-asyncio>=0.21",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.5",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
include = ["cedarscript_mcp*"]
namespaces = false

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=cedarscript_mcp --cov-report=html --cov-report=term"
testpaths = ["tests"]
```

### Step 2.2: Makefile Design
See `planning/MAKEFILE_DESIGN.md` for detailed target specifications.

---

## Phase 3: Security Module (Foundation)

### Step 3.1: security.py Implementation
**File**: `src/cedarscript_mcp/security.py`

**Purpose**: Path validation, root enforcement, security controls

```python
"""Security module for CEDARScript MCP Server."""
from pathlib import Path
from typing import Optional


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


class PathValidator:
    """Validates file paths against security constraints."""

    def __init__(
        self,
        root: Path,
        read_only: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB default
        denylist: Optional[list[str]] = None
    ):
        """
        Initialize path validator.

        Args:
            root: Root directory for all file operations
            read_only: If True, reject all write operations
            max_file_size: Maximum allowed file size in bytes
            denylist: List of glob patterns to deny (e.g., ['.git/*', '*.env'])
        """
        self.root = root.resolve()
        self.read_only = read_only
        self.max_file_size = max_file_size
        self.denylist = denylist or [
            '.git/**',
            'node_modules/**',
            '__pycache__/**',
            '.env',
            '*.env',
            '.env.*',
            'credentials.json',
            '*.key',
            '*.pem',
        ]

        if not self.root.exists():
            raise SecurityError(f"Root directory does not exist: {self.root}")
        if not self.root.is_dir():
            raise SecurityError(f"Root path is not a directory: {self.root}")

    def validate_path(self, file_path: str, for_write: bool = False) -> Path:
        """
        Validate a file path for security.

        Args:
            file_path: Relative or absolute file path
            for_write: True if path will be used for write operations

        Returns:
            Resolved absolute path

        Raises:
            SecurityError: If validation fails
        """
        # Resolve path (handles relative paths, symlinks, ..)
        if Path(file_path).is_absolute():
            resolved = Path(file_path).resolve()
        else:
            resolved = (self.root / file_path).resolve()

        # Check path is within root (prevent traversal attacks)
        try:
            resolved.relative_to(self.root)
        except ValueError:
            raise SecurityError(
                f"Path escape attempt: '{file_path}' resolves outside root directory"
            )

        # Check denylist
        relative = resolved.relative_to(self.root)
        for pattern in self.denylist:
            if relative.match(pattern):
                raise SecurityError(f"Path matches denylist pattern '{pattern}': {file_path}")

        # Check read-only mode
        if for_write and self.read_only:
            raise SecurityError("Write operation rejected: server in read-only mode")

        # Check file size (if exists and reading)
        if not for_write and resolved.exists() and resolved.is_file():
            size = resolved.stat().st_size
            if size > self.max_file_size:
                raise SecurityError(
                    f"File exceeds maximum size ({self.max_file_size} bytes): {file_path}"
                )

        return resolved

    def validate_root(self, root: str) -> Path:
        """
        Validate that a proposed root is safe.

        Args:
            root: Proposed root directory

        Returns:
            Resolved root path

        Raises:
            SecurityError: If validation fails
        """
        root_path = Path(root).resolve()

        if not root_path.exists():
            raise SecurityError(f"Root directory does not exist: {root}")
        if not root_path.is_dir():
            raise SecurityError(f"Root path is not a directory: {root}")

        return root_path
```

**Tests**: `tests/test_security.py`
- Test path traversal attempts (`../../../etc/passwd`)
- Test denylist patterns (`.git/config`, `.env`)
- Test read-only mode enforcement
- Test file size limits
- Test relative vs absolute paths

---

## Phase 4: Adapter Layer

### Step 4.1: adapters.py Implementation
**File**: `src/cedarscript_mcp/adapters.py`

**Purpose**: Protocol translation, error handling, serialization

```python
"""Adapters for CEDARScript <-> MCP protocol translation."""
import traceback
from typing import Any
from cedarscript_editor import CEDARScriptEditorException


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
                        "Ensure server is not in read-only mode (if writing)"
                    ]
                }
            }
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
                    "command_index": getattr(exc, 'ordinal', None),
                    "details": str(exc),
                    "suggestions": _parse_suggestions_from_exception(exc)
                }
            }
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
                        "Use parse_cedarscript tool to validate before applying"
                    ]
                }
            }
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
                    "traceback": traceback.format_exc()
                }
            }
        }


def _parse_suggestions_from_exception(exc: CEDARScriptEditorException) -> list[str]:
    """Extract actionable suggestions from CEDARScript exception."""
    suggestions = []
    exc_str = str(exc)

    # Common patterns in CEDARScript exceptions
    if "file not found" in exc_str.lower():
        suggestions.extend([
            "Verify the file path is correct",
            "Check if file exists in project root",
            "Consider using CREATE command if file should be created"
        ])
    elif "marker not found" in exc_str.lower():
        suggestions.extend([
            "Re-analyze the file structure (it may have changed)",
            "Use line numbers instead of markers if structure is unstable",
            "Verify the function/class name is correct"
        ])
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
    # This is a simplified serialization
    # Real implementation depends on cedarscript_ast_parser structure
    return {
        "type": command.__class__.__name__,
        "target": getattr(command, 'target', None),
        # Add more fields as needed
    }


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
        original,
        modified,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=""
    )

    return "\n".join(diff)
```

**Tests**: `tests/test_adapters.py`
- Test exception translation for each error type
- Test suggestion extraction
- Test diff generation

---

## Phase 5: Tools Layer

### Step 5.1: tools.py Implementation
**File**: `src/cedarscript_mcp/tools.py`

**Purpose**: MCP tool definitions

```python
"""MCP tool definitions for CEDARScript operations."""
from pathlib import Path
from typing import Annotated
from cedarscript_editor import CEDARScriptEditor, find_commands
from .security import PathValidator, SecurityError
from .adapters import serialize_command, generate_diff


def parse_cedarscript_tool(
    content: Annotated[str, "CEDARScript commands to parse"]
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
            "commands": [serialize_command(cmd) for cmd in parsed]
        }
    except ValueError as e:
        raise ValueError(f"CEDARScript parse error: {e}")


def apply_cedarscript_tool(
    commands: Annotated[str, "CEDARScript commands to apply"],
    root: Annotated[str, "Project root directory path"],
    dry_run: Annotated[bool, "Preview changes without writing"] = True,
    validator: PathValidator = None  # Injected by server
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
        # Dry-run: Generate diffs without writing
        editor = CEDARScriptEditor(str(root_path))

        # Mock the file writing to capture diffs
        # This is a simplified approach; real implementation needs
        # to intercept writes in CEDARScriptEditor
        results = {
            "success": True,
            "dry_run": True,
            "preview": {
                "command_count": len(parsed),
                "affected_files": [],
                "diffs": []
            }
        }

        # TODO: Implement actual dry-run diff generation
        # This requires modifying CEDARScriptEditor or mocking file I/O

        return results
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
            "command_count": len(parsed)
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
            "tree_sitter": True
        },
        "security": {
            "path_validation": True,
            "read_only_mode": True,
            "file_size_limits": True
        }
    }


def _get_cedarscript_version() -> str:
    """Get cedarscript-editor version."""
    try:
        import cedarscript_editor
        return getattr(cedarscript_editor, '__version__', 'unknown')
    except:
        return 'unknown'
```

**Tests**: `tests/test_tools.py`
- Test parse_cedarscript with valid/invalid syntax
- Test apply_cedarscript in dry-run and execute modes
- Test security validation integration
- Test error handling

---

## Phase 6: MCP Server Core

### Step 6.1: server.py Implementation
**File**: `src/cedarscript_mcp/server.py`

**Purpose**: MCP STDIO server, request handling, lifecycle

```python
#!/usr/bin/env python3
"""CEDARScript MCP Server - STDIO implementation."""
import sys
import signal
import logging
import os
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP
from .tools import (
    parse_cedarscript_tool,
    apply_cedarscript_tool,
    list_capabilities_tool
)
from .security import PathValidator, SecurityError
from .adapters import translate_exception


# Configure logging
def setup_logging(level: str = "INFO", format: str = "text"):
    """Configure logging based on environment."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    if format == "json":
        # Structured JSON logging
        import json
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                return json.dumps({
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "module": record.module,
                })
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JSONFormatter())
    else:
        # Standard text logging
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        )

    logger = logging.getLogger("cedarscript_mcp")
    logger.setLevel(log_level)
    logger.addHandler(handler)
    return logger


logger = setup_logging(
    level=os.getenv("CEDARSCRIPT_LOG_LEVEL", "INFO"),
    format=os.getenv("CEDARSCRIPT_LOG_FORMAT", "text")
)


# Initialize MCP server
mcp = FastMCP("CEDARScript Editor")


# Global validator (set via CLI args or env)
_global_validator: Optional[PathValidator] = None


def get_validator(root: Optional[str] = None) -> PathValidator:
    """Get or create path validator."""
    global _global_validator

    if root:
        return PathValidator(Path(root))

    if _global_validator is None:
        # Use environment default
        default_root = os.getenv("CEDARSCRIPT_ROOT", os.getcwd())
        read_only = os.getenv("CEDARSCRIPT_READ_ONLY", "false").lower() == "true"
        max_size = int(os.getenv("CEDARSCRIPT_MAX_FILE_SIZE", 10 * 1024 * 1024))

        _global_validator = PathValidator(
            Path(default_root),
            read_only=read_only,
            max_file_size=max_size
        )

    return _global_validator


# Register MCP tools
@mcp.tool()
def parse_cedarscript(content: str) -> dict:
    """Parse and validate CEDARScript commands."""
    logger.info("parse_cedarscript called")
    try:
        return parse_cedarscript_tool(content)
    except Exception as e:
        logger.error(f"parse_cedarscript failed: {e}")
        raise


@mcp.tool()
def apply_cedarscript(
    commands: str,
    root: str,
    dry_run: bool = True
) -> dict:
    """Apply CEDARScript transformations."""
    logger.info(f"apply_cedarscript called (root={root}, dry_run={dry_run})")
    try:
        validator = get_validator(root)
        return apply_cedarscript_tool(
            commands, root, dry_run, validator
        )
    except Exception as e:
        logger.error(f"apply_cedarscript failed: {e}")
        raise


@mcp.tool()
def list_capabilities() -> dict:
    """List server capabilities."""
    logger.info("list_capabilities called")
    return list_capabilities_tool()


# Signal handlers for graceful shutdown
def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down gracefully")
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


def main():
    """Main entry point for MCP server."""
    import argparse

    parser = argparse.ArgumentParser(
        description="CEDARScript MCP Server - AI-assisted code transformations"
    )
    parser.add_argument(
        "--root",
        type=str,
        default=os.getenv("CEDARSCRIPT_ROOT", os.getcwd()),
        help="Project root directory (default: $CEDARSCRIPT_ROOT or cwd)"
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        default=os.getenv("CEDARSCRIPT_READ_ONLY", "false").lower() == "true",
        help="Run in read-only mode (no file writes)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("CEDARSCRIPT_LOG_LEVEL", "INFO"),
        help="Logging level"
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=int(os.getenv("CEDARSCRIPT_MAX_FILE_SIZE", 10 * 1024 * 1024)),
        help="Maximum file size in bytes (default: 10MB)"
    )

    args = parser.parse_args()

    # Initialize global validator
    global _global_validator
    _global_validator = PathValidator(
        Path(args.root),
        read_only=args.read_only,
        max_file_size=args.max_file_size
    )

    logger.info(f"Starting CEDARScript MCP Server")
    logger.info(f"  Root: {args.root}")
    logger.info(f"  Read-only: {args.read_only}")
    logger.info(f"  Max file size: {args.max_file_size} bytes")

    # Run MCP server with STDIO transport
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Tests**: `tests/test_integration.py`
- Test full request/response cycle
- Test signal handling
- Test configuration from CLI args and env vars
- Test error propagation

---

## Phase 7: Package Initialization

### Step 7.1: __init__.py
**File**: `src/cedarscript_mcp/__init__.py`

```python
"""CEDARScript MCP Server - AI-assisted code transformations."""

__version__ = "0.1.0"

from .server import main
from .tools import (
    parse_cedarscript_tool,
    apply_cedarscript_tool,
    list_capabilities_tool
)
from .security import PathValidator, SecurityError
from .adapters import translate_exception, MCPError

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
```

---

## Phase 8: Documentation

### Step 8.1: README.md
See separate README.md creation task.

### Step 8.2: Example Configurations

**File**: `examples/claude_desktop.json`
```json
{
  "mcpServers": {
    "cedarscript": {
      "command": "python",
      "args": [
        "-m",
        "cedarscript_mcp.server",
        "--root",
        "${workspaceFolder}"
      ],
      "env": {
        "CEDARSCRIPT_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**File**: `examples/vscode_mcp.json`
```json
{
  "servers": {
    "cedarscript": {
      "command": "python",
      "args": ["-m", "cedarscript_mcp.server"],
      "env": {
        "CEDARSCRIPT_ROOT": "${workspaceFolder}",
        "CEDARSCRIPT_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

**File**: `examples/quickstart.md`
```markdown
# CEDARScript MCP Server - Quick Start

## Installation

```bash
pip install cedarscript-mcp-server
```

## Usage with Claude Desktop

1. Open Claude Desktop settings
2. Navigate to MCP Servers configuration
3. Add this configuration:

```json
{
  "mcpServers": {
    "cedarscript": {
      "command": "python",
      "args": ["-m", "cedarscript_mcp.server", "--root", "/path/to/your/project"]
    }
  }
}
```

4. Restart Claude Desktop
5. Ask Claude to use CEDARScript tools!

## Example Prompts

"Parse this CEDARScript command: UPDATE myfile.py SET imports.append('import os')"

"Apply this transformation (preview first): UPDATE calculator.py SET function:add REPLACE 'x + y' WITH 'x + y + 1'"

"Show me what CEDARScript capabilities you have access to"
```

---

## Phase 9: Testing

### Step 9.1: Test Fixtures
**File**: `tests/conftest.py`

```python
"""Pytest fixtures for CEDARScript MCP Server tests."""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_project_root(tmp_path):
    """Create temporary project directory with sample files."""
    project = tmp_path / "test_project"
    project.mkdir()

    # Create sample files
    (project / "myfile.py").write_text(
        "import sys\n\ndef calculate(x):\n    return x + 1\n"
    )
    (project / "README.md").write_text("# Test Project\n")

    yield project

    # Cleanup handled by tmp_path fixture


@pytest.fixture
def validator(temp_project_root):
    """Create PathValidator for tests."""
    from cedarscript_mcp.security import PathValidator
    return PathValidator(temp_project_root)
```

### Step 9.2: Security Tests
**File**: `tests/test_security.py`

```python
"""Tests for security module."""
import pytest
from pathlib import Path
from cedarscript_mcp.security import PathValidator, SecurityError


def test_path_traversal_blocked(validator):
    """Test that path traversal attacks are blocked."""
    with pytest.raises(SecurityError, match="Path escape attempt"):
        validator.validate_path("../../../etc/passwd")


def test_denylist_patterns(validator):
    """Test denylist pattern matching."""
    with pytest.raises(SecurityError, match="denylist"):
        validator.validate_path(".git/config")

    with pytest.raises(SecurityError, match="denylist"):
        validator.validate_path(".env")


def test_read_only_mode(temp_project_root):
    """Test read-only mode enforcement."""
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

    with pytest.raises(SecurityError, match="exceeds maximum size"):
        validator.validate_path("large.txt")
```

### Step 9.3: Tool Tests
**File**: `tests/test_tools.py`

```python
"""Tests for MCP tools."""
import pytest
from cedarscript_mcp.tools import parse_cedarscript_tool, list_capabilities_tool


def test_parse_valid_cedarscript():
    """Test parsing valid CEDARScript."""
    result = parse_cedarscript_tool(
        "UPDATE myfile.py SET imports.append('import os')"
    )
    assert result["success"] is True
    assert result["count"] == 1


def test_parse_invalid_cedarscript():
    """Test parsing invalid CEDARScript."""
    with pytest.raises(ValueError, match="parse error"):
        parse_cedarscript_tool("INVALID COMMAND")


def test_list_capabilities():
    """Test capabilities listing."""
    caps = list_capabilities_tool()
    assert "server" in caps
    assert "version" in caps
    assert "features" in caps
    assert "UPDATE" in caps["features"]["commands"]
```

---

## Phase 10: Makefile

See `planning/MAKEFILE_DESIGN.md` for complete Makefile implementation.

---

## Implementation Checklist

- [ ] Phase 1: Project structure
- [ ] Phase 2: Configuration files (pyproject.toml, .gitignore, LICENSE)
- [ ] Phase 3: Security module (`security.py`)
- [ ] Phase 4: Adapter layer (`adapters.py`)
- [ ] Phase 5: Tools layer (`tools.py`)
- [ ] Phase 6: MCP server core (`server.py`)
- [ ] Phase 7: Package initialization (`__init__.py`)
- [ ] Phase 8: Documentation (README, examples)
- [ ] Phase 9: Testing (fixtures, tests)
- [ ] Phase 10: Makefile
- [ ] Phase 11: CI/CD (GitHub Actions)
- [ ] Phase 12: Initial release (TestPyPI, then PyPI)

---

**Implementation Version**: 1.0.0
**Last Updated**: 2025-01-21
