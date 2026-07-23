# stream-spy

Intercept and monitor subprocess streams with JSON parsing and syntax highlighting.

Think of it as **tee** for your subprocess I/O, but with beautiful formatting and JSON awareness.

## Use Case

Primarily designed for wrapping [MCP](https://modelcontextprotocol.io/) STDIO servers to intercept and monitor communication between clients and servers:

```bash
stream-spy --stdin-json --stdout-json uvx mcp-server-foo
```

This will:
1. Start the MCP server as a subprocess
2. Intercept all JSON-RPC messages flowing through stdin/stdout
3. Display them with beautiful syntax highlighting
4. Log everything to a file for later inspection

## Installation

```bash
pip install stream-spy
```

## Usage

```bash
# Basic usage - just wrap any command
stream-spy python my_script.py

# MCP server monitoring (stdin/stdout are JSON-RPC)
stream-spy --stdin-json --stdout-json uvx mcp-server-foo

# With expanded JSON formatting (multi-line pretty print)
stream-spy --stdin-json --stdout-json --expand uvx mcp-server-foo

# Log everything to a file for tailing
stream-spy --stdin-json --stdout-json --log-file /tmp/mcp.log uvx mcp-server-foo
```

Then in another terminal:
```bash
tail -f /tmp/mcp.log
```

## Flags

| Flag | Description |
|------|-------------|
| `command` | Command and arguments to run as a subprocess (required) |
| `--stdin-json` | Treat stdin input as JSON lines with syntax highlighting |
| `--stdout-json` | Treat stdout output as JSON lines with syntax highlighting |
| `--stderr-json` | Treat stderr output as JSON lines with syntax highlighting |
| `--expand` | Expand JSON objects to multi-line pretty print (default: compact single-line) |
| `--log-file` | Write all intercepted streams to a log file |

## Output Format

Each line is prefixed with its source:

```
>>> IN:   {"jsonrpc":"2.0","method":"initialize","params":{...}}
<<< OUT:  {"jsonrpc":"2.0","result":{"protocolVersion":"2024-11-05",...}}
<<< ERR:  [2024-01-15 10:30:00] Server starting...
```

When JSON mode is enabled, valid JSON gets syntax highlighting via **rich**. Invalid JSON lines show a warning icon:

```
⚠️  JSON parse error: This is just a regular log line
```

## Design

- **Async I/O**: Uses asyncio for concurrent stream handling
- **Rich formatting**: Beautiful console output with syntax highlighting
- **JSON-aware**: Parses and validates JSON lines independently
- **File logging**: Optional file output for later inspection with `tail -f`
- **Graceful shutdown**: Handles SIGINT/SIGTERM to cleanly terminate subprocesses

## Example: MCP Server Monitoring

```bash
# Terminal 1 - Start the stream spy wrapper
stream-spy --stdin-json --stdout-json --expand uvx mcp-server-filesystem --root /tmp

# Terminal 2 - Monitor the log
tail -f /tmp/stream-spy.log
```
