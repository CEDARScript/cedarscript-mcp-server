# CEDARScript MCP Server - Architecture

## Overview

The CEDARScript MCP Server is a production-grade adapter that exposes the CEDARScript Editor library via the Model Context Protocol (MCP). It enables AI agents (like Claude) to perform intelligent code transformations through a secure, well-defined protocol.

## Design Philosophy

### Separation of Concerns
- **Core Library** (`cedarscript-editor`): Pure computation, no protocol awareness
- **MCP Server** (this project): Thin adapter layer, protocol handling, security

This separation ensures:
- Core library remains focused and testable
- MCP server can evolve independently
- Users can choose CLI-only or MCP integration
- Multiple MCP server variants possible (STDIO, HTTP, gRPC)

### Fail-Safe Defaults
- **Dry-run by default**: All mutations require explicit opt-in
- **Read-only mode**: Optional complete write protection
- **Path validation**: Strict root directory enforcement
- **Explicit confirmation**: Multi-step workflows for destructive operations

### Observable Systems
- **Structured logging**: JSON format for machine parsing
- **Request tracing**: Unique IDs for debugging
- **Error enrichment**: AI-friendly context and suggestions
- **Metrics hooks**: Performance and reliability monitoring

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Client (Claude)                      │
│                    Desktop / VS Code / API                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ JSON-RPC 2.0 over STDIO
                      │ (subprocess communication)
┌─────────────────────▼───────────────────────────────────────┐
│                 CEDARScript MCP Server                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │  server.py - MCP Protocol Handler                       │ │
│ │  - StdioServerTransport (stdin/stdout)                  │ │
│ │  - Request routing & validation                         │ │
│ │  - Signal handling (graceful shutdown)                  │ │
│ │  - Logging & metrics                                    │ │
│ └─────────────────┬───────────────────────────────────────┘ │
│                   │                                           │
│ ┌─────────────────▼───────────────────────────────────────┐ │
│ │  tools.py - MCP Tool Definitions                        │ │
│ │  - parse_cedarscript(content) → ParseResult             │ │
│ │  - apply_cedarscript(commands, root, dry_run=True)      │ │
│ │  - explain_error(error_msg) → Explanation               │ │
│ │  - list_capabilities() → Features                       │ │
│ └─────────────────┬───────────────────────────────────────┘ │
│                   │                                           │
│ ┌─────────────────▼───────────────────────────────────────┐ │
│ │  adapters.py - Protocol Translation                     │ │
│ │  - CEDARScript AST ↔ JSON serialization                 │ │
│ │  - Exception → Structured MCP Error                     │ │
│ │  - Diff generation (unified format)                     │ │
│ │  - Result enrichment (line ranges, context)             │ │
│ └─────────────────┬───────────────────────────────────────┘ │
│                   │                                           │
│ ┌─────────────────▼───────────────────────────────────────┐ │
│ │  security.py - Safety & Validation                      │ │
│ │  - Path traversal prevention                            │ │
│ │  - Root directory enforcement                           │ │
│ │  - File size limits                                     │ │
│ │  - Allowlist/denylist patterns                          │ │
│ └─────────────────┬───────────────────────────────────────┘ │
└───────────────────┼───────────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────────┐
│              cedarscript-editor (Core Library)                 │
│  - CEDARScriptEditor.apply_commands()                         │
│  - find_commands() - AST parsing                              │
│  - Tree-sitter integration                                    │
│  - File manipulation                                          │
└───────────────────────────────────────────────────────────────┘
```

## Protocol Mapping: MCP ↔ CEDARScript

### MCP Tool: `parse_cedarscript`
**Purpose**: Validate CEDARScript syntax without execution

**Input (JSON-RPC)**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "parse_cedarscript",
    "arguments": {
      "content": "UPDATE myfile.py SET imports.append('import os')"
    }
  }
}
```

**Mapping**:
- Calls `find_commands(content)`
- Returns AST as serialized JSON
- Catches `ValueError` for syntax errors

**Output (success)**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "commands": [
      {
        "type": "UpdateCommand",
        "target": "myfile.py",
        "action": "append",
        "segment": "imports",
        "content": ["import os"]
      }
    ],
    "count": 1
  }
}
```

**Output (error)**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid CEDARScript syntax",
    "data": {
      "type": "ParseError",
      "details": "Expected 'UPDATE' or 'CREATE', found 'UPDAET'",
      "suggestion": "Check command spelling. Valid commands: UPDATE, CREATE, DELETE, MOVE"
    }
  }
}
```

### MCP Tool: `apply_cedarscript`
**Purpose**: Apply code transformations (with preview mode)

**Input**:
```json
{
  "name": "apply_cedarscript",
  "arguments": {
    "commands": "UPDATE myfile.py SET function:calculate REPLACE 'x + 1' WITH 'x + 2'",
    "root": "/path/to/project",
    "dry_run": true
  }
}
```

**Mapping**:
- Parse via `find_commands(commands)`
- Validate `root` path via `security.validate_root()`
- If `dry_run=False`: Call `CEDARScriptEditor(root).apply_commands()`
- If `dry_run=True`: Mock file writes, generate diffs

**Output (dry_run=true)**:
```json
{
  "success": true,
  "dry_run": true,
  "preview": {
    "affected_files": ["myfile.py"],
    "diffs": [
      {
        "file": "myfile.py",
        "diff": "--- myfile.py\n+++ myfile.py\n@@ -10,1 +10,1 @@\n-    return x + 1\n+    return x + 2"
      }
    ]
  }
}
```

**Output (dry_run=false)**:
```json
{
  "success": true,
  "dry_run": false,
  "results": [
    "Updated myfile.py\n  -> REPLACE in function calculate: 1 occurrence"
  ],
  "affected_files": ["myfile.py"]
}
```

### MCP Tool: `explain_error`
**Purpose**: Provide AI-friendly error explanations

**Input**:
```json
{
  "name": "explain_error",
  "arguments": {
    "error_message": "CEDARScriptEditorException: Command #2 failed: File not found: utils.py"
  }
}
```

**Output**:
```json
{
  "explanation": "The second CEDARScript command tried to modify 'utils.py', but the file doesn't exist in the project root.",
  "suggestions": [
    "Verify the file path is correct",
    "Check if the file was created in command #1",
    "Use CREATE command if the file should be created first"
  ],
  "recovery_steps": [
    "Run parse_cedarscript to validate syntax",
    "List project files to verify paths",
    "Consider CREATE FILE utils.py before UPDATE"
  ]
}
```

## Security Model

### Path Validation (security.py)
```python
class PathValidator:
    def __init__(self, root: Path, read_only: bool = False):
        self.root = root.resolve()  # Absolute path
        self.read_only = read_only

    def validate(self, file_path: str) -> Path:
        """Ensure path is within root, no traversal attacks."""
        resolved = (self.root / file_path).resolve()
        if not resolved.is_relative_to(self.root):
            raise SecurityError(f"Path escape attempt: {file_path}")
        return resolved
```

### Sandboxing Strategy
1. **Root Enforcement**: All file operations confined to specified directory
2. **Read-Only Mode**: Optional complete write protection (parsing only)
3. **File Size Limits**: Configurable max file size (default: 10MB)
4. **Pattern Filtering**: Allowlist/denylist for file operations
   - Default denylist: `.git/`, `node_modules/`, `__pycache__/`, `.env`

### Privilege Model
- **No elevation**: Server runs with user's permissions
- **Explicit mutations**: Dry-run by default, require confirmation
- **Audit logging**: All write operations logged with timestamps

## Error Handling Strategy

### Error Categories
1. **Protocol Errors** (JSON-RPC): Malformed requests, invalid methods
2. **Validation Errors**: Invalid arguments, path violations
3. **Parse Errors**: CEDARScript syntax issues
4. **Execution Errors**: File not found, permission denied, CEDARScript failures
5. **System Errors**: Out of memory, disk full, unexpected exceptions

### Error Response Format
All errors follow JSON-RPC 2.0 spec with enriched `data`:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,  // Application error codes
    "message": "Human-readable summary",
    "data": {
      "type": "ErrorType",
      "details": "Specific diagnostic info",
      "context": {
        "file": "myfile.py",
        "line": 42,
        "command_index": 2
      },
      "suggestions": ["Fix suggestion 1", "Fix suggestion 2"],
      "recovery_steps": ["Step 1", "Step 2"]
    }
  }
}
```

### Exception Translation (adapters.py)
```python
def translate_exception(exc: Exception) -> dict:
    """Convert Python exceptions to MCP error responses."""
    if isinstance(exc, CEDARScriptEditorException):
        return {
            "code": -32000,
            "message": "CEDARScript execution failed",
            "data": {
                "type": "ExecutionError",
                "command_index": exc.ordinal,
                "details": exc.description,
                "suggestions": parse_suggestions(exc)
            }
        }
    elif isinstance(exc, SecurityError):
        return {"code": -32001, "message": "Security violation", ...}
    # ... more mappings
```

## Configuration Management

### Environment Variables
- `CEDARSCRIPT_ROOT`: Default project root path
- `CEDARSCRIPT_LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR
- `CEDARSCRIPT_LOG_FORMAT`: text, json
- `CEDARSCRIPT_READ_ONLY`: true/false (force read-only mode)
- `CEDARSCRIPT_MAX_FILE_SIZE`: Max file size in bytes

### CLI Arguments
```bash
python -m cedarscript_mcp.server \
  --root /path/to/project \
  --log-level DEBUG \
  --read-only \
  --max-file-size 10485760
```

### Priority Order
1. CLI arguments (highest priority)
2. Environment variables
3. Default values (lowest priority)

## Logging Strategy

### Structured Logging (JSON Format)
```json
{
  "timestamp": "2025-01-21T10:30:45.123Z",
  "level": "INFO",
  "request_id": "req_abc123",
  "event": "tool_called",
  "tool": "apply_cedarscript",
  "args": {"root": "/project", "dry_run": true},
  "duration_ms": 234,
  "status": "success"
}
```

### Log Levels
- **DEBUG**: Request/response payloads, internal state
- **INFO**: Tool calls, file operations, high-level events
- **WARNING**: Validation failures, retryable errors
- **ERROR**: Execution failures, system errors

### Privacy Considerations
- Sensitive data (file contents, API keys) redacted by default
- Opt-in verbose mode for debugging (logged to separate file)

## Performance Characteristics

### Expected Latency
- **parse_cedarscript**: 10-100ms (depends on command complexity)
- **apply_cedarscript (dry_run)**: 50-500ms (file reading, diff generation)
- **apply_cedarscript (execute)**: 100ms-5s (includes tree-sitter parsing, file writes)

### Resource Limits
- **Memory**: Proportional to file sizes (tree-sitter AST parsing)
- **CPU**: Burst during parsing, minimal during idle
- **Disk I/O**: Read-heavy (parsing), write-heavy (execution)

### Scalability Notes
- STDIO transport: Single client, single process (by design)
- Stateless: Each request independent (no session state)
- Concurrency: Not applicable (STDIO is sequential)

## Testing Strategy

### Unit Tests
- Tool function behavior (mocked CEDARScript editor)
- Adapter serialization/deserialization
- Security validation (path traversal attempts)
- Error translation

### Integration Tests
- Full request/response cycle via STDIO
- Real CEDARScript Editor integration
- File system mutations (in temp directories)

### Protocol Compliance Tests
- JSON-RPC 2.0 spec validation
- Error code correctness
- Message format validation

### Security Tests
- Path traversal attempts
- File size limit enforcement
- Read-only mode verification
- Denylist pattern matching

## Deployment Patterns

### Claude Desktop Integration
```json
{
  "mcpServers": {
    "cedarscript": {
      "command": "python",
      "args": ["-m", "cedarscript_mcp.server", "--root", "${workspaceFolder}"]
    }
  }
}
```

### VS Code MCP Client
```json
{
  "servers": {
    "cedarscript": {
      "command": "python",
      "args": ["-m", "cedarscript_mcp.server"],
      "env": {
        "CEDARSCRIPT_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

### Docker Containerization
```dockerfile
FROM python:3.12-slim
RUN pip install cedarscript-mcp-server
ENTRYPOINT ["python", "-m", "cedarscript_mcp.server"]
CMD ["--root", "/workspace"]
```

## Future Extensions

### Potential Enhancements
- **HTTP Transport**: Alternative to STDIO for web-based clients
- **Multi-root Support**: Work with multiple project directories
- **Incremental Parsing**: Cache ASTs for performance
- **Transaction Support**: Rollback on error
- **Collaboration Features**: Multi-user locking, conflict resolution
- **Plugin System**: Custom tools via entry points

### Backward Compatibility Commitment
- Semantic versioning (MAJOR.MINOR.PATCH)
- 6-month deprecation notice for breaking changes
- Compatibility matrix with cedarscript-editor versions
- Migration guides for major version upgrades

---

**Architecture Version**: 1.0.0
**Last Updated**: 2025-01-21
**Author**: Google Principal Engineer Design Pattern
