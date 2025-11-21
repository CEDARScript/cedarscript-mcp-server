#!/usr/bin/env python3
"""CEDARScript MCP Server - STDIO implementation."""

import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .adapters import translate_exception
from .security import PathValidator, SecurityError
from .tools import (
    apply_cedarscript_tool,
    list_capabilities_tool,
    parse_cedarscript_tool,
)


# Configure logging
def setup_logging(level: str = "INFO", format: str = "text"):
    """Configure logging based on environment."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    if format == "json":
        # Structured JSON logging
        import json

        class JSONFormatter(logging.Formatter):
            def format(self, record):
                return json.dumps(
                    {
                        "timestamp": self.formatTime(record),
                        "level": record.levelname,
                        "message": record.getMessage(),
                        "module": record.module,
                    }
                )

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JSONFormatter())
    else:
        # Standard text logging
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))

    logger = logging.getLogger("cedarscript_mcp")
    logger.setLevel(log_level)
    logger.addHandler(handler)
    return logger


logger = setup_logging(
    level=os.getenv("CEDARSCRIPT_LOG_LEVEL", "INFO"),
    format=os.getenv("CEDARSCRIPT_LOG_FORMAT", "text"),
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
            Path(default_root), read_only=read_only, max_file_size=max_size
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
    commands: str, root: str, dry_run: bool = True
) -> dict:
    """Apply CEDARScript transformations."""
    logger.info(f"apply_cedarscript called (root={root}, dry_run={dry_run})")
    try:
        validator = get_validator(root)
        return apply_cedarscript_tool(commands, root, dry_run, validator)
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
        help="Project root directory (default: $CEDARSCRIPT_ROOT or cwd)",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        default=os.getenv("CEDARSCRIPT_READ_ONLY", "false").lower() == "true",
        help="Run in read-only mode (no file writes)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("CEDARSCRIPT_LOG_LEVEL", "INFO"),
        help="Logging level",
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=int(os.getenv("CEDARSCRIPT_MAX_FILE_SIZE", 10 * 1024 * 1024)),
        help="Maximum file size in bytes (default: 10MB)",
    )

    args = parser.parse_args()

    # Initialize global validator
    global _global_validator
    _global_validator = PathValidator(
        Path(args.root), read_only=args.read_only, max_file_size=args.max_file_size
    )

    logger.info("Starting CEDARScript MCP Server")
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
