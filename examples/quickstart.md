# CEDARScript MCP Server - Quick Start Guide

## Installation

```bash
pip install cedarscript-mcp-server
```

## Setup with Claude Desktop

### Step 1: Locate Configuration File

The Claude Desktop configuration file is typically located at:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Step 2: Add CEDARScript Server

Open the configuration file and add the CEDARScript MCP server:

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
      ],
      "env": {
        "CEDARSCRIPT_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Replace** `/path/to/your/project` with the actual path to your project directory.

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop to load the new MCP server configuration.

### Step 4: Verify Installation

Ask Claude:
> "What CEDARScript capabilities do you have access to?"

Claude should respond with information about the available tools (parse_cedarscript, apply_cedarscript, list_capabilities).

## Example Prompts

### 1. Parse CEDARScript Commands

> "Parse this CEDARScript command: `UPDATE myfile.py SET imports.append('import os')`"

Claude will validate the syntax and show you the parsed AST.

### 2. Preview Code Transformations

> "Apply this transformation in dry-run mode:
> ```
> UPDATE calculator.py
> SET function:calculate
> REPLACE 'x + 1' WITH 'x + 2'
> ```"

Claude will show you a preview of the changes without modifying any files.

### 3. Apply Code Transformations

> "Apply this transformation to my code:
> ```cedarscript
> UPDATE myfile.py
> SET imports.append('from typing import List, Dict')
> ```
> Run it in dry-run mode first to preview."

Claude will:
1. First run in dry-run mode to show you the preview
2. Ask for confirmation
3. Apply the changes if you approve

### 4. Check Server Status

> "Show me what CEDARScript features are available"

Claude will display server version, supported commands, and security settings.

## Configuration Options

### Environment Variables

You can customize the server behavior using environment variables in the configuration:

```json
{
  "mcpServers": {
    "cedarscript": {
      "command": "python",
      "args": ["-m", "cedarscript_mcp.server", "--root", "/path/to/project"],
      "env": {
        "CEDARSCRIPT_LOG_LEVEL": "DEBUG",
        "CEDARSCRIPT_READ_ONLY": "false",
        "CEDARSCRIPT_MAX_FILE_SIZE": "10485760"
      }
    }
  }
}
```

**Available options:**
- `CEDARSCRIPT_LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR
- `CEDARSCRIPT_READ_ONLY`: true/false (prevents all file writes)
- `CEDARSCRIPT_MAX_FILE_SIZE`: Maximum file size in bytes (default: 10MB)

### Command-Line Arguments

Alternatively, use CLI arguments:

```json
{
  "mcpServers": {
    "cedarscript": {
      "command": "python",
      "args": [
        "-m",
        "cedarscript_mcp.server",
        "--root", "/path/to/project",
        "--log-level", "DEBUG",
        "--max-file-size", "10485760"
      ]
    }
  }
}
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'mcp'"

**Solution**: Install the MCP SDK:
```bash
pip install mcp>=1.0.0
```

### Issue: "SecurityError: Path escape attempt"

**Solution**: Ensure the file paths in your CEDARScript commands are within the project root directory specified in `--root`.

### Issue: "SecurityError: Write operation rejected: server in read-only mode"

**Solution**: Remove read-only mode by:
- Removing `--read-only` from CLI args, or
- Setting `"CEDARSCRIPT_READ_ONLY": "false"` in env

### Issue: Server not appearing in Claude

**Solution**:
1. Check that the configuration file path is correct
2. Verify JSON syntax (use a JSON validator)
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for error messages

## Advanced Usage

### Multiple Project Roots

You can configure multiple CEDARScript servers for different projects:

```json
{
  "mcpServers": {
    "cedarscript-project-a": {
      "command": "python",
      "args": ["-m", "cedarscript_mcp.server", "--root", "/path/to/project-a"]
    },
    "cedarscript-project-b": {
      "command": "python",
      "args": ["-m", "cedarscript_mcp.server", "--root", "/path/to/project-b"]
    }
  }
}
```

### Read-Only Mode (Safe Exploration)

For exploring code without risk of modification:

```json
{
  "mcpServers": {
    "cedarscript-readonly": {
      "command": "python",
      "args": [
        "-m",
        "cedarscript_mcp.server",
        "--root", "/path/to/project",
        "--read-only"
      ]
    }
  }
}
```

### Debug Mode

For troubleshooting:

```json
{
  "mcpServers": {
    "cedarscript-debug": {
      "command": "python",
      "args": [
        "-m",
        "cedarscript_mcp.server",
        "--root", "/path/to/project",
        "--log-level", "DEBUG"
      ],
      "env": {
        "CEDARSCRIPT_LOG_FORMAT": "json"
      }
    }
  }
}
```

Logs will appear in Claude Desktop's console (View → Developer → Developer Tools).

## Next Steps

- Read [ARCHITECTURE.md](../planning/ARCHITECTURE.md) for system design
- Check [README.md](../README.md) for full documentation
- Explore [CEDARScript syntax](https://github.com/CEDARScript/cedarscript-editor-python) for advanced transformations

## Support

- **Issues**: [GitHub Issues](https://github.com/CEDARScript/cedarscript-mcp-server/issues)
- **Email**: cedarscript@orgecc.com
