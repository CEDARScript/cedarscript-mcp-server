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
        denylist: Optional[list[str]] = None,
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
            ".git/**",
            "node_modules/**",
            "__pycache__/**",
            ".env",
            "*.env",
            ".env.*",
            "credentials.json",
            "*.key",
            "*.pem",
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
                raise SecurityError(
                    f"Path matches denylist pattern '{pattern}': {file_path}"
                )

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
