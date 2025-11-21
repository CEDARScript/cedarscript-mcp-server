# CEDARScript MCP Server

**AI-Assisted Code Transformations via Model Context Protocol**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Overview

CEDARScript MCP Server exposes the powerful [CEDARScript Editor](https://github.com/CEDARScript/cedarscript-editor-python) through the Model Context Protocol (MCP), enabling AI agents like Claude to perform intelligent, semantic-aware code transformations.

### Key Features

- **🔒 Secure by Default**: Path validation, sandboxing, read-only mode
- **🎯 Dry-Run Mode**: Preview changes before applying
- **🌲 Tree-Sitter Powered**: Language-aware code analysis
- **📡 STDIO Transport**: Simple subprocess integration (no HTTP overhead)
- **🛠️ Production-Ready**: Comprehensive logging, error handling, testing

## Quick Start

### Installation

```bash
pip install cedarscript-mcp-server
```

### Usage with Claude Desktop

1. Open Claude Desktop configuration (usually `~/.config/Claude/claude_desktop_config.json`)

2. Add CEDARScript MCP server:

```json
{
  "mcpServers": {
    "cedarscript": {
      "command": "python",
      "args": [
        "-m",
        "cedarscript_mcp.server",
        "--root",
        "/path/to/your/project"
      ]
    }
  }
}
```

3. Restart Claude Desktop

4. Ask Claude to use CEDARScript:
   - "Parse this CEDARScript command: `UPDATE myfile.py SET imports.append('import os')`"
   - "Apply this transformation (preview first): `UPDATE calculator.py SET function:calculate REPLACE 'x + 1' WITH 'x + 2'`"

### Command-Line Usage

```bash
# Start server (STDIO mode)
python -m cedarscript_mcp.server --root /path/to/project

# With custom options
python -m cedarscript_mcp.server \
  --root /path/to/project \
  --read-only \
  --log-level DEBUG \
  --max-file-size 10485760
```

## Architecture

CEDARScript MCP Server is a thin adapter layer that:
1. Accepts JSON-RPC requests over STDIO
2. Validates paths and security constraints
3. Delegates to [CEDARScript Editor](https://github.com/CEDARScript/cedarscript-editor-python) for execution
4. Returns structured results or error messages

```
┌─────────────────────────────────┐
│   Claude Desktop / VS Code      │
│        (MCP Client)             │
└────────────┬────────────────────┘
             │ JSON-RPC over STDIO
┌────────────▼────────────────────┐
│  CEDARScript MCP Server         │
│  • Security (path validation)   │
│  • Tools (parse, apply, list)   │
│  • Adapters (protocol mapping)  │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   CEDARScript Editor (core)     │
│  • AST parsing                  │
│  • Tree-sitter analysis         │
│  • File transformations         │
└─────────────────────────────────┘
```

## Available Tools

### `parse_cedarscript`
Parse and validate CEDARScript commands without execution.

**Parameters:**
- `content` (string): CEDARScript commands

**Returns:** Parsed AST commands

**Example:**
```python
{
  "content": "UPDATE myfile.py SET imports.append('import os')"
}
```

### `apply_cedarscript`
Apply CEDARScript transformations to code files.

**Parameters:**
- `commands` (string): CEDARScript commands
- `root` (string): Project root directory path
- `dry_run` (boolean, default: true): Preview changes without writing

**Returns:** Results, diffs (if dry_run), affected files

**Example:**
```python
{
  "commands": "UPDATE calculator.py SET function:add REPLACE 'x + y' WITH 'x + y + 1'",
  "root": "/path/to/project",
  "dry_run": true
}
```

### `list_capabilities`
List server capabilities and supported features.

**Returns:** Server version, features, security settings

## Configuration

### Environment Variables

- `CEDARSCRIPT_ROOT`: Default project root (default: current directory)
- `CEDARSCRIPT_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `CEDARSCRIPT_LOG_FORMAT`: Log format (text, json)
- `CEDARSCRIPT_READ_ONLY`: Force read-only mode (true/false)
- `CEDARSCRIPT_MAX_FILE_SIZE`: Max file size in bytes (default: 10485760)

### CLI Arguments

```bash
python -m cedarscript_mcp.server \
  --root /path/to/project \         # Project root directory
  --read-only \                     # Enable read-only mode
  --log-level DEBUG \               # Logging level
  --max-file-size 10485760          # Max file size (bytes)
```

## Security

### Path Validation
- All file paths are validated against the specified root directory
- Path traversal attacks (`../../../etc/passwd`) are blocked
- Symlinks are resolved and validated

### Denylist Patterns
Files matching these patterns are automatically rejected:
- `.git/**`, `node_modules/**`, `__pycache__/**`
- `.env`, `*.env`, `.env.*`
- `credentials.json`, `*.key`, `*.pem`

### Read-Only Mode
When enabled, all write operations are rejected (parsing/analysis only).

### File Size Limits
Configurable maximum file size (default: 10MB) to prevent resource exhaustion.

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/CEDARScript/cedarscript-mcp-server.git
cd cedarscript-mcp-server

# Install development dependencies
make install

# Run tests
make test

# Run with coverage
make test-cov

# Format and lint
make check
```

### Makefile Targets

```bash
make help              # Show all available targets
make install           # Install with dev dependencies
make test              # Run full test suite
make test-fast         # Run tests (skip integration)
make check             # Format, lint, security checks
make run               # Launch server (demo mode)
make build             # Build distribution packages
```

See `planning/MAKEFILE_DESIGN.md` for complete target documentation.

## Testing

```bash
# Run all tests
make test

# With coverage report
make test-cov

# Watch mode (auto-rerun on changes)
make test-watch

# Test against multiple cedarscript-editor versions
make test-matrix
```

## Documentation

- **[ARCHITECTURE.md](planning/ARCHITECTURE.md)**: System design, protocol mapping, security model
- **[IMPLEMENTATION.md](planning/IMPLEMENTATION.md)**: Step-by-step implementation guide
- **[MAKEFILE_DESIGN.md](planning/MAKEFILE_DESIGN.md)**: Makefile targets and automation
- **[Examples](examples/)**: Claude Desktop, VS Code, quickstart guides

## Examples

### Claude Desktop Configuration

See `examples/claude_desktop.json` for drop-in configuration.

### VS Code MCP Client

See `examples/vscode_mcp.json` for VS Code setup.

### Programmatic Usage

```python
from cedarscript_mcp import PathValidator, apply_cedarscript_tool

# Create validator
validator = PathValidator(Path("/path/to/project"))

# Apply transformation (dry-run)
result = apply_cedarscript_tool(
    commands="UPDATE myfile.py SET imports.append('import os')",
    root="/path/to/project",
    dry_run=True,
    validator=validator
)

print(result)
```

## Troubleshooting

### Server Not Starting

**Issue**: `ModuleNotFoundError: No module named 'mcp'`

**Solution**: Install MCP SDK: `pip install mcp>=1.0.0`

### Path Validation Errors

**Issue**: `SecurityError: Path escape attempt`

**Solution**: Ensure file paths are within the specified root directory.

### Read-Only Mode Blocking Writes

**Issue**: `SecurityError: Write operation rejected`

**Solution**: Remove `--read-only` flag or set `CEDARSCRIPT_READ_ONLY=false`.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Run `make check test` before committing
4. Submit a pull request

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Related Projects

- [CEDARScript Editor](https://github.com/CEDARScript/cedarscript-editor-python) - Core transformation library
- [CEDARScript AST Parser](https://github.com/CEDARScript/cedarscript-ast-parser) - Language parser
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification

## Support

- **Issues**: [GitHub Issues](https://github.com/CEDARScript/cedarscript-mcp-server/issues)
- **Documentation**: [GitHub README](https://github.com/CEDARScript/cedarscript-mcp-server#readme)
- **Email**: cedarscript@orgecc.com

---

**Made with ❤️ by the CEDARScript Team**
